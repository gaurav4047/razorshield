from datetime import datetime, timezone
from app.db.models.payment_case import InterventionType, PaymentContext, PaymentMethod
from app.domain_logic.stopping_rules import (
    check_module_a_policy_gate,
    check_module_b_policy_gate,
    check_module_c_policy_gate,
)
from app.pipeline.state import PipelineState


async def policy_gate_node(state: PipelineState) -> dict:
    module = state.get("module")

    if module == "A":
        method_str = state.get("method", "card")
        context_str = state.get("context", "one_time")
        root_cause = state.get("classified_root_cause")
        intervention_str = state.get("recommended_intervention")
        retry_count = state.get("retry_count", 0) or 0
        attempt_number = state.get("attempt_number", 1) or 1

        method_enum = (
            PaymentMethod(method_str)
            if method_str in PaymentMethod._value2member_map_
            else PaymentMethod.CARD
        )
        context_enum = (
            PaymentContext(context_str)
            if context_str in PaymentContext._value2member_map_
            else PaymentContext.ONE_TIME
        )
        intervention_enum = (
            InterventionType(intervention_str)
            if intervention_str in InterventionType._value2member_map_
            else None
        )

        last_action_str = state.get("last_action_at")
        last_action_dt = datetime.fromisoformat(last_action_str) if last_action_str else None
        now_dt = datetime.now(timezone.utc)

        gate_res = check_module_a_policy_gate(
            method=method_enum,
            context=context_enum,
            classified_root_cause=root_cause,
            recommended_intervention=intervention_enum,
            attempt_number=attempt_number,
            retry_count=retry_count,
            last_action_at=last_action_dt,
            now=now_dt,
        )

        return {
            "policy_passed": gate_res.allowed,
            "final_decision": gate_res.final_action,
            "reason": gate_res.reason,
            "stopping_rules_checked": gate_res.stopping_rules_checked,
            "rule_recommendation": gate_res.rule_recommendation,
            "npci_window_conflict": gate_res.npci_window_conflict,
            "reschedule_at": gate_res.reschedule_at.isoformat() if gate_res.reschedule_at else None,
        }

    if module == "B":
        dispute_flag = bool(state.get("dispute_flag", False))
        broken_promise_count = state.get("broken_promise_count", 0) or 0
        current_rung = state.get("current_rung", 0) or 0
        supplier_is_msme = bool(state.get("supplier_is_msme", True))
        computed_interest_paise = state.get("computed_interest_paise")
        human_approved = bool(state.get("human_approved", False))

        last_contact_str = state.get("last_contact_at")
        last_contact_dt = datetime.fromisoformat(last_contact_str) if last_contact_str else None
        now_dt = datetime.now(timezone.utc)

        gate_res = check_module_b_policy_gate(
            dispute_flag=dispute_flag,
            broken_promise_count=broken_promise_count,
            current_rung=current_rung,
            target_rung=current_rung,
            last_contact_at=last_contact_dt,
            computed_interest_paise=computed_interest_paise,
            supplier_is_msme=supplier_is_msme,
            human_approved=human_approved,
            now=now_dt,
        )

        return {
            "policy_passed": gate_res.allowed,
            "final_decision": gate_res.final_action,
            "reason": gate_res.reason,
            "stopping_rules_checked": gate_res.stopping_rules_checked,
            "rule_recommendation": gate_res.rule_recommendation,
        }

    if module == "C":
        amount_paise = state.get("order_amount_paise") or 0
        nudge_sent = bool(state.get("nudge_sent", False))
        abandonment_detected = state.get("abandonment_detected", True)

        if not abandonment_detected:
            return {
                "policy_passed": False,
                "final_decision": "wait_abandonment_window",
                "reason": "Order within normal checkout window; not yet abandoned",
                "stopping_rules_checked": [
                    {
                        "rule": "abandonment_window_check",
                        "passed": False,
                        "detail": "Order has not yet exceeded abandonment threshold",
                    }
                ],
                "rule_recommendation": None,
            }

        gate_res = check_module_c_policy_gate(
            amount_paise=amount_paise,
            nudge_sent=nudge_sent,
        )

        return {
            "policy_passed": gate_res.allowed,
            "final_decision": gate_res.final_action,
            "reason": gate_res.reason,
            "stopping_rules_checked": gate_res.stopping_rules_checked,
            "rule_recommendation": gate_res.rule_recommendation,
        }

    return {}
