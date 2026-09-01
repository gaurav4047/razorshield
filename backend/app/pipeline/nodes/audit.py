from decimal import Decimal
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLogEntry, CaseType, PipelineStage
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.payment_case import (
    FaultAttribution,
    InterventionType,
    PaymentCase,
    PaymentCaseStatus,
    PaymentMethod,
)
from app.db.session import async_session_factory
from app.domain_logic.settlement import compute_settlement
from app.pipeline.state import PipelineState


async def audit_node(state: PipelineState) -> dict:
    module = state.get("module")
    case_id_str = state.get("case_id")
    batch_id_str = state.get("batch_id")
    final_decision = state.get("final_decision", "unknown")
    stopping_rules = state.get("stopping_rules_checked", [])
    reason = state.get("reason", "Pipeline execution completed")
    ai_reasoning = state.get("ai_reasoning")
    rule_suggested = state.get("rule_recommendation")
    razorpay_ref = state.get("razorpay_reference_id")
    gross_amount = state.get("order_amount_paise")
    computed_interest = state.get("computed_interest_paise")

    case_type_map = {
        "A": CaseType.PAYMENT_CASE,
        "B": CaseType.INVOICE,
        "C": CaseType.ABANDONED_ORDER,
    }
    case_type = case_type_map.get(module, CaseType.ABANDONED_ORDER)

    case_uuid = uuid.UUID(case_id_str) if case_id_str else uuid.uuid4()
    batch_uuid = uuid.UUID(batch_id_str) if batch_id_str else uuid.uuid4()

    # Call compute_settlement whenever gross amount is present per 03_domain_logic.md §7
    mdr_paise = None
    gst_on_mdr_paise = None
    net_amount_paise = None

    if gross_amount:
        method_str = state.get("method", "card")
        method_enum = (
            PaymentMethod(method_str)
            if method_str in PaymentMethod._value2member_map_
            else PaymentMethod.CARD
        )
        is_rupay = bool(state.get("is_rupay_credit_on_upi", False))
        is_cardless = bool(state.get("is_cardless_emi", False))

        breakdown = compute_settlement(
            gross_amount_paise=gross_amount,
            method=method_enum,
            is_rupay_credit_on_upi=is_rupay,
            is_cardless_emi=is_cardless,
        )
        mdr_paise = breakdown.mdr_paise
        gst_on_mdr_paise = breakdown.gst_on_mdr_paise
        net_amount_paise = breakdown.net_amount_paise

    async with async_session_factory() as db:
        # 1. Unconditionally insert row in audit_log with settlement breakdown
        audit_entry = AuditLogEntry(
            batch_id=batch_uuid,
            case_type=case_type,
            case_id=case_uuid,
            stage=PipelineStage.AUDIT,
            rule_suggested_action=rule_suggested,
            ai_reasoning_text=ai_reasoning,
            stopping_rules_checked=stopping_rules,
            final_action=final_decision,
            reason=reason,
            gross_amount_paise=gross_amount,
            mdr_paise=mdr_paise,
            gst_on_mdr_paise=gst_on_mdr_paise,
            net_amount_paise=net_amount_paise,
            computed_interest_accrued_paise=computed_interest,
            razorpay_reference=razorpay_ref,
        )
        db.add(audit_entry)

        # 2. Update the underlying record in database
        now_utc = datetime.now(timezone.utc)

        if module == "A" and case_id_str:
            case_res = await db.execute(
                select(PaymentCase).where(PaymentCase.id == case_uuid)
            )
            pc = case_res.scalar_one_or_none()
            if pc:
                if state.get("fault_attribution"):
                    pc.fault_attribution = FaultAttribution(state["fault_attribution"])
                if state.get("classified_root_cause"):
                    pc.classified_root_cause = state["classified_root_cause"]
                if state.get("diagnosis_confidence") is not None:
                    pc.diagnosis_confidence = Decimal(str(round(state["diagnosis_confidence"], 3)))
                if state.get("recommended_intervention"):
                    pc.recommended_intervention = InterventionType(state["recommended_intervention"])
                if state.get("npci_window_conflict") is not None:
                    pc.npci_execution_window_conflict = state["npci_window_conflict"]

                if final_decision in ("silent_retry", "delayed_retry_notify", "alternate_method"):
                    pc.status = PaymentCaseStatus.RETRIED
                    pc.retry_count += 1
                    pc.last_action_at = now_utc
                    if razorpay_ref and razorpay_ref.startswith("plink_"):
                        pc.razorpay_payment_link_id = razorpay_ref
                elif final_decision == "escalate_human":
                    pc.status = PaymentCaseStatus.ESCALATED
                    pc.last_action_at = now_utc
                elif final_decision == "recovered":
                    pc.status = PaymentCaseStatus.RECOVERED
                    pc.last_action_at = now_utc

        elif module == "B" and case_id_str:
            inv_res = await db.execute(select(Invoice).where(Invoice.id == case_uuid))
            inv = inv_res.scalar_one_or_none()
            if inv:
                if state.get("current_rung") is not None:
                    inv.current_rung = state["current_rung"]
                if state.get("dispute_flag") is not None:
                    inv.dispute_flag = state["dispute_flag"]

                if final_decision == "blocked_dispute_halt":
                    inv.dispute_flag = True
                    inv.status = InvoiceStatus.DISPUTED
                elif final_decision.startswith("rung_"):
                    inv.last_contact_at = now_utc
                    inv.status = InvoiceStatus.OVERDUE
                    if razorpay_ref and razorpay_ref.startswith("plink_"):
                        inv.razorpay_payment_link_id = razorpay_ref
                elif final_decision == "pending_human_approval":
                    inv.status = InvoiceStatus.PENDING_HUMAN_APPROVAL
                elif final_decision == "recovered":
                    inv.status = InvoiceStatus.PAID
                    inv.amount_paid_paise = inv.amount_paise

        elif module == "C" and case_id_str:
            order_res = await db.execute(
                select(AbandonedOrder).where(AbandonedOrder.id == case_uuid)
            )
            order = order_res.scalar_one_or_none()
            if order:
                if final_decision == "send_abandonment_nudge":
                    order.nudge_sent = True
                    order.nudge_sent_at = now_utc
                    order.status = AbandonedOrderStatus.NUDGED
                    if razorpay_ref:
                        order.razorpay_payment_link_id = razorpay_ref
                elif final_decision == "skipped_low_value":
                    order.status = AbandonedOrderStatus.SKIPPED_LOW_VALUE
                elif final_decision == "recovered":
                    order.status = AbandonedOrderStatus.RECOVERED

        await db.commit()
        await db.refresh(audit_entry)
        audit_id = audit_entry.id

        # Live WebSocket broadcast per 01_architecture.md §3 and 07_frontend_dashboard.md §6
        try:
            from app.api.routes.audit import audit_manager, serialize_audit_entry
            await audit_manager.broadcast(serialize_audit_entry(audit_entry))
        except Exception:
            pass

    return {
        "audit_entry_id": audit_id,
    }
