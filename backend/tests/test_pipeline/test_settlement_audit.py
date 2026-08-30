import uuid
from datetime import date, timedelta
import pytest
from sqlalchemy import select
from app.db.models.audit_log import AuditLogEntry, CaseType
from app.db.models.batch import Batch
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus, PaymentContext, PaymentMethod
from app.db.session import async_session_factory
from app.pipeline.nodes.audit import audit_node
from app.pipeline.run import run_pipeline_for_invoice, run_pipeline_for_order


@pytest.mark.anyio
async def test_confirmed_recovery_audit_log_has_exact_settlement_breakdown():
    # Test confirmed recovery on an invoice for Rs 1,00,000 (10,000,000 paise)
    gross_paise = 10000000  # Rs 1,00,000
    expected_mdr = round(gross_paise * 0.02)  # 2% standard platform fee = 200,000 paise (Rs 2,000)
    expected_gst = round(expected_mdr * 0.18)  # 18% GST on MDR = 36,000 paise (Rs 360)
    expected_net = gross_paise - expected_mdr - expected_gst  # 9,764,000 paise (Rs 97,640)

    async with async_session_factory() as db:
        batch = Batch(
            label=f"Test Batch Settlement Recovery {uuid.uuid4().hex[:6]}",
            description="Testing gross-vs-net settlement breakdown on confirmed recovery",
        )
        db.add(batch)
        await db.flush()

        invoice = Invoice(
            batch_id=batch.id,
            invoice_number=f"INV-REC-{uuid.uuid4().hex[:6]}",
            buyer_name="Zenith Infra Ltd",
            buyer_contact="+919876543230",
            buyer_email="billing@zenithinfra.com",
            supplier_is_msme=True,
            has_written_agreement=True,
            amount_paise=gross_paise,
            invoice_date=date.today() - timedelta(days=40),
            goods_accepted_date=date.today() - timedelta(days=40),
            statutory_due_date=date.today() - timedelta(days=10),
            current_rung=2,
            status=InvoiceStatus.OVERDUE,
            buyer_archetype="enterprise",
        )
        db.add(invoice)
        await db.commit()
        invoice_id = invoice.id
        batch_id = batch.id

    # Simulate confirmed recovery through audit_node
    recovery_state = {
        "module": "B",
        "case_id": str(invoice_id),
        "batch_id": str(batch_id),
        "order_amount_paise": gross_paise,
        "method": "netbanking",
        "final_decision": "recovered",
        "reason": "Payment confirmed via Razorpay webhook payment.captured",
        "razorpay_reference_id": "pay_test_settlement_123",
        "stopping_rules_checked": [
            {"rule": "settlement_calculation", "passed": True, "detail": "Gross-vs-net MDR & GST computed"}
        ],
    }

    audit_result = await audit_node(recovery_state)
    audit_entry_id = audit_result["audit_entry_id"]

    # Verify audit_log row in Neon DB
    async with async_session_factory() as db:
        audit_res = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.id == audit_entry_id)
        )
        audit_row = audit_res.scalar_one_or_none()

        assert audit_row is not None
        assert audit_row.final_action == "recovered"
        # Verify gross, MDR, GST, and net are all populated
        assert audit_row.gross_amount_paise == gross_paise
        assert audit_row.mdr_paise == expected_mdr
        assert audit_row.gst_on_mdr_paise == expected_gst
        assert audit_row.net_amount_paise == expected_net
        # Verify mathematical identity: gross = net + mdr + gst
        assert audit_row.net_amount_paise + audit_row.mdr_paise + audit_row.gst_on_mdr_paise == audit_row.gross_amount_paise
