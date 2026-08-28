from app.db.models.payment_case import FaultAttribution, PaymentMethod
from app.domain_logic.fault_attribution import attribute_fault


def test_card_decline_codes_attribution():
    assert attribute_fault(PaymentMethod.CARD, "91", "") == FaultAttribution.INFRASTRUCTURE_FAULT
    assert attribute_fault(PaymentMethod.CARD, "96", "") == FaultAttribution.INFRASTRUCTURE_FAULT
    assert attribute_fault(PaymentMethod.CARD, "41", "") == FaultAttribution.CUSTOMER_FAULT
    assert attribute_fault(PaymentMethod.CARD, "43", "") == FaultAttribution.CUSTOMER_FAULT
    assert attribute_fault(PaymentMethod.CARD, "54", "") == FaultAttribution.CUSTOMER_FAULT
    assert attribute_fault(PaymentMethod.CARD, "51", "") == FaultAttribution.CUSTOMER_FAULT
    assert attribute_fault(PaymentMethod.CARD, "05", "") == FaultAttribution.UNKNOWN
    assert attribute_fault(PaymentMethod.CARD, "14", "") == FaultAttribution.UNKNOWN


def test_upi_keyword_attribution():
    assert attribute_fault(PaymentMethod.UPI, None, "Insufficient funds in account") == FaultAttribution.CUSTOMER_FAULT
    assert attribute_fault(PaymentMethod.UPI, None, "NPCI execution window block") == FaultAttribution.INFRASTRUCTURE_FAULT
    assert attribute_fault(PaymentMethod.UPI, None, "Remitter bank server down") == FaultAttribution.INFRASTRUCTURE_FAULT
    assert attribute_fault(PaymentMethod.UPI, None, "Incorrect MPIN entered") == FaultAttribution.CUSTOMER_FAULT


def test_netbanking_sync_gap_attribution():
    assert attribute_fault(PaymentMethod.NETBANKING, None, "Gateway data sync gap confirmation lost") == FaultAttribution.INFRASTRUCTURE_FAULT
    assert attribute_fault(PaymentMethod.NETBANKING, None, "Session timeout due to inactivity") == FaultAttribution.INFRASTRUCTURE_FAULT
    assert attribute_fault(PaymentMethod.NETBANKING, None, "Daily transfer limit exceeded") == FaultAttribution.CUSTOMER_FAULT


def test_wallet_and_emi_attribution():
    assert attribute_fault(PaymentMethod.WALLET, None, "Min-KYC lapsed grace period expired") == FaultAttribution.CUSTOMER_FAULT
    assert attribute_fault(PaymentMethod.WALLET, None, "Wallet institutional freeze by RBI") == FaultAttribution.INFRASTRUCTURE_FAULT
    assert attribute_fault(PaymentMethod.EMI, None, "Card not EMI eligible") == FaultAttribution.CUSTOMER_FAULT
    assert attribute_fault(PaymentMethod.EMI, None, "No merchant bank tieup available") == FaultAttribution.INFRASTRUCTURE_FAULT


def test_unknown_reason_returns_unknown():
    assert attribute_fault(PaymentMethod.CARD, None, "XYZ unclassified failure string") == FaultAttribution.UNKNOWN
