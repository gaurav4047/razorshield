from typing import Any, Literal, TypedDict


class PipelineState(TypedDict, total=False):
    module: Literal["A", "B", "C"]
    case_id: str
    batch_id: str

    # Module C / Order specific fields
    order_amount_paise: int | None
    order_created_at: str | None
    nudge_sent: bool | None
    abandonment_detected: bool | None

    # Module A / PaymentCase specific fields
    method: str | None
    context: str | None
    failure_code: str | None
    failure_raw_reason: str | None
    attempt_number: int | None
    retry_count: int | None
    last_action_at: str | None

    # Module B / Invoice specific fields
    statutory_due_date: str | None
    current_rung: int | None
    dispute_flag: bool | None
    broken_promise_count: int | None
    supplier_is_msme: bool | None
    computed_interest_paise: int | None
    last_contact_at: str | None
    human_approved: bool | None
    buyer_response_text: str | None

    # Populated by DIAGNOSE
    fault_attribution: str | None
    classified_root_cause: str | None
    ai_reasoning: str | None
    diagnosis_confidence: float | None
    recommended_intervention: str | None

    # Populated by POLICY GATE
    policy_passed: bool
    stopping_rules_checked: list[dict[str, Any]]
    rule_recommendation: str | None
    final_decision: str
    reason: str | None
    npci_window_conflict: bool | None
    reschedule_at: str | None

    # Populated by EXECUTE
    razorpay_reference_id: str | None
    execution_result: str | None

    # Populated by AUDIT
    audit_entry_id: int | None
