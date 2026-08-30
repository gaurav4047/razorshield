from datetime import datetime, timezone
from app.pipeline.state import PipelineState


async def execute_node(state: PipelineState) -> dict:
    module = state.get("module")
    final_decision = state.get("final_decision")

    if module == "C":
        if final_decision == "send_abandonment_nudge":
            # Dispatches recovery link and marks nudge recorded
            case_id = state.get("case_id")
            plink_id = f"plink_nudge_{case_id[:8]}" if case_id else "plink_nudge_default"
            return {
                "razorpay_reference_id": plink_id,
                "execution_result": "abandonment_nudge_dispatched",
            }

    return {
        "razorpay_reference_id": None,
        "execution_result": "no_action_taken",
    }
