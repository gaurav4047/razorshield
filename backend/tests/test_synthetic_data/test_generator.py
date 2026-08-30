import pytest
from zoneinfo import ZoneInfo
from sqlalchemy import func, select
from app.db.models.batch import Batch
from app.db.models.invoice import Invoice
from app.db.models.order import AbandonedOrder
from app.db.models.payment_case import PaymentCase
from app.db.session import async_session_factory
from app.synthetic_data.generator import compute_floored_counts, generate_batch
from app.synthetic_data.archetypes import MODULE_A_ARCHETYPES, MODULE_B_ARCHETYPES, MODULE_C_ARCHETYPES

from datetime import timedelta, timezone
IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def test_floored_counts_algorithm():
    # Module A: 60 cases
    counts_a = compute_floored_counts(MODULE_A_ARCHETYPES, target_batch_size=60)
    assert sum(counts_a.values()) == 60
    assert counts_a["npci_window_blocked"] == 9  # 15% of 60 = 9 (>= floor 5)
    assert counts_a["gateway_sync_gap"] == 3    # 2% of 60 = 1.2 -> floored to 3
    assert counts_a["halted_subscription_unrecovered"] == 3  # 3% of 60 = 1.8 -> floored to 3
    assert counts_a["transient_infra_glitch"] == 9  # 12 absorbed surplus of 3 -> 9

    # Module B: 50 cases
    counts_b = compute_floored_counts(MODULE_B_ARCHETYPES, target_batch_size=50)
    assert sum(counts_b.values()) == 50
    assert counts_b["pays_after_reminder_1"] == 13  # 15 absorbed surplus of 2 from rounding -> 13
    assert counts_b["disputes_invoice"] == 5

    # Module C: 25 cases
    counts_c = compute_floored_counts(MODULE_C_ARCHETYPES, target_batch_size=25)
    assert sum(counts_c.values()) == 25
    assert counts_c["converts_after_nudge"] == 10
    assert counts_c["below_value_floor"] == 5


@pytest.mark.anyio
async def test_generate_batch_live_db():
    async with async_session_factory() as db:
        batch = await generate_batch(db, label="Test Synthetic Sizing Verification")
        batch_id = batch.id

    async with async_session_factory() as db:
        # Verify Module A cases
        res_a = await db.execute(
            select(PaymentCase.buyer_archetype, func.count(PaymentCase.id))
            .where(PaymentCase.batch_id == batch_id)
            .group_by(PaymentCase.buyer_archetype)
        )
        counts_a_db = dict(res_a.fetchall())
        assert sum(counts_a_db.values()) == 60
        assert counts_a_db["npci_window_blocked"] == 9
        assert counts_a_db["gateway_sync_gap"] == 3

        # Verify npci_window_blocked timestamps fall inside 10:00-13:00 IST
        npci_res = await db.execute(
            select(PaymentCase)
            .where(PaymentCase.batch_id == batch_id, PaymentCase.buyer_archetype == "npci_window_blocked")
        )
        npci_cases = npci_res.scalars().all()
        assert len(npci_cases) == 9
        for c in npci_cases:
            ist_dt = c.created_at.astimezone(IST)
            assert 10 <= ist_dt.hour < 13, f"NPCI timestamp {ist_dt} outside 10:00-13:00 IST window!"

        # Verify Module B invoices
        res_b = await db.execute(
            select(Invoice.buyer_archetype, func.count(Invoice.id))
            .where(Invoice.batch_id == batch_id)
            .group_by(Invoice.buyer_archetype)
        )
        counts_b_db = dict(res_b.fetchall())
        assert sum(counts_b_db.values()) == 50

        # Verify 15% non-MSME split (~8 out of 50)
        msme_res = await db.execute(
            select(Invoice.supplier_is_msme, func.count(Invoice.id))
            .where(Invoice.batch_id == batch_id)
            .group_by(Invoice.supplier_is_msme)
        )
        msme_counts = dict(msme_res.fetchall())
        assert msme_counts[False] == 8  # 15% of 50 = 8
        assert msme_counts[True] == 42

        # Verify Module C orders
        res_c = await db.execute(
            select(AbandonedOrder.buyer_archetype, func.count(AbandonedOrder.id))
            .where(AbandonedOrder.batch_id == batch_id)
            .group_by(AbandonedOrder.buyer_archetype)
        )
        counts_c_db = dict(res_c.fetchall())
        assert sum(counts_c_db.values()) == 25

        # Total cases in batch
        total_cases = sum(counts_a_db.values()) + sum(counts_b_db.values()) + sum(counts_c_db.values())
        assert total_cases == 135
