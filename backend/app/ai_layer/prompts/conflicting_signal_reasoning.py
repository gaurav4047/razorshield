from langchain_core.messages import HumanMessage, SystemMessage

from app.ai_layer.model_router import AiTask, get_model_for_task
from app.ai_layer.output_schemas import ConflictingSignalOutput


async def evaluate_conflicting_signals(
    classified_root_cause: str,
    naive_rule_suggestion: str,
    relevant_case_history: str,
) -> ConflictingSignalOutput:
    # Gemini prompt per 05_ai_layer.md §4d
    model = get_model_for_task(AiTask.CONFLICTING_SIGNAL_REASONING)
    structured_llm = model.with_structured_output(ConflictingSignalOutput)

    system_prompt = (
        "A deterministic rule suggests a default action for this payment failure. You "
        "have additional context that may or may not support that default. Decide "
        "whether the default is still the right call, and explain your reasoning "
        "plainly — this reasoning will be shown directly to a human, and should be "
        "understandable without technical jargon.\n\n"
        "You may agree with the default, or recommend a different one of the four "
        "valid intervention types: silent_retry, delayed_retry_notify, escalate_human, "
        "alternate_method. If you disagree with the default, you must clearly explain "
        "why the additional context changes the picture."
    )

    user_content = (
        f"Root cause classified: {classified_root_cause}\n"
        f"Default rule suggests: {naive_rule_suggestion}\n"
        f"Additional context: {relevant_case_history}\n\n"
        "Respond with structured output."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    result: ConflictingSignalOutput = await structured_llm.ainvoke(messages)
    return result
