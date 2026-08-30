from datetime import datetime, timezone
from app.pipeline.state import PipelineState


async def execute_node(state: PipelineState) -> dict:
    module = state.get("module")
    final_decision = state.get("final_decision")
    case_id = state.get("case_id", "case")
    prefix = case_id[:8] if case_id else "0000"

    if module == "A":
        if final_decision == "silent_retry":
            return {
                "razorpay_reference_id": f"retry_sub_{prefix}",
                "execution_result": "silent_retry_executed",
            }
        elif final_decision == "delayed_retry_notify":
            return {
                "razorpay_reference_id": f"notif_cust_{prefix}",
                "execution_result": "customer_notified_and_scheduled",
            }
        elif final_decision == "alternate_method":
            return {
                "razorpay_reference_id": f"plink_alt_{prefix}",
                "execution_result": "alternate_payment_link_sent",
            }
        elif final_decision == "escalate_human":
            return {
                "razorpay_reference_id": None,
                "execution_result": "queued_for_human_agent",
            }

    if module == "C":
        if final_decision == "send_abandonment_nudge":
            plink_id = f"plink_nudge_{prefix}"
            return {
                "razorpay_reference_id": plink_id,
                "execution_result": "abandonment_nudge_dispatched",
            }

    return {
        "razorpay_reference_id": None,
        "execution_result": "no_action_taken",
    }
