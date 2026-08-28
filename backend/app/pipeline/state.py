from typing import Any, Literal, TypedDict


class PipelineState(TypedDict):
    module: Literal["A", "B", "C"]
    case_id: str

    fault_attribution: str | None
    classified_root_cause: str | None
    ai_reasoning: str | None
    diagnosis_confidence: float | None
    recommended_intervention: str | None

    stopping_rules_checked: list[dict[str, Any]]
    rule_recommendation: str | None
    final_decision: str

    razorpay_reference_id: str | None
    execution_result: str | None

    audit_entry_id: int | None
