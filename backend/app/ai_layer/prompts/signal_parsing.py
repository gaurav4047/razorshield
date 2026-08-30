from langchain_core.messages import HumanMessage, SystemMessage
from app.ai_layer.model_router import AiTask, get_model_for_task
from app.ai_layer.output_schemas import SignalParsingOutput
from app.domain_logic.payment_taxonomy import get_valid_root_causes_for_method


async def parse_failure_signal(
    method: str,
    raw_reason: str,
    failure_code: str | None = None,
) -> SignalParsingOutput:
    model = get_model_for_task(AiTask.SIGNAL_PARSING)
    structured_llm = model.with_structured_output(SignalParsingOutput)

    valid_causes = sorted(list(get_valid_root_causes_for_method(method)))

    system_prompt = (
        "You are classifying a failed payment's raw failure reason into a single, exact root cause from a fixed list. "
        "You must return the EXACT lowercase string identifier from the provided list — never invent a new category or use uppercase names. "
        "If none seem to fit perfectly, choose the closest match and set confidence low."
    )

    user_content = (
        f"Payment method: {method}\n"
        f"Raw failure reason (from gateway): {raw_reason}\n"
        f"Failure code (may be absent): {failure_code or 'None'}\n\n"
        f"Valid exact root cause strings for this method:\n"
        + "\n".join(f"- {c}" for c in valid_causes)
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    result: SignalParsingOutput = await structured_llm.ainvoke(messages)
    return result
