from datetime import datetime, timezone
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_layer.prompts.batch_pattern_detection import narrate_pattern, propose_pattern_candidates
from app.db.models.audit_log import AuditLogEntry, CaseType
from app.db.models.batch import Batch
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus
from app.db.session import get_db
from app.domain_logic.pattern_detection import detect_systemic_patterns
from app.pipeline.run import run_pipeline_for_invoice, run_pipeline_for_order, run_pipeline_for_payment_case
from app.synthetic_data.generator import generate_batch

router = APIRouter()


class CreateBatchRunRequest(BaseModel):
    label: str | None = None
    description: str | None = None
    seed: int = 42


@router.get("", status_code=200)
async def list_batches(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Batch).order_by(Batch.created_at.desc()))
    batches = res.scalars().all()
    return [
        {
            "id": str(b.id),
            "label": b.label,
            "description": b.description,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in batches
    ]


@router.get("/{batch_id}/summary", status_code=200)
async def get_batch_summary(batch_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    batch_res = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = batch_res.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Module A aggregates
    res_a = await db.execute(
        select(
            func.count(PaymentCase.id),
            func.coalesce(func.sum(PaymentCase.amount_paise), 0),
        ).where(PaymentCase.batch_id == batch_id)
    )
    count_a, at_risk_a = res_a.one()

    # Module B aggregates
    res_b = await db.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.amount_paise), 0),
        ).where(Invoice.batch_id == batch_id)
    )
    count_b, at_risk_b = res_b.one()

    # Module C aggregates
    res_c = await db.execute(
        select(
            func.count(AbandonedOrder.id),
            func.coalesce(func.sum(AbandonedOrder.amount_paise), 0),
        ).where(AbandonedOrder.batch_id == batch_id)
    )
    count_c, at_risk_c = res_c.one()

    total_cases = int(count_a + count_b + count_c)
    total_at_risk_paise = int(at_risk_a + at_risk_b + at_risk_c)

    # Settlement / Recovered totals from Audit Log per 02_data_model.md §7
    audit_res = await db.execute(
        select(
            func.coalesce(func.sum(AuditLogEntry.gross_amount_paise), 0),
            func.coalesce(func.sum(AuditLogEntry.mdr_paise), 0),
            func.coalesce(func.sum(AuditLogEntry.gst_on_mdr_paise), 0),
            func.coalesce(func.sum(AuditLogEntry.net_amount_paise), 0),
            func.coalesce(func.sum(AuditLogEntry.computed_interest_accrued_paise), 0),
        ).where(
            AuditLogEntry.batch_id == batch_id,
            AuditLogEntry.final_action.in_(["recovered", "paid"]),
        )
    )
    gross_rec_paise, total_mdr, total_gst, net_rec_paise, total_interest_accrued = [
        int(x) for x in audit_res.one()
    ]

    # Exception counts
    unrec_a = int(await db.scalar(
        select(func.count(PaymentCase.id)).where(
            PaymentCase.batch_id == batch_id,
            PaymentCase.status == PaymentCaseStatus.CLOSED_UNRECOVERED,
        )
    ) or 0)

    unrec_b = int(await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.batch_id == batch_id,
            Invoice.status == InvoiceStatus.WRITTEN_OFF,
        )
    ) or 0)

    unrec_c = int(await db.scalar(
        select(func.count(AbandonedOrder.id)).where(
            AbandonedOrder.batch_id == batch_id,
            AbandonedOrder.status == AbandonedOrderStatus.EXPIRED_UNRECOVERED,
        )
    ) or 0)

    exception_count = unrec_a + unrec_b + unrec_c
    recovery_rate = (gross_rec_paise / total_at_risk_paise) if total_at_risk_paise > 0 else 0.0

    return {
        "batch_id": str(batch_id),
        "label": batch.label,
        "total_cases": total_cases,
        "total_at_risk_paise": total_at_risk_paise,
        "total_at_risk_inr": total_at_risk_paise / 100.0,
        "gross_recovered_paise": gross_rec_paise,
        "gross_recovered_inr": gross_rec_paise / 100.0,
        "mdr_fees_paise": total_mdr,
        "gst_on_mdr_paise": total_gst,
        "net_recovered_paise": net_rec_paise,
        "net_recovered_inr": net_rec_paise / 100.0,
        "total_interest_accrued_paise": total_interest_accrued,
        "total_interest_accrued_inr": total_interest_accrued / 100.0,
        "recovery_rate": round(recovery_rate, 4),
        "exception_count": exception_count,
        "modules": {
            "A": {"cases": int(count_a), "at_risk_paise": int(at_risk_a), "at_risk_inr": int(at_risk_a) / 100.0, "exceptions": unrec_a},
            "B": {"cases": int(count_b), "at_risk_paise": int(at_risk_b), "at_risk_inr": int(at_risk_b) / 100.0, "exceptions": unrec_b},
            "C": {"cases": int(count_c), "at_risk_paise": int(at_risk_c), "at_risk_inr": int(at_risk_c) / 100.0, "exceptions": unrec_c},
        },
    }


