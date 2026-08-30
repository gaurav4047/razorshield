import uuid
import pytest
from sqlalchemy import select
from app.db.models.audit_log import AuditLogEntry, CaseType
from app.db.models.batch import Batch
from app.db.models.payment_case import (
    PaymentCase,
    PaymentCaseStatus,
    PaymentContext,
    PaymentMethod,
)
from app.db.session import async_session_factory
from app.pipeline.run import run_pipeline_for_payment_case


@pytest.mark.anyio
async def test_module_a_pipeline_deterministic_path():
    # 1. Test case with direct lookup match in payment_taxonomy: NO AI call should occur
    async with async_session_factory() as db:
        batch = Batch(
            label=f"Test Batch Module A Deterministic {uuid.uuid4().hex[:6]}",
            description="Testing deterministic path without LLM call",
        )
        db.add(batch)
        await db.flush()

        case = PaymentCase(
            batch_id=batch.id,
            razorpay_payment_id=f"pay_det_{uuid.uuid4().hex[:8]}",
            method=PaymentMethod.CARD,
            context=PaymentContext.SUBSCRIPTION,
            amount_paise=100000,
            failure_code="54",  # Standard ISO 8583 decline code for expired card
            failure_raw_reason="Card expired or validity lapsed",
            attempt_number=1,
            retry_count=0,
            status=PaymentCaseStatus.OPEN,
        )
        db.add(case)
        await db.commit()
        case_id = case.id

    async with async_session_factory() as db:
        final_state = await run_pipeline_for_payment_case(case_id, db)

    # Assertions on pipeline state
    assert final_state["module"] == "A"
    assert final_state["fault_attribution"] == "customer_fault"
    assert final_state["classified_root_cause"] == "card_expired"
    # Crucial proof: ai_reasoning is None because no AI call was made
    assert final_state["ai_reasoning"] is None
    assert final_state["diagnosis_confidence"] == 1.0
    assert final_state["recommended_intervention"] == "alternate_method"
    assert final_state["final_decision"] == "alternate_method"
    assert final_state["policy_passed"] is True
    assert final_state["audit_entry_id"] is not None

    # Assertions on database audit_log row
    async with async_session_factory() as db:
        audit_res = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == final_state["audit_entry_id"])
        )
        audit_row = audit_res.scalar_one_or_none()
        assert audit_row is not None
        assert audit_row.case_type == CaseType.PAYMENT_CASE
        assert audit_row.case_id == case_id
        # Explicit proof: ai_reasoning_text in DB is NULL
        assert audit_row.ai_reasoning_text is None
        assert audit_row.final_action == "alternate_method"
        assert len(audit_row.stopping_rules_checked) >= 3


@pytest.mark.anyio
async def test_module_a_pipeline_groq_signal_parsing_fallback():
    # 2. Test case with unclassified failure reason requiring real Groq LLM parsing
    async with async_session_factory() as db:
        batch = Batch(
            label=f"Test Batch Module A Groq {uuid.uuid4().hex[:6]}",
            description="Testing Groq signal parsing fallback",
        )
        db.add(batch)
        await db.flush()

        case = PaymentCase(
            batch_id=batch.id,
            razorpay_payment_id=f"pay_groq_{uuid.uuid4().hex[:8]}",
            method=PaymentMethod.UPI,
            context=PaymentContext.SUBSCRIPTION,
            amount_paise=250000,
            failure_code=None,  # No standard failure code
            failure_raw_reason="Transaction declined due to unexpected upstream timeout at remitter bank CBS server",
            attempt_number=1,
            retry_count=0,
            status=PaymentCaseStatus.OPEN,
        )
        db.add(case)
        await db.commit()
        case_id = case.id

    async with async_session_factory() as db:
        final_state = await run_pipeline_for_payment_case(case_id, db)

    # Verify real Groq signal parsing occurred
    assert final_state["module"] == "A"
    assert final_state["fault_attribution"] in ("infrastructure_fault", "customer_fault")
    assert final_state["classified_root_cause"] is not None
    # Crucial proof: ai_reasoning is populated with real LLM reasoning text
    assert final_state["ai_reasoning"] is not None
    assert len(final_state["ai_reasoning"]) > 10
    assert final_state["diagnosis_confidence"] is not None
    assert final_state["audit_entry_id"] is not None

    # Verify audit_log row in database
    async with async_session_factory() as db:
        audit_res = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == final_state["audit_entry_id"])
        )
        audit_row = audit_res.scalar_one_or_none()
        assert audit_row is not None
        assert audit_row.case_id == case_id
        # Explicit proof: real Groq reasoning text persisted in audit_log
        assert audit_row.ai_reasoning_text is not None
        assert len(audit_row.ai_reasoning_text) > 10
        assert len(audit_row.stopping_rules_checked) >= 3


@pytest.mark.anyio
async def test_module_a_confidence_threshold_gate():
    # 3. Test low confidence classification routes directly to escalate_human
    from app.pipeline.nodes.diagnose import diagnose_node
    from unittest.mock import AsyncMock, patch
    from app.ai_layer.output_schemas import SignalParsingOutput

    # Simulate low-confidence (0.45 < 0.70 threshold) model output
    mock_low_conf_output = SignalParsingOutput(
        classified_root_cause="CARD_INSUFFICIENT_FUNDS",
        fault_attribution="customer_fault",
        confidence=0.45,
        brief_reasoning="Ambiguous error message with low confidence.",
    )

    state = {
        "module": "A",
        "method": "card",
        "context": "subscription",
        "failure_code": None,
        "failure_raw_reason": "Vague intermittent gateway disruption with no clear pattern",
    }

    with patch("app.pipeline.nodes.diagnose.parse_failure_signal", new=AsyncMock(return_value=mock_low_conf_output)):
        result = await diagnose_node(state)
        # Even though root cause was CARD_INSUFFICIENT_FUNDS, low confidence forced escalate_human
        assert result["recommended_intervention"] == "escalate_human"
        assert result["diagnosis_confidence"] == 0.45
