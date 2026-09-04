import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.audit_log import AuditLogEntry, CaseType, PipelineStage
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus, PaymentMethod
from app.db.models.webhook_event import RawWebhookEvent
from app.db.session import get_db
from app.domain_logic.settlement import compute_settlement
from app.razorpay_client.webhook_verify import verify_webhook_signature

router = APIRouter()


async def process_webhook_recovery(payload: dict, db: AsyncSession) -> dict | None:
    event_type = payload.get("event", "")
    payload_data = payload.get("payload", {})

    # Extract payment, payment_link, or order entity
    payment_entity = payload_data.get("payment", {}).get("entity", {})
    plink_entity = payload_data.get("payment_link", {}).get("entity", {})
    order_entity = payload_data.get("order", {}).get("entity", {})

    plink_id = plink_entity.get("id") or payment_entity.get("payment_link_id")
    order_id = order_entity.get("id") or payment_entity.get("order_id")
    payment_id = payment_entity.get("id") or f"pay_{uuid.uuid4().hex[:12]}"
    ref_id = plink_entity.get("reference_id") or order_entity.get("receipt")
    notes = plink_entity.get("notes", {}) or payment_entity.get("notes", {}) or order_entity.get("notes", {})

    case_id_note = notes.get("case_id") or notes.get("invoice_id") or notes.get("order_id")

    # Determine method & gross amount
    method_str = payment_entity.get("method", "card")
    method_enum = PaymentMethod(method_str) if method_str in PaymentMethod._value2member_map_ else PaymentMethod.CARD
    gross_amount = payment_entity.get("amount") or plink_entity.get("amount") or order_entity.get("amount") or 0

    now_utc = datetime.now(timezone.utc)

    # 1. Try matching Module A (PaymentCase)
    payment_case = None
    if case_id_note:
        try:
            pc_uuid = uuid.UUID(str(case_id_note))
            pc_res = await db.execute(select(PaymentCase).where(PaymentCase.id == pc_uuid))
            payment_case = pc_res.scalar_one_or_none()
        except Exception:
            pass

    if not payment_case and plink_id:
        pc_res = await db.execute(select(PaymentCase).where(PaymentCase.razorpay_payment_link_id == plink_id))
        payment_case = pc_res.scalar_one_or_none()

    if not payment_case and payment_id:
        pc_res = await db.execute(select(PaymentCase).where(PaymentCase.razorpay_payment_id == payment_id))
        payment_case = pc_res.scalar_one_or_none()

    if payment_case:
        payment_case.status = PaymentCaseStatus.RECOVERED
        payment_case.last_action_at = now_utc
        if not gross_amount:
            gross_amount = payment_case.amount_paise

        settlement = compute_settlement(gross_amount_paise=gross_amount, method=method_enum)

        audit_entry = AuditLogEntry(
            batch_id=payment_case.batch_id,
            case_type=CaseType.PAYMENT_CASE,
            case_id=payment_case.id,
            stage=PipelineStage.AUDIT,
            rule_suggested_action="recovered",
            final_action="recovered",
            reason=f"Recovery confirmed via Razorpay webhook {event_type}",
            gross_amount_paise=gross_amount,
            mdr_paise=settlement.mdr_paise,
            gst_on_mdr_paise=settlement.gst_on_mdr_paise,
            net_amount_paise=settlement.net_amount_paise,
            razorpay_reference=payment_id,
            stopping_rules_checked=[
                {"rule": "policy_gate_is_final", "passed": True, "detail": "Webhook payment recovery confirmed and settled"}
            ],
        )
        db.add(audit_entry)
        await db.flush()
        try:
            from app.api.routes.audit import audit_manager, serialize_audit_entry
            meta = {
                "counterparty_name": f"{payment_case.method.value.upper()} Mandate",
                "case_reference": payment_case.razorpay_payment_id,
            }
            await audit_manager.broadcast(serialize_audit_entry(audit_entry, meta))
        except Exception:
            pass
        return {"module": "A", "case_id": str(payment_case.id), "status": "recovered"}

    # 2. Try matching Module B (Invoice)
    invoice = None
    if case_id_note:
        try:
            inv_uuid = uuid.UUID(str(case_id_note))
            inv_res = await db.execute(select(Invoice).where(Invoice.id == inv_uuid))
            invoice = inv_res.scalar_one_or_none()
        except Exception:
            pass

    if not invoice and ref_id:
        inv_res = await db.execute(select(Invoice).where(Invoice.invoice_number == ref_id))
        invoice = inv_res.scalar_one_or_none()

    if not invoice and plink_id:
        inv_res = await db.execute(select(Invoice).where(Invoice.razorpay_payment_link_id == plink_id))
        invoice = inv_res.scalar_one_or_none()

    if invoice:
        invoice.status = InvoiceStatus.PAID
        invoice.amount_paid_paise = gross_amount or invoice.amount_paise
        if not gross_amount:
            gross_amount = invoice.amount_paise

        settlement = compute_settlement(gross_amount_paise=gross_amount, method=method_enum)

        audit_entry = AuditLogEntry(
            batch_id=invoice.batch_id,
            case_type=CaseType.INVOICE,
            case_id=invoice.id,
            stage=PipelineStage.AUDIT,
            rule_suggested_action="recovered",
            final_action="recovered",
            reason=f"Invoice payment confirmed via Razorpay webhook {event_type}",
            gross_amount_paise=gross_amount,
            mdr_paise=settlement.mdr_paise,
            gst_on_mdr_paise=settlement.gst_on_mdr_paise,
            net_amount_paise=settlement.net_amount_paise,
            razorpay_reference=payment_id or plink_id,
            stopping_rules_checked=[
                {"rule": "policy_gate_is_final", "passed": True, "detail": "Webhook payment recovery confirmed and settled"}
            ],
        )
        db.add(audit_entry)
        await db.flush()
        try:
            from app.api.routes.audit import audit_manager, serialize_audit_entry
            meta = {
                "counterparty_name": invoice.buyer_name,
                "case_reference": invoice.invoice_number,
            }
            await audit_manager.broadcast(serialize_audit_entry(audit_entry, meta))
        except Exception:
            pass
        return {"module": "B", "case_id": str(invoice.id), "status": "recovered"}

    # 3. Try matching Module C (AbandonedOrder)
    order = None
    if case_id_note:
        try:
            ord_uuid = uuid.UUID(str(case_id_note))
            ord_res = await db.execute(select(AbandonedOrder).where(AbandonedOrder.id == ord_uuid))
            order = ord_res.scalar_one_or_none()
        except Exception:
            pass

    if not order and order_id:
        ord_res = await db.execute(select(AbandonedOrder).where(AbandonedOrder.razorpay_order_id == order_id))
        order = ord_res.scalar_one_or_none()

    if not order and plink_id:
        ord_res = await db.execute(select(AbandonedOrder).where(AbandonedOrder.razorpay_payment_link_id == plink_id))
        order = ord_res.scalar_one_or_none()

    if order:
        order.status = AbandonedOrderStatus.RECOVERED
        if not gross_amount:
            gross_amount = order.amount_paise

        settlement = compute_settlement(gross_amount_paise=gross_amount, method=method_enum)

        audit_entry = AuditLogEntry(
            batch_id=order.batch_id,
            case_type=CaseType.ABANDONED_ORDER,
            case_id=order.id,
            stage=PipelineStage.AUDIT,
            rule_suggested_action="recovered",
            final_action="recovered",
            reason=f"Abandoned order recovered via Razorpay webhook {event_type}",
            gross_amount_paise=gross_amount,
            mdr_paise=settlement.mdr_paise,
            gst_on_mdr_paise=settlement.gst_on_mdr_paise,
            net_amount_paise=settlement.net_amount_paise,
            razorpay_reference=payment_id or order_id,
            stopping_rules_checked=[
                {"rule": "policy_gate_is_final", "passed": True, "detail": "Webhook payment recovery confirmed and settled"}
            ],
        )
        db.add(audit_entry)
        await db.flush()
        try:
            from app.api.routes.audit import audit_manager, serialize_audit_entry
            meta = {
                "counterparty_name": order.customer_name,
                "case_reference": order.razorpay_order_id,
            }
            await audit_manager.broadcast(serialize_audit_entry(audit_entry, meta))
        except Exception:
            pass
        return {"module": "C", "case_id": str(order.id), "status": "recovered"}

    return None


