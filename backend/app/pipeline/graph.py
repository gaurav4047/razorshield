from typing import Literal
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.pipeline.nodes.audit import audit_node
from app.pipeline.nodes.diagnose import diagnose_node
from app.pipeline.nodes.execute import execute_node
from app.pipeline.nodes.policy_gate import policy_gate_node
from app.pipeline.state import PipelineState

ACTIVE_EXECUTION_DECISIONS = {
    "send_abandonment_nudge",
    "silent_retry",
    "delayed_retry_notify",
    "alternate_method",
    "first_reminder_with_payment_link",
    "second_reminder_with_interest",
    "formal_notice_cc_controller",
}


def build_module_graph(module: Literal["A", "B", "C"]) -> CompiledStateGraph:
    workflow = StateGraph(PipelineState)
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("policy_gate", policy_gate_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("audit", audit_node)

    workflow.set_entry_point("diagnose")
    workflow.add_edge("diagnose", "policy_gate")

    # Policy gate routes to execute if action is approved;
    # Blocked or non-action outcomes route directly to audit (unconditional audit guarantee)
    def route_after_policy_gate(state: PipelineState) -> str:
        if state.get("policy_passed") and state.get("final_decision") in ACTIVE_EXECUTION_DECISIONS:
            return "execute"
        return "audit"

    workflow.add_conditional_edges(
        "policy_gate",
        route_after_policy_gate,
        {"execute": "execute", "audit": "audit"},
    )
    workflow.add_edge("execute", "audit")
    workflow.add_edge("audit", END)

    return workflow.compile()
