from datetime import date, timedelta
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select
from app.ai_layer.prompts.message_drafting import draft_reminder_message
from app.config import settings
from app.db.models.audit_log import AuditLogEntry, CaseType
from app.db.models.batch import Batch
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.session import async_session_factory
from app.domain_logic.msmed import compute_accrued_interest
from app.pipeline.run import run_pipeline_for_invoice


@pytest.mark.anyio
async def test_module_b_deterministic_rung_advancement():
    # 1. Test deterministic rung advancement with zero AI calls
    today = date.today()
    due_date = today - timedelta(days=3)  # 3 days overdue -> Rung 1

    async with async_session_factory() as db:
        batch = Batch(
            label=f"Test Batch Module B Rung 1 {uuid.uuid4().hex[:6]}",
            description="Testing deterministic rung 1 advancement",
        )
        db.add(batch)
        await db.flush()

        invoice = Invoice(
            batch_id=batch.id,
            invoice_number=f"INV-TEST-{uuid.uuid4().hex[:6]}",
            buyer_name="Alpha Tech Pvt Ltd",
            buyer_contact="+919876543220",
            buyer_email="accounts@alphatech.com",
            supplier_is_msme=True,
            has_written_agreement=True,
            amount_paise=10000000,  # Rs 1,00,000
            invoice_date=due_date - timedelta(days=30),
            goods_accepted_date=due_date - timedelta(days=30),
            statutory_due_date=due_date,
            current_rung=0,
            status=InvoiceStatus.PENDING,
            buyer_archetype="standard_b2b",
        )
        db.add(invoice)
        await db.commit()
        invoice_id = invoice.id

    async with async_session_factory() as db:
        final_state = await run_pipeline_for_invoice(invoice_id, db)

    assert final_state["module"] == "B"
    assert final_state["current_rung"] == 1
    assert final_state["final_decision"] == "rung_1_action"
    assert final_state["policy_passed"] is True
    assert final_state["ai_reasoning"] is None
    assert final_state["audit_entry_id"] is not None

    async with async_session_factory() as db:
        audit_res = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == final_state["audit_entry_id"])
        )
        audit_row = audit_res.scalar_one_or_none()
        assert audit_row is not None
        assert audit_row.case_type == CaseType.INVOICE
        assert audit_row.case_id == invoice_id
        assert audit_row.ai_reasoning_text is None
        assert audit_row.final_action == "rung_1_action"
        assert len(audit_row.stopping_rules_checked) >= 3


@pytest.mark.anyio
async def test_module_b_msmed_interest_citation_at_rung_2():
    # 2. Test exact MSMED interest calculation and citation at Rung 2 (+10 days overdue)
    today = date.today()
    due_date = today - timedelta(days=10)
    principal_paise = 10000000  # Rs 1,00,000

    async with async_session_factory() as db:
        batch = Batch(
            label=f"Test Batch Module B Interest {uuid.uuid4().hex[:6]}",
            description="Testing MSMED interest citation at rung 2",
        )
        db.add(batch)
        await db.flush()

        invoice = Invoice(
            batch_id=batch.id,
            invoice_number="INV-2026-MSME-001",
            buyer_name="Beta Manufacturing Ltd",
            buyer_contact="+919876543221",
            buyer_email="finance@betamfg.com",
            supplier_is_msme=True,
            has_written_agreement=True,
            amount_paise=principal_paise,
            invoice_date=due_date - timedelta(days=30),
            goods_accepted_date=due_date - timedelta(days=30),
            statutory_due_date=due_date,
            current_rung=1,
            status=InvoiceStatus.OVERDUE,
            buyer_archetype="slow_payer",
        )
        db.add(invoice)
        await db.commit()
        invoice_id = invoice.id

    async with async_session_factory() as db:
        final_state = await run_pipeline_for_invoice(invoice_id, db, supplier_is_msme=True)

    # Assert rung advanced to 2
    assert final_state["current_rung"] == 2
    assert final_state["final_decision"] == "rung_2_action"

    # Compute expected statutory interest per MSMED formula (RBI rate 5.50%)
    expected_interest_paise = compute_accrued_interest(
        amount_paise=principal_paise,
        statutory_due_date=due_date,
        as_of_date=today,
        rbi_bank_rate=Decimal("5.50"),
    )
    assert final_state["computed_interest_paise"] == expected_interest_paise

    # Draft reminder message and verify exact numerical citation
    drafted_msg = draft_reminder_message(
        invoice_number="INV-2026-MSME-001",
        buyer_name="Beta Manufacturing Ltd",
        amount_paise=principal_paise,
        days_overdue=10,
        current_rung=2,
        computed_interest_paise=expected_interest_paise,
        supplier_is_msme=True,
    )
    expected_interest_inr_str = f"Rs {expected_interest_paise / 100:,.2f}"
    assert expected_interest_inr_str in drafted_msg
    assert "Section 16 of the MSMED Act 2006" in drafted_msg


