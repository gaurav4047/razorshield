from app.db.models.payment_case import FaultAttribution, InterventionType

HARD_DECLINE_ROOT_CAUSES = {
    "card_lost_or_stolen",
    "card_expired",
    "mandate_expired",
}

PLAUSIBLE_RETRY_CUSTOMER_CAUSES = {
    "insufficient_balance",
    "insufficient_credit_limit",
    "insufficient_wallet_balance",
    "daily_upi_limit_exceeded",
    "daily_transfer_limit_exceeded",
}


def select_intervention(
    fault_attribution: FaultAttribution,
    classified_root_cause: str | None,
    attempt_number: int = 1,
) -> InterventionType:
    # Rule 1 enforcement: Hard decline causes NEVER retry
    if classified_root_cause in HARD_DECLINE_ROOT_CAUSES:
        return InterventionType.ALTERNATE_METHOD

    # Special case: gateway data sync gap must always escalate to prevent double-charge
    if classified_root_cause == "gateway_data_sync_gap":
        return InterventionType.ESCALATE_HUMAN

    if fault_attribution == FaultAttribution.INFRASTRUCTURE_FAULT:
        if attempt_number <= 1:
            return InterventionType.SILENT_RETRY
        return InterventionType.ESCALATE_HUMAN

    if fault_attribution == FaultAttribution.CUSTOMER_FAULT:
        if classified_root_cause in PLAUSIBLE_RETRY_CUSTOMER_CAUSES:
            return InterventionType.DELAYED_RETRY_NOTIFY
        return InterventionType.ALTERNATE_METHOD

    # Unknown or low confidence
    return InterventionType.ESCALATE_HUMAN
