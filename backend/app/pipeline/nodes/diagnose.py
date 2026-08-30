from datetime import datetime, timedelta, timezone
from app.config import settings
from app.domain_logic.fault_attribution import attribute_fault
from app.domain_logic.intervention_types import select_intervention
from app.domain_logic.payment_taxonomy import classify_root_cause
from app.pipeline.state import PipelineState


async def diagnose_node(state: PipelineState) -> dict:
    module = state.get("module")

    if module == "C":
        # Pure deterministic timeout check per 03_domain_logic.md §6 & 05_ai_layer.md §3
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
