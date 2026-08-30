from app.domain_logic.stopping_rules import (
    check_module_a_policy_gate,
    check_module_b_policy_gate,
    check_module_c_policy_gate,
)
from app.pipeline.state import PipelineState


async def policy_gate_node(state: PipelineState) -> dict:
    module = state.get("module")

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
