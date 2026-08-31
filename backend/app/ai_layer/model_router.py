import asyncio
import enum
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from pydantic import PrivateAttr
from app.config import settings

# Global concurrency semaphore to prevent burst rate limits on Gemini API
_gemini_semaphore = asyncio.Semaphore(1)


class AiTask(str, enum.Enum):
    SIGNAL_PARSING = "signal_parsing"
    REPLY_CLASSIFICATION = "reply_classification"
    MESSAGE_DRAFTING = "message_drafting"
    CONFLICTING_SIGNAL_REASONING = "conflicting_signal_reasoning"
    BATCH_PATTERN_DETECTION = "batch_pattern_detection"


class ResilientGeminiChatModel(BaseChatModel):
    """
    Wrapper around ChatGoogleGenerativeAI that enforces:
    1. Single-concurrency rate pacing via Semaphore
    2. Automatic fallback to Groq if Google AI returns 429/503/timeout
    """
    _gemini_model: ChatGoogleGenerativeAI = PrivateAttr()
    _groq_fallback: ChatGroq = PrivateAttr()

    def __init__(self, model_name: str = "gemini-3.6-flash", temperature: float = 0.0, **kwargs: Any):
        super().__init__(**kwargs)
        self._gemini_model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature,
            timeout=12.0,
        )
        self._groq_fallback = ChatGroq(
            model_name="openai/gpt-oss-120b",
            groq_api_key=settings.GROQ_API_KEY,
            temperature=temperature,
        )

    @property
    def _llm_type(self) -> str:
        return "resilient_gemini"

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None, **kwargs: Any) -> ChatResult:
        return self._gemini_model._generate(messages, stop=stop, **kwargs)

    async def _agenerate(self, messages: list[BaseMessage], stop: list[str] | None = None, **kwargs: Any) -> ChatResult:
        async with _gemini_semaphore:
            try:
                await asyncio.sleep(0.3)
                return await self._gemini_model._agenerate(messages, stop=stop, **kwargs)
            except Exception as exc:
                err_str = str(exc).lower()
                if "429" in err_str or "resource_exhausted" in err_str or "503" in err_str or "timeout" in err_str or "high demand" in err_str:
                    return await self._groq_fallback._agenerate(messages, stop=stop, **kwargs)
                raise exc

    def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:
        gemini_structured = self._gemini_model.with_structured_output(schema, **kwargs)
        groq_structured = self._groq_fallback.with_structured_output(schema, **kwargs)

        class StructuredRunner:
            async def ainvoke(inner_self, input_msgs: Any) -> Any:
                async with _gemini_semaphore:
                    try:
                        await asyncio.sleep(0.3)
                        return await gemini_structured.ainvoke(input_msgs)
                    except Exception as exc:
                        err_str = str(exc).lower()
                        if "429" in err_str or "resource_exhausted" in err_str or "503" in err_str or "timeout" in err_str or "high demand" in err_str:
                            return await groq_structured.ainvoke(input_msgs)
                        raise exc

        return StructuredRunner()


def get_model_for_task(task: AiTask) -> BaseChatModel:
    if task in (AiTask.SIGNAL_PARSING, AiTask.REPLY_CLASSIFICATION):
        return ChatGroq(
            model_name="openai/gpt-oss-120b",
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.0,
        )

    if task == AiTask.MESSAGE_DRAFTING:
        return ResilientGeminiChatModel(
            model_name="gemini-3.6-flash",
            temperature=0.2,
        )

    if task in (AiTask.CONFLICTING_SIGNAL_REASONING, AiTask.BATCH_PATTERN_DETECTION):
        return ResilientGeminiChatModel(
            model_name="gemini-3.6-flash",
            temperature=0.0,
        )

    raise ValueError(f"Unknown AiTask: {task}")
