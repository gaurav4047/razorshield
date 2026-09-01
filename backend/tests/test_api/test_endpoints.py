import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.db.session import async_session_factory
from app.db.models.batch import Batch
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus, PaymentMethod, PaymentContext
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from datetime import date, datetime, timezone


@pytest.mark.anyio
async def test_api_endpoints_full_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health check
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        # 2. Seed test batch and cases
        async with async_session_factory() as db:
            batch = Batch(
                label=f"API Test Batch {uuid.uuid4().hex[:6]}",
                description="Testing all API endpoints",
            )
            db.add(batch)
            await db.flush()

            pc = PaymentCase(
                batch_id=batch.id,
                razorpay_payment_id=f"pay_api_{uuid.uuid4().hex[:8]}",
                method=PaymentMethod.UPI,
                context=PaymentContext.SUBSCRIPTION,
                amount_paise=50000,
                failure_code="U30",
                failure_raw_reason="UPI payment failed during testing",
                attempt_number=1,
                retry_count=0,
                status=PaymentCaseStatus.OPEN,
            )
            db.add(pc)

            inv = Invoice(
                batch_id=batch.id,
                invoice_number=f"INV-API-{uuid.uuid4().hex[:4]}",
                buyer_name="Acme Corp Ltd",
                buyer_contact="+919876543210",
                buyer_email="buyer@acme.com",
                buyer_archetype="cash_flow_constrained",
                supplier_is_msme=True,
                amount_paise=15000000,
                amount_paid_paise=0,
                invoice_date=date(2026, 1, 1),
                goods_accepted_date=date(2026, 1, 5),
                statutory_due_date=date(2026, 2, 19),
                status=InvoiceStatus.OVERDUE,
                current_rung=1,
                dispute_flag=False,
                broken_promise_count=0,
            )

            db.add(inv)

            order = AbandonedOrder(
                batch_id=batch.id,
                razorpay_order_id=f"order_api_{uuid.uuid4().hex[:8]}",
                customer_name="Test Customer",
                customer_contact="+919123456789",
                customer_email="cust@test.com",
                amount_paise=45000,
                order_created_at=datetime.now(timezone.utc),
                status=AbandonedOrderStatus.OPEN,
            )
            db.add(order)
            await db.commit()

            batch_id = batch.id
            pc_id = pc.id
            inv_id = inv.id
            order_id = order.id

        # 3. GET /api/batches
        resp = await client.get("/api/batches")
        assert resp.status_code == 200
        batches = resp.json()
        assert len(batches) >= 1
        assert any(b["id"] == str(batch_id) for b in batches)

        # 4. GET /api/batches/{id}/summary
        resp = await client.get(f"/api/batches/{batch_id}/summary")
        assert resp.status_code == 200
        summary = resp.json()
        assert summary["batch_id"] == str(batch_id)
        assert summary["total_cases"] == 3
        assert summary["total_at_risk_paise"] == 50000 + 15000000 + 45000
        assert "exceptions_breakdown" in summary

        # 5. GET /api/cases
        # Module A
        resp_a = await client.get(f"/api/cases?module=A&batch_id={batch_id}")
        assert resp_a.status_code == 200
        data_a = resp_a.json()
        assert data_a["count"] == 1
        assert data_a["cases"][0]["id"] == str(pc_id)
        assert data_a["cases"][0]["method"] == "upi"

        # Module B
        resp_b = await client.get(f"/api/cases?module=B&batch_id={batch_id}")
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["count"] == 1
        assert data_b["cases"][0]["id"] == str(inv_id)
        assert data_b["cases"][0]["supplier_is_msme"] is True
        assert data_b["cases"][0]["computed_interest_paise"] > 0

        # Module C
        resp_c = await client.get(f"/api/cases?module=C&batch_id={batch_id}")
        assert resp_c.status_code == 200
        data_c = resp_c.json()
        assert data_c["count"] == 1
        assert data_c["cases"][0]["id"] == str(order_id)

        # 6. GET /api/cases/{module}/{case_id} detail
        resp_detail = await client.get(f"/api/cases/B/{inv_id}")
        assert resp_detail.status_code == 200
        detail = resp_detail.json()
        assert detail["id"] == str(inv_id)
        assert detail["invoice_number"].startswith("INV-API-")
        assert "audit_logs" in detail
        assert "promises" in detail

        # 7. GET /api/audit
        resp_audit = await client.get(f"/api/audit?batch_id={batch_id}")
        assert resp_audit.status_code == 200
        audit_data = resp_audit.json()
        assert "audit_logs" in audit_data

        # 8. POST /api/cases/{module}/{case_id}/simulate-webhook
        resp_sim = await client.post(f"/api/cases/A/{pc_id}/simulate-webhook")
        assert resp_sim.status_code == 200
        sim_data = resp_sim.json()
        assert sim_data["status"] == "recovered"
        assert sim_data["case_id"] == str(pc_id)

