from datetime import datetime, timedelta, timezone
from app.ai_layer.prompts.signal_parsing import parse_failure_signal
from app.config import settings
from app.db.models.payment_case import FaultAttribution, PaymentMethod
from app.domain_logic.intervention_types import select_intervention
from app.domain_logic.payment_taxonomy import (
    classify_root_cause,
    get_valid_root_causes_for_method,
)
from app.pipeline.state import PipelineState

# Canonical alias mapping for common LLM variations
CANONICAL_ROOT_CAUSE_MAP = {
    "upi_bank_unavailable": "upi_bank_server_unavailable",
    "bank_unavailable": "upi_bank_server_unavailable",
    "bank_timeout": "upi_bank_server_unavailable",
    "npci_timeout": "npci_switch_timeout",
    "npci_degraded": "npci_switch_timeout",
    "upi_psp_unavailable": "upi_bank_server_unavailable",
    "upi_beneficiary_timeout": "upi_bank_server_unavailable",
    "3ds_timeout": "issuer_timeout",
    "gateway_timeout": "issuer_timeout",
    "card_gateway_timeout": "issuer_timeout",
    "card_3ds_timeout": "issuer_timeout",
    "card_network_error": "network_glitch",
    "card_system_error": "network_glitch",
    "card_invalid_cvv": "card_lost_or_stolen",
    "card_do_not_honor": "card_lost_or_stolen",
    "card_suspected_fraud": "card_lost_or_stolen",
    "card_invalid_number": "card_lost_or_stolen",
    "upi_invalid_mpin": "wrong_upi_pin",
    "upi_mpin_exceeded": "wrong_upi_pin",
    "upi_vpa_deactivated": "mandate_expired",
    "upi_user_dropped": "insufficient_balance",
}


async def diagnose_node(state: PipelineState) -> dict:
    module = state.get("module")

    if module == "A":
        method_str = state.get("method", "card")
        method_enum = (
            PaymentMethod(method_str)
            if method_str in PaymentMethod._value2member_map_
            else PaymentMethod.CARD
        )
        failure_code = state.get("failure_code")
        raw_reason = state.get("failure_raw_reason", "")
        attempt_number = state.get("attempt_number", 1) or 1

        # 1. Deterministic fault attribution & taxonomy classification per 03_domain_logic.md §1-2
        root_cause, deterministic_attribution = classify_root_cause(
            method=method_enum,
            failure_code=failure_code,
            raw_reason=raw_reason,
        )

        if deterministic_attribution != FaultAttribution.UNKNOWN and root_cause is not None:
            # Deterministic path: direct taxonomy classification without LLM call
            intervention_enum = select_intervention(
                fault_attribution=deterministic_attribution,
                classified_root_cause=root_cause,
                attempt_number=attempt_number,
            )
            return {
                "fault_attribution": deterministic_attribution.value,
                "classified_root_cause": root_cause,
                "ai_reasoning": None,
                "diagnosis_confidence": 1.0,
                "recommended_intervention": intervention_enum.value,
            }

        # 2. AI Fallback: Invoke Groq signal parsing prompt only when attribution is unknown
        ai_res = await parse_failure_signal(
            method=method_str,
            raw_reason=raw_reason,
            failure_code=failure_code,
        )

        raw_classified = (ai_res.classified_root_cause or "").strip().lower()
        fault_attr = ai_res.fault_attribution
        confidence = float(ai_res.confidence)
        reasoning = ai_res.brief_reasoning

        # 3. Post-call validation against closed vocabulary per 05_ai_layer.md §4a
        valid_causes = get_valid_root_causes_for_method(method_enum)

        # Normalize via canonical alias map if needed
        normalized_root_cause = CANONICAL_ROOT_CAUSE_MAP.get(raw_classified, raw_classified)

        is_valid_cause = normalized_root_cause in valid_causes

        if not is_valid_cause:
            # Invalid/unmatched category returned by model -> reject and escalate to human
            return {
                "fault_attribution": "unknown",
                "classified_root_cause": None,
                "ai_reasoning": f"Rejected invalid root cause '{raw_classified}': not in closed vocabulary. {reasoning}",
                "diagnosis_confidence": 0.0,
                "recommended_intervention": "escalate_human",
            }

        # 4. Confidence Threshold Gate: Low confidence forces human escalation
        if confidence < settings.AI_CONFIDENCE_THRESHOLD:
            intervention = "escalate_human"
        else:
            attr_enum = (
                FaultAttribution(fault_attr)
                if fault_attr in ("customer_fault", "infrastructure_fault")
                else FaultAttribution.UNKNOWN
            )
            intervention_enum = select_intervention(
                fault_attribution=attr_enum,
                classified_root_cause=normalized_root_cause,
                attempt_number=attempt_number,
            )
            intervention = intervention_enum.value

        return {
            "fault_attribution": fault_attr,
            "classified_root_cause": normalized_root_cause,
            "ai_reasoning": reasoning,
            "diagnosis_confidence": confidence,
            "recommended_intervention": intervention,
        }

    if module == "C":
        order_created_str = state.get("order_created_at")
        threshold_mins = settings.ABANDONED_ORDER_THRESHOLD_MINUTES

        is_abandoned = True
        if order_created_str:
            order_created_at = datetime.fromisoformat(order_created_str)
            now = datetime.now(timezone.utc)
            if (now - order_created_at) < timedelta(minutes=threshold_mins):
                is_abandoned = False

        if not is_abandoned:
            return {
                "abandonment_detected": False,
                "recommended_intervention": "wait",
                "fault_attribution": "unknown",
                "classified_root_cause": None,
                "ai_reasoning": None,
                "diagnosis_confidence": 1.0,
            }

        return {
            "abandonment_detected": True,
            "recommended_intervention": "send_abandonment_nudge",
            "fault_attribution": "customer_fault",
            "classified_root_cause": "checkout_abandonment",
            "ai_reasoning": None,
            "diagnosis_confidence": 1.0,
        }

    return {}
