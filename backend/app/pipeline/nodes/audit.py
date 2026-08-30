import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLogEntry, CaseType, PipelineStage
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.session import async_session_factory
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

    case_type_map = {
        "A": CaseType.PAYMENT_CASE,
        "B": CaseType.INVOICE,
        "C": CaseType.ABANDONED_ORDER,
    }
    case_type = case_type_map.get(module, CaseType.ABANDONED_ORDER)

    case_uuid = uuid.UUID(case_id_str) if case_id_str else uuid.uuid4()
    batch_uuid = uuid.UUID(batch_id_str) if batch_id_str else uuid.uuid4()

    async with async_session_factory() as db:
        # 1. Unconditionally insert row in audit_log
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
            razorpay_reference=razorpay_ref,
        )
        db.add(audit_entry)

        # 2. Update the underlying record in database
        if module == "C" and case_id_str:
            order_res = await db.execute(
                select(AbandonedOrder).where(AbandonedOrder.id == case_uuid)
            )
            order = order_res.scalar_one_or_none()
            if order:
                now_utc = datetime.now(timezone.utc)
                if final_decision == "send_abandonment_nudge":
                    order.nudge_sent = True
                    order.nudge_sent_at = now_utc
                    order.status = AbandonedOrderStatus.NUDGED
                    if razorpay_ref:
                        order.razorpay_payment_link_id = razorpay_ref
                elif final_decision == "skipped_low_value":
                    order.status = AbandonedOrderStatus.SKIPPED_LOW_VALUE

        await db.commit()
        await db.refresh(audit_entry)
        audit_id = audit_entry.id

    return {
        "audit_entry_id": audit_id,
    }
