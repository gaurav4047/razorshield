from datetime import datetime, timedelta, timezone
from app.ai_layer.prompts.signal_parsing import parse_failure_signal
from app.config import settings
from app.db.models.payment_case import FaultAttribution, PaymentMethod
from app.domain_logic.intervention_types import select_intervention
from app.domain_logic.payment_taxonomy import classify_root_cause
from app.pipeline.state import PipelineState


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

        root_cause = ai_res.classified_root_cause
        fault_attr = ai_res.fault_attribution
        confidence = float(ai_res.confidence)
        reasoning = ai_res.brief_reasoning

        # 3. Confidence Threshold Gate: Low confidence forces human escalation per 05_ai_layer.md §4a
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
                classified_root_cause=root_cause,
                attempt_number=attempt_number,
            )
            intervention = intervention_enum.value

        return {
            "fault_attribution": fault_attr,
            "classified_root_cause": root_cause,
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