@router.post("/razorpay", status_code=status.HTTP_200_OK)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: str | None = Header(None, alias="X-Razorpay-Event-Id"),
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty webhook body",
        )

    # 1. Signature Verification: Reject immediately on invalid/missing signature before any json.loads()
    if not x_razorpay_signature or not settings.RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature or secret configuration",
        )

    if not verify_webhook_signature(
        raw_body=raw_body,
        received_signature=x_razorpay_signature,
        webhook_secret=settings.RAZORPAY_WEBHOOK_SECRET,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # 2. JSON Parsing: Executed strictly after successful signature verification
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(exc)}",
        )

    # 3. Event Identification: Use X-Razorpay-Event-Id header (unique per delivery)
    event_id = x_razorpay_event_id or payload.get("event_id") or payload.get("id")
    event_type = payload.get("event", "unknown")

    # 4. Idempotency Check: Return 200 OK without re-inserting if this specific delivery was already processed
    if event_id:
        existing = await db.execute(
            select(RawWebhookEvent).where(RawWebhookEvent.razorpay_event_id == event_id)
        )
        if existing.scalar_one_or_none():
            return {
                "status": "already_received",
                "event_id": event_id,
                "event_type": event_type,
            }

    # 5. Process state transitions on confirmed payments
    recovery_info = None
    if event_type in ("payment.captured", "payment.authorized", "payment_link.paid", "order.paid"):
        recovery_info = await process_webhook_recovery(payload, db)

    # 6. Persistence: Record verified event in raw_webhook_events
    webhook_event = RawWebhookEvent(
        razorpay_event_id=event_id,
        event_type=event_type,
        payload=payload,
        signature_verified=True,
        processed=True if recovery_info else False,
    )
    db.add(webhook_event)
    await db.commit()
    await db.refresh(webhook_event)

    return {
        "status": "ok",
        "event_id": event_id,
        "event_type": event_type,
        "record_id": webhook_event.id,
        "recovery": recovery_info,
    }
