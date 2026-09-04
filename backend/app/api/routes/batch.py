from datetime import datetime, timezone
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_layer.prompts.batch_pattern_detection import narrate_pattern, propose_pattern_candidates
from app.db.models.audit_log import AuditLogEntry, CaseType
from app.db.models.batch import Batch
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus
from app.db.session import get_db
from app.domain_logic.pattern_detection import (
    detect_systemic_patterns,
    detect_systemic_patterns_b,
    detect_systemic_patterns_c,
)
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
            AuditLogEntry.final_action.in_(["recovered", "paid", "partially_paid"]),
        )
    )
    gross_rec_paise, total_mdr, total_gst, net_rec_paise, total_interest_accrued = [
        int(x) for x in audit_res.one()
    ]

    settled_res = await db.scalar(
        select(func.count(distinct(AuditLogEntry.case_id))).where(
            AuditLogEntry.batch_id == batch_id,
            AuditLogEntry.final_action.in_(["recovered", "paid"]),
        )
    )
    settled_cases_count = int(settled_res or 0)

    # Partial payment metrics
    partial_res = await db.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.amount_paid_paise), 0),
        ).where(
            Invoice.batch_id == batch_id,
            Invoice.status == InvoiceStatus.PARTIALLY_PAID,
        )
    )
    partial_count, partial_amount_paise = [int(x) for x in partial_res.one()]

    # Categorized Exception Breakdown
    low_value_skipped = int(await db.scalar(
        select(func.count(AbandonedOrder.id)).where(
            AbandonedOrder.batch_id == batch_id,
            AbandonedOrder.status == AbandonedOrderStatus.SKIPPED_LOW_VALUE,
        )
    ) or 0)

    disputed_halted = int(await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.batch_id == batch_id,
            Invoice.dispute_flag.is_(True),
        )
    ) or 0)

    hard_declines = int(await db.scalar(
        select(func.count(PaymentCase.id)).where(
            PaymentCase.batch_id == batch_id,
            PaymentCase.status == PaymentCaseStatus.CLOSED_UNRECOVERED,
        )
    ) or 0)

    samadhaan_pending = int(await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.batch_id == batch_id,
            Invoice.current_rung == 4,
            Invoice.status == InvoiceStatus.PENDING_HUMAN_APPROVAL,
        )
    ) or 0)

    gateway_escalated = int(await db.scalar(
        select(func.count(PaymentCase.id)).where(
            PaymentCase.batch_id == batch_id,
            PaymentCase.status == PaymentCaseStatus.ESCALATED,
        )
    ) or 0)

    written_off_count = int(await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.batch_id == batch_id,
            Invoice.status == InvoiceStatus.WRITTEN_OFF,
        )
    ) or 0)

    expired_unrecovered_count = int(await db.scalar(
        select(func.count(AbandonedOrder.id)).where(
            AbandonedOrder.batch_id == batch_id,
            AbandonedOrder.status == AbandonedOrderStatus.EXPIRED_UNRECOVERED,
        )
    ) or 0)

    # Exception counts per module
    unrec_a = hard_declines + gateway_escalated
    unrec_b = disputed_halted + samadhaan_pending + written_off_count
    unrec_c = low_value_skipped + expired_unrecovered_count

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
        "settled_cases_count": settled_cases_count,
        "recovery_rate": round(recovery_rate, 4),
        "case_recovery_rate": round(settled_cases_count / total_cases, 4) if total_cases > 0 else 0.0,
        "partially_paid_count": partial_count,
        "partially_paid_amount_paise": partial_amount_paise,
        "partially_paid_amount_inr": partial_amount_paise / 100.0,
        "exception_count": exception_count,
        "exceptions_breakdown": {
            "low_value_floor_skipped": low_value_skipped,
            "disputed_invoices_halted": disputed_halted,
            "hard_declines_halted": hard_declines,
            "samadhaan_filing_pending": samadhaan_pending,
            "gateway_sync_escalated": gateway_escalated,
            "written_off_debts": written_off_count,
            "expired_unrecovered_orders": expired_unrecovered_count,
        },
        "modules": {
            "A": {"cases": int(count_a), "at_risk_paise": int(at_risk_a), "at_risk_inr": int(at_risk_a) / 100.0, "exceptions": unrec_a},
            "B": {"cases": int(count_b), "at_risk_paise": int(at_risk_b), "at_risk_inr": int(at_risk_b) / 100.0, "exceptions": unrec_b},
            "C": {"cases": int(count_c), "at_risk_paise": int(at_risk_c), "at_risk_inr": int(at_risk_c) / 100.0, "exceptions": unrec_c},
        },
    }


