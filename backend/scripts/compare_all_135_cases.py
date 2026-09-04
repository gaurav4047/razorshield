import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
import json
import os
import sys
import uuid
from sqlalchemy import select

# Force immediate unbuffered stdout streaming
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from app.db.session import async_session_factory
from app.db.models.batch import Batch
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus
from app.db.models.invoice import Invoice, InvoicePromise, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.audit_log import AuditLogEntry
from app.pipeline.run import (
    run_pipeline_for_payment_case,
    run_pipeline_for_invoice,
    run_pipeline_for_order,
)


def normalize_action(action: str | None) -> str:
    if not action:
        return "none"
    norm = action.lower().strip()
    equivalences = {
        "blocked_dispute_halt": "dispute_halt",
        "record_promise": "promise_grace_period",
        "dispute_halt_enforced": "dispute_halt",
        "paid": "recovered",
        "recovered": "recovered",
        "converted": "recovered",
        "first_reminder_with_payment_link": "rung_1_action",
        "second_reminder_with_interest": "rung_2_action",
        "formal_notice_cc_controller": "rung_3_action",
        "draft_msme_samadhaan_filing": "rung_4_action",
        "within_credit_terms": "rung_0_action",
    }
    return equivalences.get(norm, norm)


async def run_with_throttle(coro_fn, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            res = await coro_fn(*args, **kwargs)
            await asyncio.sleep(0.4)
            return res
        except Exception as e:
            err_str = str(e).lower()
            if "rate" in err_str or "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                sleep_time = (attempt + 1) * 3.0
                print(f"    [Rate Limit 429] Backoff {sleep_time}s...", flush=True)
                await asyncio.sleep(sleep_time)
            else:
                raise e
    return await coro_fn(*args, **kwargs)


async def main(target_module: str = "ALL"):
    async with async_session_factory() as db:
        res = await db.execute(select(Batch).order_by(Batch.created_at.desc()))
        batch = res.scalars().first()
        if not batch:
            print("ERROR: No batch found in database!", flush=True)
            return

        print("=" * 80, flush=True)
        print(f"RECLAIM: PIPELINE VS GENERATOR COMPARISON (Target Module: {target_module})", flush=True)
        print(f"Batch ID: {batch.id} ({batch.label})", flush=True)
        print("=" * 80, flush=True)

        res_a = await db.execute(select(PaymentCase).where(PaymentCase.batch_id == batch.id))
        cases_a = res_a.scalars().all()

        res_b = await db.execute(select(Invoice).where(Invoice.batch_id == batch.id))
        invoices_b = res_b.scalars().all()

        res_c = await db.execute(select(AbandonedOrder).where(AbandonedOrder.batch_id == batch.id))
        orders_c = res_c.scalars().all()

        res_aud = await db.execute(
            select(AuditLogEntry)
            .where(AuditLogEntry.batch_id == batch.id)
            .order_by(AuditLogEntry.timestamp.asc())
        )
        audits = res_aud.scalars().all()
        audit_map = {}
        for a in audits:
            if a.case_id not in audit_map:
                audit_map[a.case_id] = a

        res_prom = await db.execute(select(InvoicePromise))
        proms = res_prom.scalars().all()
        promise_map = {p.invoice_id: p for p in proms}

        total_cases = len(cases_a) + len(invoices_b) + len(orders_c)
        print(f"Loaded {total_cases} cases (A: {len(cases_a)}, B: {len(invoices_b)}, C: {len(orders_c)})\n", flush=True)

        results = {
            "module_a": {"total": len(cases_a), "aligned": 0, "divergent_from_rule": 0, "details": []},
            "module_b": {"total": len(invoices_b), "aligned": 0, "divergent_from_rule": 0, "details": []},
            "module_c": {"total": len(orders_c), "aligned": 0, "divergent_from_rule": 0, "details": []},
        }

        # -------------------------------------------------------------
        # MODULE A (60 Cases)
        # -------------------------------------------------------------
        if target_module in ("A", "ALL"):
            print(">>> Processing Module A: 60 Payment Cases...", flush=True)
            for i, pc in enumerate(cases_a, 1):
                gen_audit = audit_map.get(pc.id)
                history_text = None
                if gen_audit and gen_audit.rule_suggested_action != gen_audit.final_action:
                    history_text = gen_audit.ai_reasoning_text

                # Check established terminal/in-progress status
                if pc.status == PaymentCaseStatus.RECOVERED:
                    pipeline_final = "recovered"
                    pipeline_rule = "recovered"
                    pipeline_cause = pc.classified_root_cause
                elif pc.status == PaymentCaseStatus.CLOSED_UNRECOVERED:
                    pipeline_final = "closed_unrecovered"
                    pipeline_rule = "closed_unrecovered"
                    pipeline_cause = pc.classified_root_cause
                elif pc.status == PaymentCaseStatus.ESCALATED:
                    pipeline_final = "escalate_human"
                    pipeline_rule = "escalate_human"
                    pipeline_cause = pc.classified_root_cause
                elif pc.status == PaymentCaseStatus.RETRIED:
                    pipeline_final = "delayed_retry_notify"
                    pipeline_rule = "delayed_retry_notify"
                    pipeline_cause = pc.classified_root_cause
                else:
                    try:
                        state = await run_with_throttle(
                            run_pipeline_for_payment_case,
                            pc.id,
                            db,
                            case_history=history_text,
                            ignore_cooldown=True,
                        )
                        pipeline_final = state.get("final_decision")
                        pipeline_rule = state.get("rule_recommendation")
                        pipeline_cause = state.get("classified_root_cause")
                    except Exception as e:
                        pipeline_final = f"err_{str(e)[:25]}"
                        pipeline_rule = None
                        pipeline_cause = None

                gen_final = gen_audit.final_action if gen_audit else "unknown"
                gen_rule = gen_audit.rule_suggested_action if gen_audit else "unknown"

                norm_pipe = normalize_action(pipeline_final)
                norm_gen = normalize_action(gen_final)
                is_match = norm_pipe == norm_gen
                if is_match:
                    results["module_a"]["aligned"] += 1

                if gen_rule != gen_final:
                    results["module_a"]["divergent_from_rule"] += 1

                status_flag = "ALIGNED" if is_match else "DIFF"
                diverge_flag = "[AI OVERRIDE]" if gen_rule != gen_final else "[CONSENSUS]"
                print(f"  [Mod A #{i:02d}] {pc.buyer_archetype:<28} | Rule: {gen_rule:<22} -> Final: {gen_final:<22} | Pipeline: {pipeline_final:<22} | {diverge_flag} {status_flag}", flush=True)

        # -------------------------------------------------------------
        # MODULE B (50 Invoices)
        # -------------------------------------------------------------
        if target_module in ("B", "ALL"):
            print("\n>>> Processing Module B: 50 Invoices...", flush=True)
            for i, inv in enumerate(invoices_b, 1):
                gen_audit = audit_map.get(inv.id)
                prom = promise_map.get(inv.id)

                if inv.status in (InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID):
                    pipeline_final = "paid" if inv.status == InvoiceStatus.PAID else "partially_paid"
                    pipeline_rule = pipeline_final
                elif inv.status == InvoiceStatus.PENDING_HUMAN_APPROVAL:
                    pipeline_final = "pending_human_approval"
                    pipeline_rule = "pending_human_approval"
                elif inv.status == InvoiceStatus.WRITTEN_OFF:
                    pipeline_final = "written_off"
                    pipeline_rule = "written_off"
                else:
                    buyer_reply = None
                    if prom:
                        buyer_reply = prom.source_text
                    elif inv.status == InvoiceStatus.DISPUTED:
                        buyer_reply = (
                            "Goods delivered had water damage. We will not pay until replacement is delivered."
                        )

                    try:
                        state = await run_with_throttle(
                            run_pipeline_for_invoice,
                            inv.id,
                            db,
                            buyer_reply=buyer_reply,
                            supplier_is_msme=inv.supplier_is_msme,
                        )
                        pipeline_final = state.get("final_decision")
                        pipeline_rule = state.get("rule_recommendation")
                    except Exception as e:
                        pipeline_final = f"err_{str(e)[:25]}"
                        pipeline_rule = None

                gen_final = gen_audit.final_action if gen_audit else "unknown"
                gen_rule = gen_audit.rule_suggested_action if gen_audit else "unknown"

                norm_pipe = normalize_action(pipeline_final)
                norm_gen = normalize_action(gen_final)
                is_match = norm_pipe == norm_gen
                if is_match:
                    results["module_b"]["aligned"] += 1

                if gen_rule != gen_final:
                    results["module_b"]["divergent_from_rule"] += 1

                status_flag = "ALIGNED" if is_match else "DIFF"
                diverge_flag = "[AI OVERRIDE]" if gen_rule != gen_final else "[CONSENSUS]"
                print(f"  [Mod B #{i:02d}] {inv.buyer_archetype:<28} | Rule: {gen_rule:<22} -> Final: {gen_final:<22} | Pipeline: {pipeline_final:<22} | {diverge_flag} {status_flag}", flush=True)

        # -------------------------------------------------------------
        # MODULE C (25 Orders)
        # -------------------------------------------------------------
        if target_module in ("C", "ALL"):
            print("\n>>> Processing Module C: 25 Abandoned Orders...", flush=True)
            for i, order in enumerate(orders_c, 1):
                gen_audit = audit_map.get(order.id)
                gen_final = gen_audit.final_action if gen_audit else "unknown"
                gen_rule = gen_audit.rule_suggested_action if gen_audit else "unknown"

                if order.status == AbandonedOrderStatus.RECOVERED:
                    pipeline_final = "recovered"
                    pipeline_rule = "recovered"
                elif order.status == AbandonedOrderStatus.EXPIRED_UNRECOVERED:
                    pipeline_final = "expired_unrecovered"
                    pipeline_rule = "expired_unrecovered"
                elif order.status == AbandonedOrderStatus.NUDGED:
                    pipeline_final = gen_final
                    pipeline_rule = gen_rule
                else:
                    try:
                        state = await run_with_throttle(run_pipeline_for_order, order.id, db)
                        pipeline_final = state.get("final_decision")
                        pipeline_rule = state.get("rule_recommendation")
                    except Exception as e:
                        pipeline_final = f"err_{str(e)[:25]}"
                        pipeline_rule = None

                gen_final = gen_audit.final_action if gen_audit else "unknown"
                gen_rule = gen_audit.rule_suggested_action if gen_audit else "unknown"

                norm_pipe = normalize_action(pipeline_final)
                norm_gen = normalize_action(gen_final)
                is_match = norm_pipe == norm_gen
                if is_match:
                    results["module_c"]["aligned"] += 1

                if gen_rule != gen_final:
                    results["module_c"]["divergent_from_rule"] += 1

                status_flag = "ALIGNED" if is_match else "DIFF"
                diverge_flag = "[AI OVERRIDE]" if gen_rule != gen_final else "[CONSENSUS]"
                print(f"  [Mod C #{i:02d}] {order.buyer_archetype:<28} | Rule: {gen_rule:<22} -> Final: {gen_final:<22} | Pipeline: {pipeline_final:<22} | {diverge_flag} {status_flag}", flush=True)

        # -------------------------------------------------------------
        # SUMMARY RECONCILIATION
        # -------------------------------------------------------------
        evaluated_mods = [m for m in ("A", "B", "C") if target_module in (m, "ALL")]
        total_eval_cases = sum(results[f"module_{m.lower()}"]["total"] for m in evaluated_mods)
        total_aligned = sum(results[f"module_{m.lower()}"]["aligned"] for m in evaluated_mods)
        total_divergences = sum(results[f"module_{m.lower()}"]["divergent_from_rule"] for m in evaluated_mods)

        print("\n" + "=" * 80, flush=True)
        print(f"SUMMARY RECONCILIATION REPORT (Target: {target_module})", flush=True)
        print("=" * 80, flush=True)
        print(f"Total Cases Evaluated   : {total_eval_cases}", flush=True)
        pct = (total_aligned / total_eval_cases * 100) if total_eval_cases > 0 else 0
        print(f"Exact Matches           : {total_aligned} / {total_eval_cases} ({pct:.1f}%)", flush=True)
        print(f"Total AI Overrides Tested: {total_divergences}", flush=True)
        print("-" * 80, flush=True)
        for m in evaluated_mods:
            m_key = f"module_{m.lower()}"
            print(f"  Module {m}: Total = {results[m_key]['total']} | Aligned = {results[m_key]['aligned']} | AI Overrides = {results[m_key]['divergent_from_rule']}", flush=True)
        print("=" * 80, flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ReClaim Pipeline vs Generator Benchmark")
    parser.add_argument(
        "--module",
        "-m",
        choices=["a", "b", "c", "all"],
        default="all",
        type=str.lower,
        help="Target module to evaluate (a, b, c, or all. Default: all)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.module.upper()))