@router.post("/run", status_code=201)
async def run_batch(req: CreateBatchRunRequest, db: AsyncSession = Depends(get_db)):
    # 1. Generate fresh 135-case batch
    batch_label = req.label or f"Synthetic Batch {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
    batch = await generate_batch(db, label=batch_label, seed=req.seed)

    # 2. Execute initial pipeline pass for all cases
    cases_a = (await db.execute(select(PaymentCase).where(PaymentCase.batch_id == batch.id))).scalars().all()
    for pc in cases_a:
        await run_pipeline_for_payment_case(pc.id, db)

    invoices = (await db.execute(select(Invoice).where(Invoice.batch_id == batch.id))).scalars().all()
    for inv in invoices:
        await run_pipeline_for_invoice(inv.id, db)

    orders = (await db.execute(select(AbandonedOrder).where(AbandonedOrder.batch_id == batch.id))).scalars().all()
    for o in orders:
        await run_pipeline_for_order(o.id, db)

    return {
        "status": "completed",
        "batch_id": str(batch.id),
        "label": batch.label,
        "cases_processed": len(cases_a) + len(invoices) + len(orders),
    }


@router.get("/{batch_id}/pattern", status_code=200)
async def get_batch_pattern(batch_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Fetch all Module A payment cases in batch
    cases_res = await db.execute(
        select(PaymentCase).where(PaymentCase.batch_id == batch_id)
    )
    cases = cases_res.scalars().all()
    if not cases:
        raise HTTPException(status_code=404, detail="No Module A cases found for this batch")

    # Step 1: Gemini candidate proposals
    case_summary = (
        f"Batch with {len(cases)} payment failures across card, upi, netbanking.\n"
        "Time distribution: multiple UPI failures clustered between 10:00-13:00 IST.\n"
        "Methods: UPI, Card, Netbanking."
    )
    candidates = await propose_pattern_candidates(case_summary)

    # Step 2: Deterministic verification
    findings = detect_systemic_patterns(cases)

    # Step 3: Gemini narration on confirmed findings
    narrations = []
    for f in findings:
        narration_text = await narrate_pattern(
            pattern_type=f.pattern_type,
            candidate_description=f.description,
            bucket_count=f.bucket_count,
            total_cases_in_scope=f.total_cases_in_scope,
            observed_share=f.observed_share,
            expected_share_under_uniform=f.expected_share_under_uniform,
        )
        narrations.append(
            {
                "pattern_type": f.pattern_type,
                "description": f.description,
                "bucket_count": f.bucket_count,
                "total_cases_in_scope": f.total_cases_in_scope,
                "observed_share": round(f.observed_share, 4),
                "expected_share": round(f.expected_share_under_uniform, 4),
                "excess_ratio": round(f.observed_share / f.expected_share_under_uniform, 2),
                "narration": narration_text,
            }
        )

    return {
        "batch_id": str(batch_id),
        "candidates_proposed": candidates.candidate_groupings,
        "verified_findings_count": len(findings),
        "findings": narrations,
    }
