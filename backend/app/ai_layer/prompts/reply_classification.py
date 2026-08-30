from langchain_core.messages import HumanMessage, SystemMessage
from app.ai_layer.model_router import AiTask, get_model_for_task
from app.ai_layer.output_schemas import ReplyClassificationOutput


async def classify_buyer_reply(
    raw_message: str,
    invoice_number: str = "",
    amount_paise: int = 0,
    days_overdue: int = 0,
    reminder_count: int = 0,
) -> ReplyClassificationOutput:
    model = get_model_for_task(AiTask.REPLY_CLASSIFICATION)
    structured_llm = model.with_structured_output(ReplyClassificationOutput)

    system_prompt = (
        "You are classifying a buyer's reply to a payment reminder for an overdue B2B invoice. "
        "Classify it into exactly one of: promise_to_pay, claims_already_paid, dispute, stall, unclear.\n\n"
        "Guidance:\n"
        "- promise_to_pay: buyer commits to a specific or implied future payment date/amount\n"
        "- claims_already_paid: buyer asserts payment was already made\n"
        "- dispute: buyer contests the invoice amount, goods/services received, defects, or validity of debt\n"
        "- stall: vague deflection with no commitment ('will look into it', 'checking with accounts') and no dispute\n"
        "- unclear: ambiguous, doesn't fit the above\n\n"
        "If classified as promise_to_pay and a date is mentioned or inferable, extract promised_date (YYYY-MM-DD). "
        "If an amount is mentioned, extract promised_amount_paise."
    )

    user_content = (
        f"Buyer's message: {raw_message}\n"
        f"Invoice: {invoice_number}\n"
        f"Amount: Rs {amount_paise / 100:.2f}\n"
        f"Days overdue: {days_overdue}\n"
        f"Prior reminders sent: {reminder_count}\n"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    result: ReplyClassificationOutput = await structured_llm.ainvoke(messages)
    return result
