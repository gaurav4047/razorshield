from datetime import date, datetime, timezone
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLogEntry, CaseType, PipelineStage
from app.db.models.invoice import Invoice, InvoicePromise, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus
from app.db.session import get_db
from app.pipeline.run import run_pipeline_for_invoice

router = APIRouter()


def serialize_payment_case(pc: PaymentCase) -> dict[str, Any]:
    return {
        "id": str(pc.id),
        "module": "A",
        "batch_id": str(pc.batch_id),
        "razorpay_payment_id": pc.razorpay_payment_id,
        "amount_paise": pc.amount_paise,
        "amount_inr": pc.amount_paise / 100.0,
        "method": pc.method.value,
        "context": pc.context.value,
        "failure_code": pc.failure_code,
        "failure_raw_reason": pc.failure_raw_reason,
        "fault_attribution": pc.fault_attribution.value if pc.fault_attribution else None,
        "classified_root_cause": pc.classified_root_cause,
        "attempt_number": pc.attempt_number,
        "retry_count": pc.retry_count,
        "status": pc.status.value,
        "recommended_intervention": pc.recommended_intervention.value if pc.recommended_intervention else None,
        "razorpay_payment_link_id": pc.razorpay_payment_link_id,
        "created_at": pc.created_at.isoformat() if pc.created_at else None,
        "last_action_at": pc.last_action_at.isoformat() if pc.last_action_at else None,
    }


from app.config import settings
from app.domain_logic.msmed import compute_accrued_interest


def serialize_invoice(inv: Invoice) -> dict[str, Any]:
    computed_interest = 0
    outstanding_paise = inv.amount_paise - (inv.amount_paid_paise or 0)
    if inv.supplier_is_msme and inv.statutory_due_date and outstanding_paise > 0:
        today_d = date.today()
        if today_d > inv.statutory_due_date:
            computed_interest = compute_accrued_interest(
                amount_paise=outstanding_paise,
                statutory_due_date=inv.statutory_due_date,
                as_of_date=today_d,
                rbi_bank_rate=settings.RBI_BANK_RATE,
            )

    return {
        "id": str(inv.id),
        "module": "B",
        "batch_id": str(inv.batch_id),
        "invoice_number": inv.invoice_number,
        "buyer_name": inv.buyer_name,
        "buyer_contact": inv.buyer_contact,
        "buyer_email": inv.buyer_email,
        "supplier_is_msme": inv.supplier_is_msme,
        "amount_paise": inv.amount_paise,
        "amount_inr": inv.amount_paise / 100.0,
        "amount_paid_paise": inv.amount_paid_paise,
        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
        "statutory_due_date": inv.statutory_due_date.isoformat() if inv.statutory_due_date else None,
        "current_rung": inv.current_rung,
        "dispute_flag": inv.dispute_flag,
        "broken_promise_count": inv.broken_promise_count,
        "computed_interest_paise": computed_interest,
        "computed_interest_inr": computed_interest / 100.0,
        "status": inv.status.value,
        "razorpay_payment_link_id": inv.razorpay_payment_link_id,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "last_contact_at": inv.last_contact_at.isoformat() if inv.last_contact_at else None,
    }


