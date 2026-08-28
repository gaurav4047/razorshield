from app.db.models.payment_case import FaultAttribution, PaymentMethod
from app.domain_logic.payment_taxonomy import classify_root_cause


def test_classify_card_codes():
    cause, fault = classify_root_cause(PaymentMethod.CARD, "91", "Issuer inoperative")
    assert cause == "issuer_timeout"
    assert fault == FaultAttribution.INFRASTRUCTURE_FAULT

    cause, fault = classify_root_cause(PaymentMethod.CARD, "54", "Expired card")
    assert cause == "card_expired"
    assert fault == FaultAttribution.CUSTOMER_FAULT


def test_classify_upi_keywords():
    cause, fault = classify_root_cause(PaymentMethod.UPI, None, "NPCI switch timeout")
    assert cause == "npci_switch_timeout"
    assert fault == FaultAttribution.INFRASTRUCTURE_FAULT

    cause, fault = classify_root_cause(PaymentMethod.UPI, None, "Customer has low balance")
    assert cause == "insufficient_balance"
    assert fault == FaultAttribution.CUSTOMER_FAULT


def test_classify_netbanking_sync_gap():
    cause, fault = classify_root_cause(PaymentMethod.NETBANKING, None, "Data sync gap between bank and merchant")
    assert cause == "gateway_data_sync_gap"
    assert fault == FaultAttribution.INFRASTRUCTURE_FAULT


def test_classify_unmatched_fallback():
    cause, fault = classify_root_cause(PaymentMethod.UPI, None, "Random unrecognized glitch")
    assert cause is None
    assert fault == FaultAttribution.UNKNOWN
