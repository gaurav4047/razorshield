from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import random
import uuid
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.batch import Batch
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.payment_case import (
    PaymentCase,
    PaymentCaseStatus,
    PaymentContext,
    PaymentMethod,
    SubscriptionState,
)
from app.domain_logic.msmed import compute_statutory_due_date
from app.synthetic_data.archetypes import (
    MODULE_A_ARCHETYPES,
    MODULE_B_ARCHETYPES,
    MODULE_C_ARCHETYPES,
    ArchetypeDefinition,
)

IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def compute_floored_counts(
    archetypes: dict[str, ArchetypeDefinition],
    target_batch_size: int,
) -> dict[str, int]:
    # 1. Raw count based on percentage
    raw_counts = {
        name: round((arch.share_percentage / 100.0) * target_batch_size)
        for name, arch in archetypes.items()
    }

    # 2. Apply floors (min_floor is 3 generally, 5 for npci_window_blocked)
    floored_counts = {
        name: max(raw_counts[name], arch.min_floor)
        for name, arch in archetypes.items()
    }

    # 3. Rebalance surplus/deficit against largest unfloored archetypes
    total = sum(floored_counts.values())
    diff = total - target_batch_size

    if diff > 0:
        while diff > 0:
            candidates = [
                name for name, arch in archetypes.items()
                if floored_counts[name] > arch.min_floor
            ]
            if not candidates:
                break
            max_val = max(floored_counts[c] for c in candidates)
            largest_candidates = [c for c in candidates if floored_counts[c] == max_val]
            for c in largest_candidates:
                if diff > 0 and floored_counts[c] > archetypes[c].min_floor:
                    floored_counts[c] -= 1
                    diff -= 1

    elif diff < 0:
        # Add remainder to largest archetypes
        sorted_names = sorted(archetypes.keys(), key=lambda n: floored_counts[n], reverse=True)
        idx = 0
        while diff < 0:
            floored_counts[sorted_names[idx % len(sorted_names)]] += 1
            diff += 1
            idx += 1

    return floored_counts


def generate_module_a_cases(batch_id: uuid.UUID, counts: dict[str, int], now_dt: datetime) -> list[PaymentCase]:
    cases: list[PaymentCase] = []

    for archetype_name, count in counts.items():
        for i in range(count):
            case_uuid = uuid.uuid4()
            razorpay_id = f"pay_syn_{case_uuid.hex[:8]}"

            # Timestamps per 06_synthetic_data.md §1 & §3
            if archetype_name == "npci_window_blocked":
                # Deliberately falls inside 10:00-13:00 IST
                days_ago = random.randint(0, 2)
                base_day = (now_dt.astimezone(IST) - timedelta(days=days_ago)).date()
                hour_ist = random.randint(10, 12)
                minute_ist = random.randint(0, 59)
                created_at = datetime(
                    base_day.year, base_day.month, base_day.day,
                    hour_ist, minute_ist, random.randint(0, 59),
                    tzinfo=IST
                ).astimezone(timezone.utc)
            else:
                # Uniformly random across past 24-48 hours
                seconds_ago = random.randint(300, 48 * 3600)
                created_at = now_dt - timedelta(seconds=seconds_ago)

            method = PaymentMethod.UPI
            context = PaymentContext.ONE_TIME
            amount_paise = random.randint(50000, 500000)
            failure_code = None
            raw_reason = "Transaction failed"
            sub_state = None

            if archetype_name == "transient_infra_glitch":
                method = random.choice([PaymentMethod.UPI, PaymentMethod.CARD, PaymentMethod.NETBANKING])
                context = PaymentContext.ONE_TIME
                failure_code = "91" if method == PaymentMethod.CARD else None
                raw_reason = "Issuer switch timeout / bank server temporarily inoperative"

            elif archetype_name == "npci_window_blocked":
                method = PaymentMethod.UPI
                context = PaymentContext.SUBSCRIPTION
                failure_code = "U19"
                raw_reason = "NPCI AutoPay mandate execution blocked during peak banking window"

            elif archetype_name in ("insufficient_balance_recovers", "insufficient_balance_persists"):
                method = random.choice([PaymentMethod.UPI, PaymentMethod.NETBANKING])
                context = PaymentContext.ONE_TIME
                failure_code = "51"
                raw_reason = "Customer account balance insufficient to complete debit"

            elif archetype_name == "hard_decline_card":
                method = PaymentMethod.CARD
                context = PaymentContext.SUBSCRIPTION
                failure_code = "54"
                raw_reason = "Card validity expired"

            elif archetype_name == "wallet_kyc_frozen":
                method = PaymentMethod.WALLET
                context = PaymentContext.ONE_TIME
                failure_code = None
                raw_reason = "Wallet minimum KYC lapsed, balance freeze active"

            elif archetype_name == "emi_ineligible":
                method = PaymentMethod.EMI
                context = PaymentContext.ONE_TIME
                failure_code = None
                raw_reason = "Card not eligible for instant EMI facility"

            elif archetype_name == "halted_subscription_recovers":
                method = PaymentMethod.CARD
                context = PaymentContext.SUBSCRIPTION
                sub_state = SubscriptionState.HALTED
                failure_code = "54"
                raw_reason = "Subscription halted after card expiry"

            elif archetype_name == "halted_subscription_unrecovered":
                method = PaymentMethod.CARD
                context = PaymentContext.SUBSCRIPTION
                sub_state = SubscriptionState.HALTED
                failure_code = "05"
                raw_reason = "Subscription halted after repeated bank declines"

            elif archetype_name == "gateway_sync_gap":
                method = PaymentMethod.NETBANKING
                context = PaymentContext.ONE_TIME
                failure_code = None
                raw_reason = "Gateway data sync gap: debited at bank but reconciliation pending"

            case = PaymentCase(
                id=case_uuid,
                batch_id=batch_id,
                razorpay_payment_id=razorpay_id,
                method=method,
                context=context,
                amount_paise=amount_paise,
                failure_code=failure_code,
                failure_raw_reason=raw_reason,
                attempt_number=1,
                retry_count=0,
                status=PaymentCaseStatus.OPEN,
                subscription_state=sub_state,
                buyer_archetype=archetype_name,
                created_at=created_at,
            )
            cases.append(case)

    return cases