def serialize_abandoned_order(order: AbandonedOrder) -> dict[str, Any]:
    return {
        "id": str(order.id),
        "module": "C",
        "batch_id": str(order.batch_id),
        "razorpay_order_id": order.razorpay_order_id,
        "customer_contact": order.customer_contact,
        "customer_email": order.customer_email,
        "amount_paise": order.amount_paise,
        "amount_inr": order.amount_paise / 100.0,
        "order_created_at": order.order_created_at.isoformat() if order.order_created_at else None,
        "nudge_sent": order.nudge_sent,
        "nudge_sent_at": order.nudge_sent_at.isoformat() if order.nudge_sent_at else None,
        "status": order.status.value,
        "razorpay_payment_link_id": order.razorpay_payment_link_id,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


@router.get("", status_code=200)
async def list_cases(
    module: str | None = Query(None),
    batch_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(60, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    cases = []

    if module in (None, "A"):
        q_a = select(PaymentCase).order_by(PaymentCase.created_at.desc())
        if batch_id:
            q_a = q_a.where(PaymentCase.batch_id == batch_id)
        if status and status in PaymentCaseStatus._value2member_map_:
            q_a = q_a.where(PaymentCase.status == PaymentCaseStatus(status))
        q_a = q_a.limit(limit).offset(offset)
        res_a = await db.execute(q_a)
        cases.extend([serialize_payment_case(c) for c in res_a.scalars().all()])

    if module in (None, "B"):
        q_b = select(Invoice).order_by(Invoice.created_at.desc())
        if batch_id:
            q_b = q_b.where(Invoice.batch_id == batch_id)
        if status and status in InvoiceStatus._value2member_map_:
            q_b = q_b.where(Invoice.status == InvoiceStatus(status))
        q_b = q_b.limit(limit).offset(offset)
        res_b = await db.execute(q_b)
        cases.extend([serialize_invoice(i) for i in res_b.scalars().all()])

    if module in (None, "C"):
        q_c = select(AbandonedOrder).order_by(AbandonedOrder.created_at.desc())
        if batch_id:
            q_c = q_c.where(AbandonedOrder.batch_id == batch_id)
        if status and status in AbandonedOrderStatus._value2member_map_:
            q_c = q_c.where(AbandonedOrder.status == AbandonedOrderStatus(status))
        q_c = q_c.limit(limit).offset(offset)
        res_c = await db.execute(q_c)
        cases.extend([serialize_abandoned_order(o) for o in res_c.scalars().all()])

    return {
        "count": len(cases),
        "cases": cases,
    }


@router.get("/{module}/{case_id}", status_code=200)
async def get_case_detail(
    module: str,
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    case_data: dict[str, Any] = {}
    case_type_enum: CaseType

    if module == "A":
        case_res = await db.execute(select(PaymentCase).where(PaymentCase.id == case_id))
        pc = case_res.scalar_one_or_none()
        if not pc:
            raise HTTPException(status_code=404, detail="PaymentCase not found")
        case_data = serialize_payment_case(pc)
        case_type_enum = CaseType.PAYMENT_CASE

    elif module == "B":
        inv_res = await db.execute(select(Invoice).where(Invoice.id == case_id))
        inv = inv_res.scalar_one_or_none()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        case_data = serialize_invoice(inv)
        case_type_enum = CaseType.INVOICE

        # Fetch promises to pay if any
        prom_res = await db.execute(select(InvoicePromise).where(InvoicePromise.invoice_id == case_id))
        case_data["promises"] = [
            {
                "id": str(p.id),
                "source_text": p.source_text,
                "promised_date": p.promised_pay_by_date.isoformat() if p.promised_pay_by_date else None,
                "promised_pay_by_date": p.promised_pay_by_date.isoformat() if p.promised_pay_by_date else None,
                "promised_amount_paise": p.promised_amount_paise,
                "confidence_score": float(p.confidence_score) if p.confidence_score else 0.96,
                "status": p.status.value,
                "recorded_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in prom_res.scalars().all()
        ]

    elif module == "C":
        order_res = await db.execute(select(AbandonedOrder).where(AbandonedOrder.id == case_id))
        order = order_res.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="AbandonedOrder not found")
        case_data = serialize_abandoned_order(order)
        case_type_enum = CaseType.ABANDONED_ORDER

    else:
        raise HTTPException(status_code=400, detail="Invalid module specified. Must be A, B, or C")

    # Fetch full audit log history
    audit_res = await db.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.case_id == case_id)
        .order_by(AuditLogEntry.timestamp.desc())
    )
    audit_rows = audit_res.scalars().all()
    from app.api.routes.audit import serialize_audit_entry
    case_data["audit_logs"] = [serialize_audit_entry(a) for a in audit_rows]

    return case_data


@router.post("/invoices/{invoice_id}/approve", status_code=200)
async def approve_invoice_rung4_legal(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    inv_res = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = inv_res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if inv.status != InvoiceStatus.PENDING_HUMAN_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Invoice is in status '{inv.status.value}', not 'pending_human_approval'",
        )

    # Advance with human approval flag set to True per 07_frontend_dashboard.md §9
    final_state = await run_pipeline_for_invoice(
        invoice_id=inv.id,
        db=db,
        human_approved=True,
    )

    return {
        "status": "approved",
        "invoice_id": str(invoice_id),
        "final_decision": final_state.get("final_decision"),
        "audit_entry_id": final_state.get("audit_entry_id"),
    }


@router.post("/invoices/{invoice_id}/draft-reminder", status_code=200)
async def draft_invoice_reminder_notice(
    invoice_id: uuid.UUID,
    register: str = Query("standard business English", description="Register: 'standard business English' or 'Hinglish'"),
    db: AsyncSession = Depends(get_db),
):
    inv_res = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = inv_res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if inv.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Invoice is already paid in full. Notice drafting terminated.")
    if inv.status == InvoiceStatus.WRITTEN_OFF:
        raise HTTPException(status_code=400, detail="Invoice has been written off as unrecovered.")
    if inv.dispute_flag:
        raise HTTPException(status_code=400, detail="Rule 6 (dispute_halt): Active buyer dispute prohibits automated drafting.")
    if inv.current_rung == 0:
        raise HTTPException(status_code=400, detail="Invoice is within credit terms (Rung 0). No reminder is due.")
    if inv.current_rung == 4 or inv.status == InvoiceStatus.PENDING_HUMAN_APPROVAL:
        raise HTTPException(status_code=400, detail="Rule 10: Rung 4 requires operator sign-off before drafting statutory filing.")

    now_utc = datetime.now(timezone.utc)
    cooldown_active = False
    cooldown_days_remaining = 0
    days_since_contact = 0
    if inv.last_contact_at:
        days_since_contact = (now_utc.date() - inv.last_contact_at.date()).days
        if days_since_contact < 7:
            cooldown_active = True
            cooldown_days_remaining = 7 - days_since_contact

    from app.domain_logic.msmed import compute_accrued_interest
    today = now_utc.date()
    days_overdue = (today - inv.statutory_due_date).days if inv.statutory_due_date else 0
    from decimal import Decimal
    from app.config import settings
    computed_interest = 0
    if inv.supplier_is_msme and inv.statutory_due_date and today > inv.statutory_due_date:
        rbi_rate = Decimal(str(settings.RBI_BANK_RATE))
        computed_interest = compute_accrued_interest(
            amount_paise=inv.amount_paise,
            statutory_due_date=inv.statutory_due_date,
            as_of_date=today,
            rbi_bank_rate=rbi_rate,
        )

    from app.ai_layer.prompts.message_drafting import draft_b2b_reminder_gemini
    from app.domain_logic.escalation_ladder import RUNG_METADATA

    draft_result = await draft_b2b_reminder_gemini(
        invoice_number=inv.invoice_number,
        buyer_name=inv.buyer_name,
        amount_paise=inv.amount_paise,
        days_overdue=days_overdue,
        current_rung=inv.current_rung,
        computed_interest_paise=computed_interest,
        supplier_is_msme=inv.supplier_is_msme,
        register=register,
        payment_link_url=inv.razorpay_payment_link_id,
    )

    rung_meta = RUNG_METADATA.get(inv.current_rung, {})

    return {
        "invoice_id": str(inv.id),
        "invoice_number": inv.invoice_number,
        "buyer_name": inv.buyer_name,
        "current_rung": inv.current_rung,
        "rung_tone": rung_meta.get("tone", "polite"),
        "days_overdue": days_overdue,
        "principal_amount_paise": inv.amount_paise,
        "computed_interest_paise": computed_interest,
        "statutory_basis": "MSMED Act 2006, Sections 15-16" if inv.supplier_is_msme else "standard commercial terms",
        "register": register,
        "message_text": draft_result.message_text,
        "cites_interest_figure": draft_result.cites_interest_figure,
        "cooldown_active": cooldown_active,
        "cooldown_days_remaining": cooldown_days_remaining,
        "days_since_contact": days_since_contact,
    }


@router.post("/{module}/{case_id}/create-link", status_code=200)
async def generate_case_payment_link(
    module: str,
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from app.razorpay_client.client import create_payment_link

    module = module.upper()
    amount_paise = 0
    ref_id = ""
    description = ""
    customer_name = ""
    customer_email = "customer@example.com"
    customer_contact = "+919319841600"
    if module == "A":
        pc = await db.scalar(select(PaymentCase).where(PaymentCase.id == case_id))
        if not pc:
            raise HTTPException(status_code=404, detail="PaymentCase not found")
        if pc.status == PaymentCaseStatus.RECOVERED:
            raise HTTPException(status_code=400, detail="Payment already collected and settled into bank.")
        if pc.status == PaymentCaseStatus.CLOSED_UNRECOVERED:
            raise HTTPException(status_code=400, detail="Cannot generate link for unrecoverable closed case")
        if pc.status == PaymentCaseStatus.ESCALATED:
            raise HTTPException(status_code=400, detail="Cannot generate link for escalated case under Rule 5")
        amount_paise = pc.amount_paise
        ref_id = f"ref_a_{str(pc.id)[:8]}"
        description = f"Subscription Recovery: Case {str(pc.id)[:8]}"
        customer_name = "Sarthak Test Customer"
        target_obj = pc

    elif module == "B":
        inv = await db.scalar(select(Invoice).where(Invoice.id == case_id))
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if inv.status == InvoiceStatus.PAID:
            raise HTTPException(status_code=400, detail="Invoice already paid in full.")
        if inv.dispute_flag:
            raise HTTPException(status_code=400, detail="Cannot generate link for disputed invoice under Rule 6")
        if inv.status == InvoiceStatus.WRITTEN_OFF:
            raise HTTPException(status_code=400, detail="Cannot generate link for written-off bad debt")
        amount_paise = inv.amount_paise
        ref_id = inv.invoice_number
        description = f"Invoice Settlement: {inv.invoice_number}"
        customer_name = inv.buyer_name
        customer_email = inv.buyer_email or "buyer@example.com"
        customer_contact = inv.buyer_contact or "+919319841600"
        target_obj = inv

    elif module == "C":
        order = await db.scalar(select(AbandonedOrder).where(AbandonedOrder.id == case_id))
        if not order:
            raise HTTPException(status_code=404, detail="AbandonedOrder not found")
        if order.status == AbandonedOrderStatus.RECOVERED:
            raise HTTPException(status_code=400, detail="Abandoned order already converted and paid.")
        if order.status == AbandonedOrderStatus.SKIPPED_LOW_VALUE:
            raise HTTPException(status_code=400, detail="Cannot generate link for sub-₹200 order under Rule 12")
        if order.status == AbandonedOrderStatus.EXPIRED_UNRECOVERED:
            raise HTTPException(status_code=400, detail="Cart recovery window has expired under Rule 11")
        amount_paise = order.amount_paise
        ref_id = f"ref_c_{str(order.id)[:8]}"
        description = f"Cart Recovery Nudge: Order {str(order.id)[:8]}"
        customer_name = "Priya Sharma"
        customer_contact = order.customer_contact or "+919319841600"
        target_obj = order

    has_real_link = (
        target_obj.razorpay_payment_link_id
        and not target_obj.razorpay_payment_link_id.startswith("plink_alt_")
        and not target_obj.razorpay_payment_link_id.startswith("plink_inv_")
        and not target_obj.razorpay_payment_link_id.startswith("plink_nudge_")
    )
    if has_real_link:
        short_url = None
        try:
            from app.razorpay_client.client import fetch_payment_link
            link_info = await fetch_payment_link(target_obj.razorpay_payment_link_id)
            short_url = link_info.get("short_url")
        except Exception:
            pass

        return {
            "status": "existing",
            "module": module,
            "case_id": str(case_id),
            "payment_link_id": target_obj.razorpay_payment_link_id,
            "short_url": short_url or f"https://rzp.io/rzp/{target_obj.razorpay_payment_link_id.replace('plink_', '')}",
            "amount_paise": amount_paise,
            "amount_inr": amount_paise / 100.0,
        }


    try:
        plink = await create_payment_link(
            amount_paise=amount_paise,
            reference_id=ref_id,
            description=description,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_contact=customer_contact,
            notify_sms=True,
            notify_email=True,
            notes={"case_id": str(case_id), "module": module},
        )
        target_obj.razorpay_payment_link_id = plink.get("id")
        await db.commit()

        return {
            "status": "created",
            "module": module,
            "case_id": str(case_id),
            "payment_link_id": plink.get("id"),
            "short_url": plink.get("short_url"),
            "amount_paise": amount_paise,
            "amount_inr": amount_paise / 100.0,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Razorpay API link generation failed: {str(exc)}",
        )


@router.post("/{module}/{case_id}/simulate-webhook", status_code=200)
async def simulate_case_webhook(
    module: str,
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from app.api.routes.webhooks import process_webhook_recovery
    from app.db.models.webhook_event import RawWebhookEvent

    module = module.upper()
    payment_id = f"pay_sim_{uuid.uuid4().hex[:12]}"
    amount_paise = 0

    if module == "A":
        pc = await db.scalar(select(PaymentCase).where(PaymentCase.id == case_id))
        if not pc:
            raise HTTPException(status_code=404, detail="PaymentCase not found")
        if pc.status == PaymentCaseStatus.RECOVERED:
            raise HTTPException(status_code=400, detail="PaymentCase already settled")
        if pc.status == PaymentCaseStatus.CLOSED_UNRECOVERED:
            raise HTTPException(status_code=400, detail="Cannot simulate payment on closed unrecovered case")
        if pc.status == PaymentCaseStatus.ESCALATED:
            raise HTTPException(status_code=400, detail="Cannot simulate payment on escalated case under Rule 5")
        amount_paise = pc.amount_paise
        ref_id = f"ref_a_{str(pc.id)[:8]}"
    elif module == "B":
        inv = await db.scalar(select(Invoice).where(Invoice.id == case_id))
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if inv.status == InvoiceStatus.PAID:
            raise HTTPException(status_code=400, detail="Invoice already paid in full")
        if inv.dispute_flag:
            raise HTTPException(status_code=400, detail="Cannot simulate payment on disputed invoice under Rule 6")
        if inv.status == InvoiceStatus.WRITTEN_OFF:
            raise HTTPException(status_code=400, detail="Cannot simulate payment on written-off debt")
        amount_paise = inv.amount_paise
        ref_id = inv.invoice_number
    elif module == "C":
        order = await db.scalar(select(AbandonedOrder).where(AbandonedOrder.id == case_id))
        if not order:
            raise HTTPException(status_code=404, detail="AbandonedOrder not found")
        if order.status == AbandonedOrderStatus.RECOVERED:
            raise HTTPException(status_code=400, detail="Order already recovered and paid")
        if order.status == AbandonedOrderStatus.SKIPPED_LOW_VALUE:
            raise HTTPException(status_code=400, detail="Cannot simulate payment on sub-₹200 order skipped under Rule 12")
        if order.status == AbandonedOrderStatus.EXPIRED_UNRECOVERED:
            raise HTTPException(status_code=400, detail="Cannot simulate payment on expired cart recovery")
        amount_paise = order.amount_paise
        ref_id = f"ref_c_{str(order.id)[:8]}"
    else:
        raise HTTPException(status_code=400, detail="Invalid module")

    payload = {
        "event": "payment.captured",
        "entity": "event",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "amount": amount_paise,
                    "status": "captured",
                    "method": "upi",
                    "notes": {"case_id": str(case_id), "module": module},
                }
            }
        },
    }

    raw_event = RawWebhookEvent(
        razorpay_event_id=f"evt_{payment_id}",
        event_type="payment.captured",
        signature_verified=True,
        processed=True,
        payload=payload,
    )
    db.add(raw_event)
    await db.commit()

    recovery_info = await process_webhook_recovery(payload, db)
    await db.commit()

    return {
        "status": "recovered",
        "module": module,
        "case_id": str(case_id),
        "simulated_payment_id": payment_id,
        "amount_inr": amount_paise / 100.0,
        "recovery": recovery_info,
    }


@router.get("/{module}/{case_id}/voice-nudge", status_code=200)
async def get_case_voice_nudge(
    module: str,
    case_id: uuid.UUID,
    synthesize: bool = Query(False),
    speaker: str = Query("priya"),
    custom_script: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    from app.tts.service import (
        draft_dynamic_hinglish_voice_script,
        get_stored_audio_info,
        synthesize_hinglish_voice,
    )

    module = module.upper()
    case_data: dict[str, Any] = {}

    if module == "A":
        pc = await db.scalar(select(PaymentCase).where(PaymentCase.id == case_id))
        if not pc:
            raise HTTPException(status_code=404, detail="PaymentCase not found")
        if pc.status == PaymentCaseStatus.RECOVERED:
            cdata = serialize_payment_case(pc)
            archived_script = await draft_dynamic_hinglish_voice_script("A", cdata)
            return {
                "status": "settled",
                "can_generate": False,
                "reason": "Payment has been cleared and settled into bank. Outbound collection calls are terminated.",
                "script_text": archived_script,
                "archived_call_metadata": {
                    "channel": "Autonomous AI Outbound Voice",
                    "provider": "Sarvam AI Bulbul:v3 Neural Engine",
                    "call_status": "Answered & Converted",
                    "duration_seconds": 32,
                    "outcome": "Debtor completed payment via Razorpay after voice outreach",
                },
                "audio_base64": None,
            }
        if pc.status == PaymentCaseStatus.CLOSED_UNRECOVERED:
            return {
                "status": "closed",
                "can_generate": False,
                "reason": "Rule 1 & Rule 3: Retries exhausted or card permanently dead. Automated voice outreach halted.",
                "script_text": None,
                "audio_base64": None,
            }
        if pc.status == PaymentCaseStatus.ESCALATED:
            return {
                "status": "blocked",
                "can_generate": False,
                "reason": "Rule 5: Gateway data sync gap. Escalated to human operations; automated voice outreach blocked.",
                "script_text": None,
                "audio_base64": None,
            }
        case_data = serialize_payment_case(pc)

    elif module == "B":
        inv = await db.scalar(select(Invoice).where(Invoice.id == case_id))
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if inv.status == InvoiceStatus.PAID:
            cdata = serialize_invoice(inv)
            archived_script = await draft_dynamic_hinglish_voice_script("B", cdata)
            return {
                "status": "settled",
                "can_generate": False,
                "reason": "Invoice paid in full. Outbound collection calls are terminated.",
                "script_text": archived_script,
                "archived_call_metadata": {
                    "channel": "Autonomous AI Outbound Voice",
                    "provider": "Sarvam AI Bulbul:v3 Neural Engine",
                    "call_status": "Answered & Converted",
                    "duration_seconds": 38,
                    "outcome": "Buyer settled invoice via Razorpay after statutory reminder",
                },
                "audio_base64": None,
            }
        if inv.dispute_flag:
            return {
                "status": "blocked",
                "can_generate": False,
                "reason": "Rule 6: Active dispute prohibits all automated customer outreach.",
                "script_text": None,
                "audio_base64": None,
            }
        if inv.status == InvoiceStatus.WRITTEN_OFF:
            return {
                "status": "closed",
                "can_generate": False,
                "reason": "Invoice has been written off as unrecovered bad debt. Collection calls terminated.",
                "script_text": None,
                "audio_base64": None,
            }
        if inv.status == InvoiceStatus.PENDING_HUMAN_APPROVAL:
            return {
                "status": "blocked",
                "can_generate": False,
                "reason": "Rule 10: Rung 4 legal filing requires human sign-off before further action.",
                "script_text": None,
                "audio_base64": None,
            }
        case_data = serialize_invoice(inv)

    elif module == "C":
        order = await db.scalar(select(AbandonedOrder).where(AbandonedOrder.id == case_id))
        if not order:
            raise HTTPException(status_code=404, detail="AbandonedOrder not found")
        if order.status == AbandonedOrderStatus.RECOVERED:
            cdata = serialize_abandoned_order(order)
            archived_script = await draft_dynamic_hinglish_voice_script("C", cdata)
            return {
                "status": "settled",
                "can_generate": False,
                "reason": "Checkout cart converted and paid. Outbound recovery calls are terminated.",
                "script_text": archived_script,
                "archived_call_metadata": {
                    "channel": "Autonomous AI Outbound Voice",
                    "provider": "Sarvam AI Bulbul:v3 Neural Engine",
                    "call_status": "Answered & Converted",
                    "duration_seconds": 24,
                    "outcome": "Shopper completed checkout via Razorpay Payment Link",
                },
                "audio_base64": None,
            }
        if order.status == AbandonedOrderStatus.SKIPPED_LOW_VALUE or order.amount_paise < 20000:
            return {
                "status": "blocked",
                "can_generate": False,
                "reason": "Rule 12: Order amount is below the ₹200 recovery floor. Nudge skipped.",
                "script_text": None,
                "audio_base64": None,
            }
        if order.status == AbandonedOrderStatus.EXPIRED_UNRECOVERED:
            return {
                "status": "closed",
                "can_generate": False,
                "reason": "Single nudge window elapsed without conversion. Cart recovery closed under Rule 11.",
                "script_text": None,
                "audio_base64": None,
            }
        case_data = serialize_abandoned_order(order)

    else:
        raise HTTPException(status_code=400, detail="Invalid module")

    stored_info = get_stored_audio_info(module, str(case_id), speaker)
    audio_url = stored_info["audio_url"] if stored_info else None
    audio_base64 = None

    if custom_script and custom_script.strip():
        script = custom_script.strip()
    elif stored_info and stored_info.get("script_text"):
        script = stored_info["script_text"]
    else:
        script = await draft_dynamic_hinglish_voice_script(module, case_data)

    if synthesize:
        try:
            tts_res = await synthesize_hinglish_voice(
                script,
                speaker=speaker,
                module=module,
                case_id=str(case_id),
            )
            audio_base64 = tts_res["audio_base64"]
            audio_url = tts_res["audio_url"] or audio_url
            script = tts_res.get("text", script)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Sarvam TTS Error: {str(exc)}")

    return {
        "status": "synthesized" if audio_url else "ready",
        "can_generate": True,
        "module": module,
        "case_id": str(case_id),
        "script_text": script,
        "audio_url": audio_url,
        "audio_base64": audio_base64,
        "speaker": speaker,
    }



