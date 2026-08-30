from langchain_core.messages import SystemMessage, HumanMessage
from app.ai_layer.model_router import AiTask, get_model_for_task
from app.ai_layer.output_schemas import SignalParsingOutput

METHOD_ROOT_CAUSES = {
    "card": [
        "CARD_INSUFFICIENT_FUNDS",
        "CARD_INVALID_NUMBER",
        "CARD_EXPIRED",
        "CARD_INVALID_CVV",
        "CARD_DO_NOT_HONOR",
        "CARD_SUSPECTED_FRAUD",
        "CARD_3DS_TIMEOUT",
        "CARD_GATEWAY_TIMEOUT",
        "CARD_NETWORK_ERROR",
        "CARD_SYSTEM_ERROR",
    ],
    "upi": [
        "UPI_INSUFFICIENT_FUNDS",
        "UPI_INVALID_MPIN",
        "UPI_MPIN_EXCEEDED",
        "UPI_APP_TIMEOUT",
        "UPI_VPA_DEACTIVATED",
        "UPI_USER_DROPPED",
        "UPI_PSP_UNAVAILABLE",
        "UPI_NPCI_DEGRADED",
        "UPI_BANK_UNAVAILABLE",
        "UPI_BENEFICIARY_TIMEOUT",
    ],
    "netbanking": [
        "NETBANKING_AUTH_FAILED",
        "NETBANKING_USER_CANCELLED",
        "NETBANKING_SESSION_EXPIRED",
        "NETBANKING_GATEWAY_TIMEOUT",
        "NETBANKING_BANK_DEGRADED",
        "NETBANKING_SYNC_GAP",
    ],
    "wallet": [
        "WALLET_INSUFFICIENT_BALANCE",
        "WALLET_CONSENT_EXPIRED",
        "WALLET_UNAVAILABLE",
    ],
    "emi": [
        "EMI_ISSUER_REJECTED",
        "EMI_CARDLESS_UNAVAILABLE",
    ],
}


async def parse_failure_signal(
    method: str,
    raw_reason: str,
    failure_code: str | None = None,
) -> SignalParsingOutput:
    model = get_model_for_task(AiTask.SIGNAL_PARSING)
    structured_llm = model.with_structured_output(SignalParsingOutput)

    method_key = method.lower()
    valid_causes = METHOD_ROOT_CAUSES.get(method_key, [c for sub in METHOD_ROOT_CAUSES.values() for c in sub])

    system_prompt = (
        "You are classifying a failed payment's raw failure reason into a single, exact root cause from a fixed list. "
        "You must choose one value from the list provided — never invent a new category. "
        "If none seem to fit perfectly, choose the closest match and set confidence low."
    )

    user_content = (
        f"Payment method: {method}\n"
        f"Raw failure reason (from gateway): {raw_reason}\n"
        f"Failure code (may be absent): {failure_code or 'None'}\n\n"
        f"Valid root causes for this method: {', '.join(valid_causes)}\n"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    result: SignalParsingOutput = await structured_llm.ainvoke(messages)
    return result