def generate_module_b_invoices(batch_id: uuid.UUID, counts: dict[str, int], now_dt: datetime) -> list[Invoice]:
    invoices: list[Invoice] = []
    today = now_dt.date()

    company_names = [
        "Alpha Systems Pvt Ltd", "Zenith Technologies", "Vortex Manufacturing",
        "Apex Logistics", "Nova Healthcare", "Starlight Textiles",
        "Pinnacle Automotives", "Horizon Agro Foods", "Trident Chemicals",
        "Astra Consumer Goods", "Evergreen Retailers", "Solarium Solar",
    ]

    all_archetypes: list[str] = []
    for arch_name, cnt in counts.items():
        all_archetypes.extend([arch_name] * cnt)

    # 15% non-MSME split per 06_synthetic_data.md §4 (e.g. ~8 out of 50)
    total_invoices = len(all_archetypes)
    non_msme_count = round(total_invoices * 0.15)
    is_msme_flags = [False] * non_msme_count + [True] * (total_invoices - non_msme_count)
    random.shuffle(is_msme_flags)

    for i, archetype_name in enumerate(all_archetypes):
        inv_uuid = uuid.uuid4()
        supplier_is_msme = is_msme_flags[i]
        has_agreement = True
        company = random.choice(company_names)

        # Backdate goods_accepted_date per archetype to position realistically on ladder
        if archetype_name == "pays_immediately_no_nudge_needed":
            goods_date = today - timedelta(days=10)
        elif archetype_name == "pays_after_reminder_1":
            goods_date = today - timedelta(days=48)  # statutory due date reached ~3 days ago (Rung 1)
        elif archetype_name in ("promise_then_keeps_it", "promise_then_break", "disputes_invoice", "partial_payer"):
            goods_date = today - timedelta(days=55)  # overdue ~10 days (Rung 2)
        elif archetype_name == "silent_ghost":
            goods_date = today - timedelta(days=78)  # overdue ~33 days (Rung 4)
        else:
            goods_date = today - timedelta(days=random.randint(46, 60))

        invoice_date = goods_date

        if supplier_is_msme:
            statutory_due_date = compute_statutory_due_date(goods_date, has_written_agreement=has_agreement)
        else:
            statutory_due_date = invoice_date + timedelta(days=30)

        amount_paise = random.randint(1000000, 25000000)  # Rs 10,000 to Rs 2,50,000

        current_rung = 0
        status = InvoiceStatus.PENDING
        broken_promises = 0

        if archetype_name == "silent_ghost":
            current_rung = 3
            status = InvoiceStatus.OVERDUE
        elif archetype_name == "promise_then_break":
            current_rung = 2
            status = InvoiceStatus.OVERDUE
            broken_promises = random.randint(1, 3)
        elif goods_date < (today - timedelta(days=45)):
            current_rung = 1
            status = InvoiceStatus.OVERDUE

        invoice = Invoice(
            id=inv_uuid,
            batch_id=batch_id,
            invoice_number=f"INV-{today.year}-{i+1:04d}",
            buyer_name=company,
            buyer_contact=f"+9198{random.randint(10000000, 99999999)}",
            buyer_email=f"accounts@{company.lower().replace(' ', '')[:10]}.com",
            supplier_is_msme=supplier_is_msme,
            has_written_agreement=has_agreement,
            amount_paise=amount_paise,
            amount_paid_paise=0,
            currency="INR",
            invoice_date=invoice_date,
            goods_accepted_date=goods_date,
            statutory_due_date=statutory_due_date,
            status=status,
            current_rung=current_rung,
            dispute_flag=False,
            broken_promise_count=broken_promises,
            buyer_archetype=archetype_name,
        )
        invoices.append(invoice)

    return invoices


