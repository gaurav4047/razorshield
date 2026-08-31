from datetime import date, datetime, timedelta, timezone
from app.ai_layer.prompts.conflicting_signal_reasoning import evaluate_conflicting_signals
from app.ai_layer.prompts.reply_classification import classify_buyer_reply
from app.ai_layer.prompts.signal_parsing import parse_failure_signal
from app.config import settings
from app.db.models.payment_case import FaultAttribution, PaymentMethod
from app.domain_logic.escalation_ladder import compute_escalation_rung
from app.domain_logic.intervention_types import select_intervention
from app.domain_logic.msmed import compute_accrued_interest
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
        case_history = state.get("case_history")

        # 1. Deterministic fault attribution & taxonomy classification per 03_domain_logic.md §1-2
        root_cause, deterministic_attribution = classify_root_cause(
            method=method_enum,
            failure_code=failure_code,
            raw_reason=raw_reason,
        )

        if deterministic_attribution != FaultAttribution.UNKNOWN and root_cause is not None:
            # Deterministic path: direct taxonomy classification
            intervention_enum = select_intervention(
                fault_attribution=deterministic_attribution,
                classified_root_cause=root_cause,
                attempt_number=attempt_number,
            )

            # Step 5: Conflicting-signal reasoning if case history provides conflicting context
            if case_history:
                ai_eval = await evaluate_conflicting_signals(
                    classified_root_cause=root_cause,
                    naive_rule_suggestion=intervention_enum.value,
                    relevant_case_history=case_history,
                )
                final_rec = ai_eval.recommended_intervention if not ai_eval.agrees_with_default else intervention_enum.value
                return {
                    "fault_attribution": deterministic_attribution.value,
                    "classified_root_cause": root_cause,
                    "ai_reasoning": ai_eval.reasoning,
                    "diagnosis_confidence": 0.95,
                    "recommended_intervention": final_rec,
                    "rule_recommendation": intervention_enum.value,
                }

            return {
                "fault_attribution": deterministic_attribution.value,
                "classified_root_cause": root_cause,
                "ai_reasoning": None,
                "diagnosis_confidence": 1.0,
                "recommended_intervention": intervention_enum.value,
                "rule_recommendation": intervention_enum.value,
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
        normalized_root_cause = CANONICAL_ROOT_CAUSE_MAP.get(raw_classified, raw_classified)

        is_valid_cause = normalized_root_cause in valid_causes

        if not is_valid_cause:
            return {
                "fault_attribution": "unknown",
                "classified_root_cause": None,
                "ai_reasoning": f"Rejected invalid root cause '{raw_classified}': not in closed vocabulary. {reasoning}",
                "diagnosis_confidence": 0.0,
                "recommended_intervention": "escalate_human",
                "rule_recommendation": "escalate_human",
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

        # Step 5: Conflicting-signal reasoning if case history provides conflicting context
        if case_history and is_valid_cause:
            ai_eval = await evaluate_conflicting_signals(
                classified_root_cause=normalized_root_cause,
                naive_rule_suggestion=intervention,
                relevant_case_history=case_history,
            )
            final_rec = ai_eval.recommended_intervention if not ai_eval.agrees_with_default else intervention
            return {
                "fault_attribution": fault_attr,
                "classified_root_cause": normalized_root_cause,
                "ai_reasoning": ai_eval.reasoning,
                "diagnosis_confidence": confidence,
                "recommended_intervention": final_rec,
                "rule_recommendation": intervention,
            }

        return {
            "fault_attribution": fault_attr,
            "classified_root_cause": normalized_root_cause,
            "ai_reasoning": reasoning,
            "diagnosis_confidence": confidence,
            "recommended_intervention": intervention,
            "rule_recommendation": intervention,
        }

    if module == "B":
        # Module B: Escalation ladder, reply classification & MSMED interest
        due_date_str = state.get("statutory_due_date")
        statutory_due_date = date.fromisoformat(due_date_str) if due_date_str else date.today()
        current_rung = state.get("current_rung", 0) or 0
        dispute_flag = bool(state.get("dispute_flag", False))
        broken_promise_count = state.get("broken_promise_count", 0) or 0
        supplier_is_msme = bool(state.get("supplier_is_msme", True))
        amount_paise = state.get("order_amount_paise") or 0
        buyer_reply = state.get("buyer_response_text")

        now_date = date.today()

        # Check for active dispute first
        if dispute_flag:
            return {
                "dispute_flag": True,
                "recommended_intervention": "halt_dispute_active",
                "ai_reasoning": None,
                "diagnosis_confidence": 1.0,
            }

        # If there's an incoming buyer response, classify it with Groq
        if buyer_reply:
            reply_output = await classify_buyer_reply(
                raw_message=buyer_reply,
                amount_paise=amount_paise,
                days_overdue=max(0, (now_date - statutory_due_date).days),
                reminder_count=current_rung,
            )
            classified_as = reply_output.classified_as
            confidence = float(reply_output.confidence)
            reasoning = reply_output.brief_reasoning

            # Critical Rule: If classified as dispute OR low confidence dispute-leaning, halt immediately (fail toward caution)
            if classified_as == "dispute" or (confidence < settings.AI_CONFIDENCE_THRESHOLD and "dispute" in reasoning.lower()):
                return {
                    "dispute_flag": True,
                    "recommended_intervention": "halt_dispute_active",
                    "ai_reasoning": f"Buyer reply classified as dispute: {reasoning}",
                    "diagnosis_confidence": confidence,
                }

            if classified_as == "promise_to_pay":
                return {
                    "recommended_intervention": "record_promise",
                    "ai_reasoning": f"Promise to pay recorded: {reasoning}",
                    "diagnosis_confidence": confidence,
                }

        # Deterministic Rung advancement & MSMED Interest Calculation (zero AI calls)
        target_rung = compute_escalation_rung(
            statutory_due_date=statutory_due_date,
            as_of_date=now_date,
            broken_promise_count=broken_promise_count,
        )

        interest_paise = 0
        if supplier_is_msme and target_rung >= 2:
            interest_paise = compute_accrued_interest(
                amount_paise=amount_paise,
                statutory_due_date=statutory_due_date,
                as_of_date=now_date,
                rbi_bank_rate=settings.RBI_BANK_RATE,
            )

        return {
            "current_rung": target_rung,
            "computed_interest_paise": interest_paise,
            "recommended_intervention": f"rung_{target_rung}_action",
            "ai_reasoning": None,
            "diagnosis_confidence": 1.0,
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