@router.post("/run", status_code=201)
async def run_batch(
    req: CreateBatchRunRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    # 1. Generate fresh complete 135-case batch with audit telemetry
    req_obj = req or CreateBatchRunRequest()
    batch_label = req_obj.label or f"Synthetic Batch {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
    batch = await generate_batch(db, label=batch_label, seed=req_obj.seed)

    return {
        "status": "completed",
        "batch_id": str(batch.id),
        "label": batch.label,
        "cases_processed": 135,
    }


# In-memory pattern cache to guarantee instant sub-millisecond response on re-renders and tab switches
_PATTERN_CACHE: dict[str, dict[str, Any]] = {}


@router.get("/{batch_id}/pattern", status_code=200)
async def get_batch_pattern(
    batch_id: uuid.UUID,
    module: str = Query("A"),
    db: AsyncSession = Depends(get_db),
):
    mod = (module or "A").upper()
    cache_key = f"{str(batch_id)}_{mod}"
    if cache_key in _PATTERN_CACHE:
        return _PATTERN_CACHE[cache_key]

    findings = []
    candidate_groupings = []

    if mod == "B":
        inv_res = await db.execute(select(Invoice).where(Invoice.batch_id == batch_id))
        invoices = inv_res.scalars().all()
        findings = detect_systemic_patterns_b(invoices)
        candidate_groupings = [
            "Overdue B2B invoices exceeding MSMED 45-day statutory limit",
            "Disputed accounts halted under Rule 6",
            "Chronic defaults approaching Rung 4 Samadhaan legal demand",
        ]
    elif mod == "C":
        ord_res = await db.execute(select(AbandonedOrder).where(AbandonedOrder.batch_id == batch_id))
        orders = ord_res.scalars().all()
        findings = detect_systemic_patterns_c(orders)
        candidate_groupings = [
            "Micro-orders under Rs 200 low-value floor (Rule 12)",
            "High-intent checkout carts eligible for single-nudge recovery (Rule 11)",
        ]
    else:
        # Default: Module A
        cases_res = await db.execute(select(PaymentCase).where(PaymentCase.batch_id == batch_id))
        cases = cases_res.scalars().all()
        if cases:
            case_summary = [
                {
                    "method": c.method.value if hasattr(c.method, "value") else str(c.method),
                    "classified_root_cause": c.classified_root_cause or c.failure_code or "unknown",
                    "archetype": c.classified_root_cause or c.failure_code or "unknown",
                    "time_ist": c.payment_created_at.strftime("%H:%M") if getattr(c, "payment_created_at", None) else "12:00",
                    "amount_inr": (c.amount_paise or 0) / 100,
                }
                for c in cases
            ]
            try:
                candidates = await propose_pattern_candidates(case_summary)
                candidate_groupings = candidates.candidate_groupings
            except Exception:
                candidate_groupings = [
                    "UPI failures during peak morning banking hours (10:00-13:00 IST)",
                    "Recurring mandate debit failures due to bank throttle",
                ]

            findings = detect_systemic_patterns(cases)

    narrations = []
    for f in findings:
        try:
            narration_obj = await narrate_pattern(f)
            text = narration_obj.narration
        except Exception:
            ratio = round(f.observed_share / f.expected_share_under_uniform, 1) if f.expected_share_under_uniform > 0 else 1.0
            text = f"{f.bucket_count} of {f.total_count} cases clustered in {f.grouping_description} ({ratio}x baseline anomaly)."

        excess_ratio = round(f.observed_share / f.expected_share_under_uniform, 2) if f.expected_share_under_uniform > 0 else 1.0
        narrations.append(
            {
                "module": getattr(f, "module", mod),
                "title": getattr(f, "title", "Systemic Anomaly Detected (AI Synthesis)"),
                "badge_label": getattr(f, "badge_label", "Gemini 3.6 + Deterministic Baseline"),
                "stat_badge_primary": getattr(f, "stat_badge_primary", ""),
                "stat_badge_secondary": getattr(f, "stat_badge_secondary", ""),
                "rule_enforcement_title": getattr(f, "rule_enforcement_title", "Rule Enforcement:"),
                "rule_enforcement_detail": getattr(f, "rule_enforcement_detail", ""),
                "rule_enforcement_outcome": getattr(f, "rule_enforcement_outcome", "Policy Enforced"),
                "grouping_description": f.grouping_description,
                "bucket_count": f.bucket_count,
                "total_cases_in_scope": f.total_count,
                "observed_share": round(f.observed_share, 4),
                "expected_share": round(f.expected_share_under_uniform, 4),
                "excess_ratio": excess_ratio,
                "narration": text,
            }
        )

    res_payload = {
        "batch_id": str(batch_id),
        "module": mod,
        "candidates_proposed": candidate_groupings,
        "verified_findings_count": len(findings),
        "findings": narrations,
    }
    _PATTERN_CACHE[cache_key] = res_payload
    return res_payload
