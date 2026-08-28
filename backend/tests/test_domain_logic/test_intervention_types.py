from app.db.models.payment_case import FaultAttribution, InterventionType
from app.domain_logic.intervention_types import select_intervention


def test_hard_decline_never_retry_rule():
    # Rule 1: card_lost_or_stolen, card_expired, mandate_expired MUST route to alternate_method
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "card_lost_or_stolen", 1) == InterventionType.ALTERNATE_METHOD
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "card_expired", 1) == InterventionType.ALTERNATE_METHOD
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "mandate_expired", 1) == InterventionType.ALTERNATE_METHOD
    # Even if attempt_number is 1
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "card_expired", 1) != InterventionType.SILENT_RETRY
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "card_expired", 1) != InterventionType.DELAYED_RETRY_NOTIFY


def test_gateway_sync_gap_escalates_human():
    assert select_intervention(FaultAttribution.INFRASTRUCTURE_FAULT, "gateway_data_sync_gap", 1) == InterventionType.ESCALATE_HUMAN


def test_infrastructure_fault_silent_retry_then_escalate():
    assert select_intervention(FaultAttribution.INFRASTRUCTURE_FAULT, "issuer_timeout", 1) == InterventionType.SILENT_RETRY
    assert select_intervention(FaultAttribution.INFRASTRUCTURE_FAULT, "issuer_timeout", 2) == InterventionType.ESCALATE_HUMAN


def test_customer_fault_plausible_retry():
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "insufficient_balance", 1) == InterventionType.DELAYED_RETRY_NOTIFY
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "insufficient_credit_limit", 1) == InterventionType.DELAYED_RETRY_NOTIFY
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "daily_upi_limit_exceeded", 1) == InterventionType.DELAYED_RETRY_NOTIFY


def test_customer_fault_structural_failure():
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "wallet_kyc_lapsed", 1) == InterventionType.ALTERNATE_METHOD
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "card_not_emi_eligible", 1) == InterventionType.ALTERNATE_METHOD
    assert select_intervention(FaultAttribution.CUSTOMER_FAULT, "wrong_upi_pin", 1) == InterventionType.ALTERNATE_METHOD


def test_unknown_fault_escalates():
    assert select_intervention(FaultAttribution.UNKNOWN, None, 1) == InterventionType.ESCALATE_HUMAN
