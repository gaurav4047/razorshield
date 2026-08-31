import uuid
import pytest
from sqlalchemy import select
from app.ai_layer.prompts.conflicting_signal_reasoning import evaluate_conflicting_signals
from app.db.models.audit_log import AuditLogEntry
from app.db.models.batch import Batch
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus, PaymentContext, PaymentMethod
from app.db.session import async_session_factory
from app.pipeline.run import run_pipeline_for_payment_case


@pytest.mark.anyio
async def test_conflicting_signal_reasoning_prompt_direct():
    res = await evaluate_conflicting_signals(
        classified_root_cause="insufficient_balance",
        naive_rule_suggestion="delayed_retry_notify",
        relevant_case_history="Customer has 18 consecutive months of flawless on-time subscription payments. This is their very first failure.",
    )
    assert res.recommended_intervention in ("silent_retry", "delayed_retry_notify", "escalate_human", "alternate_method")
    assert isinstance(res.agrees_with_default, bool)
    assert len(res.reasoning) > 10


@pytest.mark.anyio
async def test_module_a_pipeline_with_conflicting_signals():
    async with async_session_factory() as db:
        batch = Batch(
            label=f"Test Batch Conflicting Signal {uuid.uuid4().hex[:6]}",
            description="Testing Gemini conflicting-signal reasoning in Module A pipeline",
        )
        db.add(batch)
        await db.flush()

        case = PaymentCase(
            batch_id=batch.id,
            razorpay_payment_id=f"pay_cs_{uuid.uuid4().hex[:8]}",
            method=PaymentMethod.CARD,
            context=PaymentContext.SUBSCRIPTION,
            amount_paise=299900,
            failure_code="51",  # Insufficient funds
            failure_raw_reason="Declined: Insufficient funds in account",
            attempt_number=1,
            retry_count=0,
            status=PaymentCaseStatus.OPEN,
        )
        db.add(case)
        await db.commit()
        case_id = case.id

    history_text = "Customer has 18 consecutive months of on-time subscription payments. This is their very first failure, and salary credit is scheduled tomorrow."

    async with async_session_factory() as db:
        final_state = await run_pipeline_for_payment_case(case_id, db, case_history=history_text)

    assert final_state["module"] == "A"
    assert final_state["fault_attribution"] == "customer_fault"
    assert final_state["classified_root_cause"] == "insufficient_credit_limit"
    assert final_state["ai_reasoning"] is not None
    assert final_state["rule_recommendation"] == "delayed_retry_notify"
    assert final_state["final_decision"] in ("delayed_retry_notify", "silent_retry", "alternate_method")
    assert final_state["audit_entry_id"] is not None

    # Query audit_log to verify rule_suggested_action and ai_reasoning_text
    async with async_session_factory() as db:
        audit_res = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == final_state["audit_entry_id"])
        )
        audit_entry = audit_res.scalar_one()
        assert audit_entry.rule_suggested_action == "delayed_retry_notify"
        assert audit_entry.ai_reasoning_text is not None
