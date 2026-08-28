from app.db.models.payment_case import FaultAttribution, PaymentMethod
from app.domain_logic.fault_attribution import (
    AMBIGUOUS_CARD_CODES,
    CARD_DECLINE_CODES,
    attribute_fault,
)

# Exhaustive closed-set root causes per payment method
CLOSED_ROOT_CAUSES: dict[PaymentMethod, dict[str, list[str]]] = {
    PaymentMethod.UPI: {
        "insufficient_balance": ["insufficient", "low balance", "not enough funds", "balance low"],
        "wrong_upi_pin": ["wrong pin", "incorrect pin", "invalid upi pin", "wrong upi pin", "mpin", "pin incorrect"],
        "mandate_expired": ["mandate expired", "autopay expired", "mandate inactive", "expired mandate"],
        "daily_upi_limit_exceeded": ["daily limit", "transaction limit exceeded", "limit exceeded", "max limit"],
        "npci_execution_window_block": ["execution window", "npci window", "window block", "off-peak"],
        "upi_bank_server_unavailable": ["bank server", "bank unavailable", "remitter bank down", "issuer bank down"],
        "npci_switch_timeout": ["npci switch", "switch timeout", "npci timeout", "switch down"],
    },
    PaymentMethod.CARD: {
        "insufficient_credit_limit": ["insufficient credit", "credit limit", "limit insufficient", "low balance"],
        "card_expired": ["card expired", "expired card", "validity expired"],
        "card_lost_or_stolen": ["lost", "stolen", "pick up card", "hotlist"],
        "issuer_timeout": ["issuer timeout", "bank timeout", "issuer inoperative", "no response from bank"],
        "network_glitch": ["network glitch", "system malfunction", "network error", "transmission error"],
        "authentication_server_down": ["authentication server", "3ds server", "3ds", "acs down", "otp server down"],
    },
    PaymentMethod.NETBANKING: {
        "insufficient_balance": ["insufficient", "low balance", "balance"],
        "daily_transfer_limit_exceeded": ["transfer limit", "daily transfer limit", "limit exceeded"],
        "incorrect_account_details": ["incorrect account", "invalid account", "account number wrong"],
        "session_timeout": ["session timeout", "inactivity logout", "session expired"],
        "bank_server_downtime": ["bank downtime", "netbanking server down", "bank maintenance", "bank down"],
        "gateway_data_sync_gap": ["data sync", "sync gap", "confirmation lost", "reconciliation pending"],
    },
    PaymentMethod.WALLET: {
        "wallet_kyc_lapsed": ["kyc lapsed", "kyc expired", "min-kyc", "kyc pending", "kyc"],
        "insufficient_wallet_balance": ["wallet balance low", "insufficient wallet balance", "low wallet balance"],
        "wallet_fraud_hold": ["fraud hold", "suspicious activity", "wallet hold"],
        "wallet_institutional_freeze": ["institutional freeze", "regulatory freeze", "rbi freeze", "bank freeze"],
    },
    PaymentMethod.EMI: {
        "card_not_emi_eligible": ["not emi eligible", "card ineligible", "ineligible card", "emi not supported"],
        "credit_utilization_exceeded": ["credit utilization", "sanctioned limit", "utilization exceeded"],
        "below_minimum_emi_threshold": ["below minimum emi", "minimum emi threshold", "minimum order value for emi"],
        "no_merchant_bank_emi_tieup": ["no merchant tieup", "no bank tieup", "tie-up unavailable"],
        "emi_option_unavailable_high_traffic": ["high traffic", "emi service busy", "emi unavailable"],
    },
}


def classify_root_cause(
    method: PaymentMethod,
    failure_code: str | None,
    raw_reason: str,
) -> tuple[str | None, FaultAttribution]:
    # 1. Exact match on known decline codes
    if method == PaymentMethod.CARD and failure_code:
        code_clean = failure_code.strip()
        if code_clean in CARD_DECLINE_CODES:
            root_cause, fault = CARD_DECLINE_CODES[code_clean]
            return root_cause, fault
        if code_clean in AMBIGUOUS_CARD_CODES:
            return None, FaultAttribution.UNKNOWN

    # 2. Keyword matching against raw_reason
    raw_lower = raw_reason.lower()
    method_causes = CLOSED_ROOT_CAUSES.get(method, {})
    for cause, keywords in method_causes.items():
        if any(keyword in raw_lower for keyword in keywords):
            fault = attribute_fault(method, failure_code, raw_reason)
            return cause, fault

    # 3. Unmatched -> route to AI layer
    fault = attribute_fault(method, failure_code, raw_reason)
    return None, fault
