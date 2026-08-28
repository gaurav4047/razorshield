from app.db.models.payment_case import FaultAttribution, PaymentMethod

CUSTOMER_FAULT_CAUSES: dict[PaymentMethod, set[str]] = {
    PaymentMethod.UPI: {
        "insufficient_balance",
        "wrong_upi_pin",
        "mandate_expired",
        "daily_upi_limit_exceeded",
    },
    PaymentMethod.CARD: {
        "insufficient_credit_limit",
        "card_expired",
        "card_lost_or_stolen",
    },
    PaymentMethod.NETBANKING: {
        "insufficient_balance",
        "daily_transfer_limit_exceeded",
        "incorrect_account_details",
    },
    PaymentMethod.WALLET: {
        "wallet_kyc_lapsed",
        "insufficient_wallet_balance",
    },
    PaymentMethod.EMI: {
        "card_not_emi_eligible",
        "credit_utilization_exceeded",
        "below_minimum_emi_threshold",
    },
}

INFRASTRUCTURE_FAULT_CAUSES: dict[PaymentMethod, set[str]] = {
    PaymentMethod.UPI: {
        "npci_execution_window_block",
        "upi_bank_server_unavailable",
        "npci_switch_timeout",
    },
    PaymentMethod.CARD: {
        "issuer_timeout",
        "network_glitch",
        "authentication_server_down",
    },
    PaymentMethod.NETBANKING: {
        "session_timeout",
        "bank_server_downtime",
        "gateway_data_sync_gap",
    },
    PaymentMethod.WALLET: {
        "wallet_fraud_hold",
        "wallet_institutional_freeze",
    },
    PaymentMethod.EMI: {
        "no_merchant_bank_emi_tieup",
        "emi_option_unavailable_high_traffic",
    },
}

CARD_DECLINE_CODES: dict[str, tuple[str, FaultAttribution]] = {
    "91": ("issuer_timeout", FaultAttribution.INFRASTRUCTURE_FAULT),
    "96": ("network_glitch", FaultAttribution.INFRASTRUCTURE_FAULT),
    "41": ("card_lost_or_stolen", FaultAttribution.CUSTOMER_FAULT),
    "43": ("card_lost_or_stolen", FaultAttribution.CUSTOMER_FAULT),
    "54": ("card_expired", FaultAttribution.CUSTOMER_FAULT),
    "51": ("insufficient_credit_limit", FaultAttribution.CUSTOMER_FAULT),
}

AMBIGUOUS_CARD_CODES = {"05", "14"}


def attribute_fault(method: PaymentMethod, failure_code: str | None, raw_reason: str) -> FaultAttribution:
    if method == PaymentMethod.CARD and failure_code:
        code_clean = failure_code.strip()
        if code_clean in CARD_DECLINE_CODES:
            return CARD_DECLINE_CODES[code_clean][1]
        if code_clean in AMBIGUOUS_CARD_CODES:
            return FaultAttribution.UNKNOWN

    raw_lower = raw_reason.lower()

    if method == PaymentMethod.NETBANKING:
        if any(k in raw_lower for k in ("data sync", "sync gap", "confirmation lost", "reconciliation pending")):
            return FaultAttribution.INFRASTRUCTURE_FAULT

    infra_keywords = {
        PaymentMethod.UPI: ["execution window", "bank server", "remitter bank down", "issuer bank down", "npci switch", "switch timeout", "switch down"],
        PaymentMethod.CARD: ["issuer timeout", "bank timeout", "inoperative", "system malfunction", "network glitch", "network error", "authentication server", "3ds", "acs down", "otp server"],
        PaymentMethod.NETBANKING: ["session timeout", "inactivity logout", "session expired", "bank downtime", "server down", "bank maintenance"],
        PaymentMethod.WALLET: ["fraud hold", "suspicious activity", "institutional freeze", "regulatory freeze", "rbi freeze"],
        PaymentMethod.EMI: ["tieup", "tie-up", "no merchant tieup", "no bank tieup", "high traffic", "service busy", "unavailable high traffic"],
    }

    if any(k in raw_lower for k in infra_keywords.get(method, [])):
        return FaultAttribution.INFRASTRUCTURE_FAULT

    cust_keywords = {
        PaymentMethod.UPI: ["insufficient", "low balance", "wrong pin", "invalid pin", "incorrect pin", "mpin", "mandate expired", "autopay expired", "limit exceeded", "daily limit"],
        PaymentMethod.CARD: ["lost", "stolen", "pick up card", "hotlist", "card expired", "expired card", "insufficient credit", "credit limit", "low balance"],
        PaymentMethod.NETBANKING: ["insufficient", "low balance", "transfer limit", "incorrect account", "invalid account"],
        PaymentMethod.WALLET: ["kyc lapsed", "kyc expired", "min-kyc", "kyc pending", "wallet balance low", "insufficient wallet"],
        PaymentMethod.EMI: ["not emi eligible", "card ineligible", "ineligible card", "credit utilization", "sanctioned limit", "below minimum emi", "minimum emi threshold"],
    }

    if any(k in raw_lower for k in cust_keywords.get(method, [])):
        return FaultAttribution.CUSTOMER_FAULT

    return FaultAttribution.UNKNOWN
