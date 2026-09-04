from datetime import date
from decimal import Decimal
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.invoice import Invoice
from app.db.models.order import AbandonedOrder
from app.db.models.payment_case import PaymentCase
from app.domain_logic.msmed import compute_accrued_interest
from app.pipeline.graph import build_module_graph
from app.pipeline.state import PipelineState

# Pre-compiled graphs per module
module_graphs = {
    "A": build_module_graph("A"),
    "B": build_module_graph("B"),
    "C": build_module_graph("C"),
}


async def run_pipeline_for_invoice(
    invoice_id: uuid.UUID | str,
    db: AsyncSession,
    buyer_reply: str | None = None,
    supplier_is_msme: bool = True,
    human_approved: bool = False,
) -> PipelineState:
    inv_uuid = uuid.UUID(str(invoice_id))
    result = await db.execute(select(Invoice).where(Invoice.id == inv_uuid))
    inv = result.scalar_one_or_none()

    if not inv:
        raise ValueError(f"Invoice with ID {invoice_id} not found")

    today_d = date.today()
    interest_paise = 0
    if supplier_is_msme and inv.statutory_due_date and today_d > inv.statutory_due_date:
        interest_paise = compute_accrued_interest(
            inv.amount_paise, inv.statutory_due_date, today_d, Decimal("6.75")
        )

    initial_state: PipelineState = {
        "module": "B",
        "case_id": str(inv.id),
        "batch_id": str(inv.batch_id),
        "order_amount_paise": inv.amount_paise,
        "statutory_due_date": inv.statutory_due_date.isoformat() if inv.statutory_due_date else None,
        "current_rung": inv.current_rung,
        "dispute_flag": inv.dispute_flag,
        "broken_promise_count": inv.broken_promise_count,
        "supplier_is_msme": supplier_is_msme,
        "computed_interest_paise": interest_paise,
        "last_contact_at": inv.last_contact_at.isoformat() if inv.last_contact_at else None,
        "human_approved": human_approved,
        "buyer_response_text": buyer_reply,
        "fault_attribution": None,
        "classified_root_cause": None,
        "ai_reasoning": None,
        "diagnosis_confidence": None,
        "recommended_intervention": None,
        "policy_passed": False,
        "stopping_rules_checked": [],
        "rule_recommendation": None,
        "final_decision": "unprocessed",
        "reason": None,
        "razorpay_reference_id": None,
        "execution_result": None,
        "audit_entry_id": None,
    }

    graph = module_graphs["B"]
    final_state = await graph.ainvoke(initial_state)
    return final_state


async def run_pipeline_for_payment_case(
    case_id: uuid.UUID | str,
    db: AsyncSession,
    case_history: str | None = None,
    ignore_cooldown: bool = False,
) -> PipelineState:
    case_uuid = uuid.UUID(str(case_id))
    result = await db.execute(select(PaymentCase).where(PaymentCase.id == case_uuid))
    pc = result.scalar_one_or_none()

    if not pc:
        raise ValueError(f"PaymentCase with ID {case_id} not found")

    # Automatically query and inject historical context from audit logs if not explicitly passed
    if not case_history:
        from app.db.models.audit_log import AuditLogEntry
        audit_res = await db.execute(
            select(AuditLogEntry)
            .where(AuditLogEntry.case_id == case_uuid)
            .order_by(AuditLogEntry.timestamp.asc())
        )
        prior_audits = audit_res.scalars().all()
        if len(prior_audits) > 1:
            history_lines = [
                f"- Attempt {i+1} ({a.timestamp.strftime('%Y-%m-%d %H:%M') if a.timestamp else 'prior'}): action={a.final_action}, reason={a.reason}"
                for i, a in enumerate(prior_audits)
            ]
            case_history = f"Historical attempts on this case:\n" + "\n".join(history_lines)
        elif pc.retry_count > 0 or pc.attempt_number > 1:
            case_history = f"Case has {pc.retry_count} prior retries (attempt #{pc.attempt_number})."

    initial_state: PipelineState = {
        "module": "A",
        "case_id": str(pc.id),
        "batch_id": str(pc.batch_id),
        "method": pc.method.value,
        "context": pc.context.value,
        "failure_code": pc.failure_code,

        "failure_raw_reason": pc.failure_raw_reason,
        "attempt_number": pc.attempt_number,
        "retry_count": pc.retry_count,
        "order_amount_paise": pc.amount_paise,
        "last_action_at": (
            None if ignore_cooldown else (pc.last_action_at.isoformat() if pc.last_action_at else None)
        ),
        "subscription_state": pc.subscription_state.value if pc.subscription_state else None,
        "case_history": case_history,
        "fault_attribution": None,
        "classified_root_cause": None,
        "ai_reasoning": None,
        "diagnosis_confidence": None,
        "recommended_intervention": None,
        "policy_passed": False,
        "stopping_rules_checked": [],
        "rule_recommendation": None,
        "final_decision": "unprocessed",
        "reason": None,
        "razorpay_reference_id": None,
        "execution_result": None,
        "audit_entry_id": None,
    }

    graph = module_graphs["A"]
    final_state = await graph.ainvoke(initial_state)
    return final_state


async def run_pipeline_for_order(order_id: uuid.UUID | str, db: AsyncSession) -> PipelineState:
    order_uuid = uuid.UUID(str(order_id))
    result = await db.execute(select(AbandonedOrder).where(AbandonedOrder.id == order_uuid))
    order = result.scalar_one_or_none()

    if not order:
        raise ValueError(f"AbandonedOrder with ID {order_id} not found")

    initial_state: PipelineState = {
        "module": "C",
        "case_id": str(order.id),
        "batch_id": str(order.batch_id),
        "order_amount_paise": order.amount_paise,
        "order_created_at": order.order_created_at.isoformat() if order.order_created_at else None,
        "nudge_sent": order.nudge_sent,
        "abandonment_detected": True,
        "fault_attribution": None,
        "classified_root_cause": None,
        "ai_reasoning": None,
        "diagnosis_confidence": None,
        "recommended_intervention": None,
        "policy_passed": False,
        "stopping_rules_checked": [],
        "rule_recommendation": None,
        "final_decision": "unprocessed",
        "reason": None,
        "razorpay_reference_id": None,
        "execution_result": None,
        "audit_entry_id": None,
    }

    graph = module_graphs["C"]
    final_state = await graph.ainvoke(initial_state)
    return final_state
