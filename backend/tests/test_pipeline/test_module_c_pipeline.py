import uuid
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import select
from app.db.models.audit_log import AuditLogEntry, CaseType, PipelineStage
from app.db.models.batch import Batch
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.session import async_session_factory
from app.pipeline.run import run_pipeline_for_order


@pytest.mark.anyio
async def test_module_c_pipeline_eligible_order_success():
    async with async_session_factory() as db:
        # 1. Create a test batch
        batch = Batch(
            label=f"Test Batch Module C {uuid.uuid4().hex[:6]}",
            description="Testing Module C LangGraph Pipeline",
        )
        db.add(batch)
        await db.flush()

        # 2. Create an eligible abandoned order (> Rs 200, created 45 mins ago, nudge_sent=False)
        order_created = datetime.now(timezone.utc) - timedelta(minutes=45)
        order = AbandonedOrder(
            batch_id=batch.id,
            razorpay_order_id=f"order_test_{uuid.uuid4().hex[:8]}",
            customer_name="Rohan Sharma",
            customer_contact="+919876543210",
            customer_email="rohan@example.com",
            amount_paise=50000,  # Rs 500
            order_created_at=order_created,
            abandonment_detected_at=datetime.now(timezone.utc),
            nudge_sent=False,
            status=AbandonedOrderStatus.OPEN,
        )
        db.add(order)
        await db.commit()
        order_id = order.id
        batch_id = batch.id

    # 3. Run the LangGraph pipeline
    async with async_session_factory() as db:
        final_state = await run_pipeline_for_order(order_id, db)

    # 4. Verify pipeline output state
    assert final_state["module"] == "C"
    assert final_state["final_decision"] == "send_abandonment_nudge"
    assert final_state["policy_passed"] is True
    assert final_state["execution_result"] == "abandonment_nudge_dispatched"
    assert final_state["razorpay_reference_id"] is not None
    assert final_state["audit_entry_id"] is not None

    # 5. Verify stopping rules checked is non-empty and contains all expected rules
    stopping_rules = final_state["stopping_rules_checked"]
    assert isinstance(stopping_rules, list)
    assert len(stopping_rules) == 3
    rule_names = [r["rule"] for r in stopping_rules]
    assert "low_value_floor" in rule_names
    assert "single_nudge_cap" in rule_names
    assert "policy_gate_is_final" in rule_names
    assert all(r["passed"] is True for r in stopping_rules)

    # 6. Verify database audit_log row was written
    async with async_session_factory() as db:
        audit_res = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == final_state["audit_entry_id"])
        )
        audit_row = audit_res.scalar_one_or_none()
        assert audit_row is not None
        assert audit_row.case_type == CaseType.ABANDONED_ORDER
        assert audit_row.case_id == order_id
        assert audit_row.batch_id == batch_id
        assert audit_row.final_action == "send_abandonment_nudge"
        assert audit_row.gross_amount_paise == 50000
        assert audit_row.stopping_rules_checked == stopping_rules

        # 7. Verify order updated in DB
        order_res = await db.execute(select(AbandonedOrder).where(AbandonedOrder.id == order_id))
        updated_order = order_res.scalar_one_or_none()
        assert updated_order.nudge_sent is True
        assert updated_order.nudge_sent_at is not None
        assert updated_order.status == AbandonedOrderStatus.NUDGED
        assert updated_order.razorpay_payment_link_id is not None


@pytest.mark.anyio
async def test_module_c_pipeline_low_value_blocked_and_unconditionally_audited():
    # Proves that when policy_gate blocks an order, EXECUTE is skipped, but AUDIT still runs
    async with async_session_factory() as db:
        batch = Batch(
            label=f"Test Batch Low Value {uuid.uuid4().hex[:6]}",
            description="Testing Low Value Policy Gate Block",
        )
        db.add(batch)
        await db.flush()

        # Low value order: Rs 150 (15,000 paise < 20,000 paise floor)
        order_created = datetime.now(timezone.utc) - timedelta(minutes=45)
        order = AbandonedOrder(
            batch_id=batch.id,
            razorpay_order_id=f"order_low_{uuid.uuid4().hex[:8]}",
            customer_name="Aakash Verma",
            customer_contact="+919876543211",
            customer_email="aakash@example.com",
            amount_paise=15000,  # Rs 150
            order_created_at=order_created,
            nudge_sent=False,
            status=AbandonedOrderStatus.OPEN,
        )
        db.add(order)
        await db.commit()
        order_id = order.id

    # Run the pipeline
    async with async_session_factory() as db:
        final_state = await run_pipeline_for_order(order_id, db)

    # Verify policy gate blocked and execute was skipped
    assert final_state["policy_passed"] is False
    assert final_state["final_decision"] == "skipped_low_value"
    assert final_state.get("execution_result") is None
    assert final_state.get("razorpay_reference_id") is None
    assert final_state["audit_entry_id"] is not None

    # Verify audit_log row STILL landed in database despite execute being skipped
    async with async_session_factory() as db:
        audit_res = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == final_state["audit_entry_id"])
        )
        audit_row = audit_res.scalar_one_or_none()
        assert audit_row is not None
        assert audit_row.final_action == "skipped_low_value"
        assert audit_row.stopping_rules_checked[0]["rule"] == "low_value_floor"
        assert audit_row.stopping_rules_checked[0]["passed"] is False


@pytest.mark.anyio
async def test_module_c_pipeline_single_nudge_cap_blocked():
    async with async_session_factory() as db:
        batch = Batch(label="Test Single Nudge Cap")
        db.add(batch)
        await db.flush()

        order_created = datetime.now(timezone.utc) - timedelta(minutes=60)
        order = AbandonedOrder(
            batch_id=batch.id,
            razorpay_order_id=f"order_nudged_{uuid.uuid4().hex[:8]}",
            customer_name="Pooja Patel",
            customer_contact="+919876543212",
            customer_email="pooja@example.com",
            amount_paise=60000,
            order_created_at=order_created,
            nudge_sent=True,  # Already sent!
            nudge_sent_at=datetime.now(timezone.utc) - timedelta(minutes=20),
            status=AbandonedOrderStatus.NUDGED,
        )
        db.add(order)
        await db.commit()
        order_id = order.id

    async with async_session_factory() as db:
        final_state = await run_pipeline_for_order(order_id, db)

    assert final_state["policy_passed"] is False
    assert final_state["final_decision"] == "blocked_single_nudge_cap"
    assert final_state["audit_entry_id"] is not None

    async with async_session_factory() as db:
        audit_res = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == final_state["audit_entry_id"])
        )
        audit_row = audit_res.scalar_one_or_none()
        assert audit_row.final_action == "blocked_single_nudge_cap"