@pytest.mark.anyio
async def test_module_b_dispute_halt_override_and_subsequent_tick():
    # 3. Simulate buyer dispute reply -> sets dispute_flag=True, halts communication on subsequent check
    today = date.today()
    due_date = today - timedelta(days=12)

    async with async_session_factory() as db:
        batch = Batch(label="Test Dispute Halt Override")
        db.add(batch)
        await db.flush()

        invoice = Invoice(
            batch_id=batch.id,
            invoice_number=f"INV-DISPUTE-{uuid.uuid4().hex[:6]}",
            buyer_name="Gamma Retailers",
            buyer_contact="+919876543222",
            buyer_email="ops@gammaretail.com",
            supplier_is_msme=True,
            has_written_agreement=True,
            amount_paise=5000000,
            invoice_date=due_date - timedelta(days=30),
            goods_accepted_date=due_date - timedelta(days=30),
            statutory_due_date=due_date,
            current_rung=1,
            dispute_flag=False,
            status=InvoiceStatus.OVERDUE,
            buyer_archetype="disputed_account",
        )
        db.add(invoice)
        await db.commit()
        invoice_id = invoice.id

    # Tick 1: Process incoming buyer reply contesting the invoice
    dispute_reply = "We dispute this invoice amount. 25% of the delivered units were defective and rejected."
    async with async_session_factory() as db:
        state_tick_1 = await run_pipeline_for_invoice(invoice_id, db, buyer_reply=dispute_reply)

    assert state_tick_1["dispute_flag"] is True
    assert state_tick_1["final_decision"] == "blocked_dispute_halt"
    assert state_tick_1["policy_passed"] is False

    # Verify DB invoice updated to DISPUTED and dispute_flag=True
    async with async_session_factory() as db:
        inv_res = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
        saved_inv = inv_res.scalar_one_or_none()
        assert saved_inv.dispute_flag is True
        assert saved_inv.status == InvoiceStatus.DISPUTED

    # Tick 2: Subsequent scheduled check (no buyer reply, normal scheduler tick)
    async with async_session_factory() as db:
        state_tick_2 = await run_pipeline_for_invoice(invoice_id, db, buyer_reply=None)

    assert state_tick_2["dispute_flag"] is True
    assert state_tick_2["policy_passed"] is False
    assert state_tick_2["final_decision"] == "blocked_dispute_halt"

    # Verify audit_log row proves the halt occurred on the subsequent tick
    async with async_session_factory() as db:
        audit_res = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == state_tick_2["audit_entry_id"])
        )
        audit_row = audit_res.scalar_one_or_none()
        assert audit_row is not None
        assert audit_row.final_action == "blocked_dispute_halt"
        assert audit_row.stopping_rules_checked[0]["rule"] == "dispute_halt"
        assert audit_row.stopping_rules_checked[0]["passed"] is False


@pytest.mark.anyio
async def test_module_b_reply_classification_confidence_fail_toward_caution():
    # 4. Test low confidence dispute-leaning classification fails toward caution (halts communication)
    from app.pipeline.nodes.diagnose import diagnose_node
    from unittest.mock import AsyncMock, patch
    from app.ai_layer.output_schemas import ReplyClassificationOutput

    mock_low_conf_dispute = ReplyClassificationOutput(
        classified_as="unclear",
        confidence=0.45,
        brief_reasoning="Buyer message has subtle dispute regarding quality of goods.",
    )

    state = {
        "module": "B",
        "statutory_due_date": date.today().isoformat(),
        "current_rung": 1,
        "dispute_flag": False,
        "broken_promise_count": 0,
        "supplier_is_msme": True,
        "order_amount_paise": 1000000,
        "buyer_response_text": "Not sure if we should pay, need to recheck items delivered.",
    }

    with patch("app.pipeline.nodes.diagnose.classify_buyer_reply", new=AsyncMock(return_value=mock_low_conf_dispute)):
        result = await diagnose_node(state)
        # Even with low confidence, dispute-leaning content forces halt_dispute_active
        assert result["dispute_flag"] is True
        assert result["recommended_intervention"] == "halt_dispute_active"
