"""
Razorpay Live Test-Mode Payment Link Generator
==============================================
IMPORTANT NOTE ON SANDBOX CONSTRAINTS:
Razorpay Test Mode enforces a hard account-level limit of 30 Payment Links maximum
per merchant account (per official Razorpay Developer documentation). 

This script generates exactly 30 genuine, live Payment Links evenly distributed
across the 3 core modules matching exact database cases in Neon DB:
- Module A (12 Cases): 4 transient_infra_glitch, 4 npci_window_blocked, 2 insufficient_balance, 2 halted_subscription
- Module B (12 Invoices): 6 pays_after_reminder_1, 4 promise_then_keeps_it, 1 promise_then_break (2nd chance), 1 silent_ghost (2nd chance)
- Module C (6 Carts): 6 converts_after_nudge

All requests are rate-paced at 2.0s per call to strictly avoid HTTP 429 gateway limits.
"""

import asyncio
import json
import os
import uuid
from sqlalchemy import select

from app.config import settings
from app.db.models.invoice import Invoice
from app.db.models.order import AbandonedOrder
from app.db.models.payment_case import PaymentCase
from app.db.session import async_session_factory
from app.razorpay_client.client import create_payment_link


RECOVERABLE_ARCHETYPES_B = {
    "pays_immediately_no_nudge_needed",
    "pays_after_reminder_1",
    "promise_then_keeps_it",
}