def generate_module_c_orders(batch_id: uuid.UUID, counts: dict[str, int], now_dt: datetime) -> list[AbandonedOrder]:
    orders: list[AbandonedOrder] = []

    all_archetypes: list[str] = []
    for arch_name, cnt in counts.items():
        all_archetypes.extend([arch_name] * cnt)

    for i, archetype_name in enumerate(all_archetypes):
        order_uuid = uuid.uuid4()
        rzp_order_id = f"order_syn_{order_uuid.hex[:8]}"

        # Backdated by 30-120 minutes per 06 §1
        minutes_ago = random.randint(35, 120)
        order_created_at = now_dt - timedelta(minutes=minutes_ago)

        if archetype_name == "below_value_floor":
            amount_paise = random.randint(5000, 19000)  # Rs 50 to Rs 190 (< Rs 200)
        else:
            amount_paise = random.randint(25000, 500000)  # Rs 250 to Rs 5,000

        order = AbandonedOrder(
            id=order_uuid,
            batch_id=batch_id,
            razorpay_order_id=rzp_order_id,
            customer_name=f"Customer {i+1}",
            customer_contact=f"+9197{random.randint(10000000, 99999999)}",
            customer_email=f"cust{i+1}@example.com",
            amount_paise=amount_paise,
            order_created_at=order_created_at,
            status=AbandonedOrderStatus.OPEN,
            nudge_sent=False,
            buyer_archetype=archetype_name,
        )
        orders.append(order)

    return orders


async def generate_batch(db: AsyncSession, label: str | None = None, seed: int | None = None) -> Batch:
    if seed is not None:
        random.seed(seed)
    now_dt = datetime.now(timezone.utc)
    batch_label = label or f"Demo Batch {now_dt.strftime('%Y-%m-%d %H:%M:%S')}"

    batch = Batch(
        label=batch_label,
        description="Synthetic demo batch: 60 Module A, 50 Module B, 25 Module C cases",
    )
    db.add(batch)
    await db.flush()

    counts_a = compute_floored_counts(MODULE_A_ARCHETYPES, target_batch_size=60)
    counts_b = compute_floored_counts(MODULE_B_ARCHETYPES, target_batch_size=50)
    counts_c = compute_floored_counts(MODULE_C_ARCHETYPES, target_batch_size=25)

    cases_a = generate_module_a_cases(batch.id, counts_a, now_dt)
    invoices_b = generate_module_b_invoices(batch.id, counts_b, now_dt)
    orders_c = generate_module_c_orders(batch.id, counts_c, now_dt)

    db.add_all(cases_a)
    db.add_all(invoices_b)
    db.add_all(orders_c)

    await db.commit()
    await db.refresh(batch)

    return batch
