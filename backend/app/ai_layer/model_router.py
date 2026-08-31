import enum
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from app.config import settings


class AiTask(str, enum.Enum):
    SIGNAL_PARSING = "signal_parsing"
    REPLY_CLASSIFICATION = "reply_classification"
    MESSAGE_DRAFTING = "message_drafting"
    CONFLICTING_SIGNAL_REASONING = "conflicting_signal_reasoning"
    BATCH_PATTERN_DETECTION = "batch_pattern_detection"


def get_model_for_task(task: AiTask) -> BaseChatModel:
    if task in (AiTask.SIGNAL_PARSING, AiTask.REPLY_CLASSIFICATION):
        return ChatGroq(
            model_name="openai/gpt-oss-120b",
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.0,
        )

    if task == AiTask.MESSAGE_DRAFTING:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2,
        )

    if task in (AiTask.CONFLICTING_SIGNAL_REASONING, AiTask.BATCH_PATTERN_DETECTION):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0,
        )

    raise ValueError(f"Unknown AiTask: {task}")