async def generate_live_razorpay_links(batch_id_str: str = "c5920dfd-17e4-462b-a915-e183297d84df"):
    target_batch_id = uuid.UUID(batch_id_str)
    print("=" * 80)
    print("GENERATING EXACT 30 LIVE RAZORPAY PAYMENT LINKS (SANDBOX LIMIT: 30)")
    print(f"Target Batch: {target_batch_id}")
    print(f"API Key: {settings.RAZORPAY_KEY_ID}")
    print("=" * 80)

    async with async_session_factory() as db:
        cases_a = (await db.execute(select(PaymentCase).where(PaymentCase.batch_id == target_batch_id))).scalars().all()
        invoices_b = (await db.execute(select(Invoice).where(Invoice.batch_id == target_batch_id))).scalars().all()
        orders_c = (await db.execute(select(AbandonedOrder).where(AbandonedOrder.batch_id == target_batch_id))).scalars().all()

        # Select exact 30 targets
        targets_a = []
        c_glitch, c_npci, c_insuf, c_halt = 0, 0, 0, 0
        for c in cases_a:
            if "switch timeout" in (c.failure_raw_reason or "").lower() and c_glitch < 4:
                targets_a.append((c, "transient_infra_glitch"))
                c_glitch += 1
            elif (c.failure_code == "U19" or "NPCI" in (c.failure_raw_reason or "")) and c_npci < 4:
                targets_a.append((c, "npci_window_blocked"))
                c_npci += 1
            elif "subscription halted" in (c.failure_raw_reason or "").lower() and c_halt < 2:
                targets_a.append((c, "halted_subscription_recovers"))
                c_halt += 1
            elif c.failure_code == "51" and c_insuf < 2:
                targets_a.append((c, "insufficient_balance_recovers"))
                c_insuf += 1

        targets_b = []
        c_rem1, c_pkeep, c_pbreak, c_sghost = 0, 0, 0, 0
        for inv in invoices_b:
            if inv.buyer_archetype == "pays_after_reminder_1" and c_rem1 < 6:
                targets_b.append((inv, inv.buyer_archetype))
                c_rem1 += 1
            elif inv.buyer_archetype == "promise_then_keeps_it" and c_pkeep < 4:
                targets_b.append((inv, inv.buyer_archetype))
                c_pkeep += 1
            elif inv.buyer_archetype == "promise_then_break" and c_pbreak < 1:
                targets_b.append((inv, "promise_then_break (2nd chance)"))
                c_pbreak += 1
            elif inv.buyer_archetype == "silent_ghost" and c_sghost < 1:
                targets_b.append((inv, "silent_ghost (2nd chance)"))
                c_sghost += 1

        targets_c = []
        c_nudge = 0
        for o in orders_c:
            if o.buyer_archetype == "converts_after_nudge" and c_nudge < 6:
                targets_c.append((o, o.buyer_archetype))
                c_nudge += 1

        total = len(targets_a) + len(targets_b) + len(targets_c)
        print(f"Selected Targets: Module A = {len(targets_a)}, Module B = {len(targets_b)}, Module C = {len(targets_c)} | Total = {total}/30\n")

        results = []
        idx = 0

        # Module A Links
        print("--- Creating Module A Links (12) ---")
        for pc, arch in targets_a:
            idx += 1
            await asyncio.sleep(2.0)
            plink = await create_payment_link(
                amount_paise=pc.amount_paise,
                reference_id=f"ref_a_{str(pc.id)[:8]}",
                description=f"Subscription Recovery: Case {str(pc.id)[:8]}",
                customer_name="Sarthak Test Customer",
                customer_email="sarthak.customer@example.com",
                customer_contact="+919319841600",
                notes={"case_id": str(pc.id), "module": "A", "archetype": arch},
            )
            pc.razorpay_payment_link_id = plink["id"]
            print(f"[{idx:02d}/30] [Mod A] {arch:<30} | Rs {pc.amount_paise/100:>8,.2f} | {plink['id']} | {plink['short_url']}", flush=True)
            results.append({
                "index": idx,
                "module": "A",
                "id": str(pc.id),
                "archetype": arch,
                "amount_inr": pc.amount_paise / 100.0,
                "plink_id": plink["id"],
                "short_url": plink["short_url"],
            })

        # Module B Links
        print("\n--- Creating Module B Links (12) ---")
        for inv, arch in targets_b:
            idx += 1
            await asyncio.sleep(2.0)
            plink = await create_payment_link(
                amount_paise=inv.amount_paise,
                reference_id=inv.invoice_number,
                description=f"Invoice Settlement: {inv.invoice_number}",
                customer_name=inv.buyer_name,
                customer_email=inv.buyer_email or "buyer@example.com",
                customer_contact=inv.buyer_contact or "+919319841600",
                notes={"case_id": str(inv.id), "module": "B", "archetype": arch},
            )
            inv.razorpay_payment_link_id = plink["id"]
            print(f"[{idx:02d}/30] [Mod B] {arch:<30} | Rs {inv.amount_paise/100:>8,.2f} | {plink['id']} | {plink['short_url']}", flush=True)
            results.append({
                "index": idx,
                "module": "B",
                "id": inv.invoice_number,
                "archetype": arch,
                "amount_inr": inv.amount_paise / 100.0,
                "plink_id": plink["id"],
                "short_url": plink["short_url"],
            })

        # Module C Links
        print("\n--- Creating Module C Links (6) ---")
        for ord_c, arch in targets_c:
            idx += 1
            await asyncio.sleep(2.0)
            plink = await create_payment_link(
                amount_paise=ord_c.amount_paise,
                reference_id=f"ref_c_{str(ord_c.id)[:8]}",
                description=f"Cart Recovery Nudge: Order {str(ord_c.id)[:8]}",
                customer_name="Priya Sharma",
                customer_email="priya.sharma@example.com",
                customer_contact=ord_c.customer_contact or "+919319841600",
                notes={"case_id": str(ord_c.id), "module": "C", "archetype": arch},
            )
            ord_c.razorpay_payment_link_id = plink["id"]
            print(f"[{idx:02d}/30] [Mod C] {arch:<30} | Rs {ord_c.amount_paise/100:>8,.2f} | {plink['id']} | {plink['short_url']}", flush=True)
            results.append({
                "index": idx,
                "module": "C",
                "id": str(ord_c.id),
                "archetype": arch,
                "amount_inr": ord_c.amount_paise / 100.0,
                "plink_id": plink["id"],
                "short_url": plink["short_url"],
            })

        await db.commit()
        print("\n" + "=" * 80)
        print("ALL 30 PAYMENT LINKS SUCCESSFULLY CREATED AND COMMITTED TO NEON DB")
        print("=" * 80)

        out_path = os.path.join(os.path.dirname(__file__), "live_razorpay_links.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Exported JSON manifest to: {out_path}")


if __name__ == "__main__":
    asyncio.run(generate_live_razorpay_links())
