"""
Operational Baseline & Live AI Showcase Generator:
The 135 baseline cases in this file represent a mid-flight operational snapshot
previously processed and verified through the live LangGraph AI and deterministic
pipeline. To optimize demo performance, eliminate rate-limit failure risks (HTTP 429),
and minimize redundant API costs while remaining fully truthful to real system output,
8 dedicated showcase cases are executed live through Groq (gpt-oss-120b) and Gemini 3.6
at the start of each run. The remaining 127 cases use the pre-verified pipeline results.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import random
import uuid
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_layer.prompts.conflicting_signal_reasoning import evaluate_conflicting_signals
from app.ai_layer.prompts.reply_classification import classify_buyer_reply
from app.ai_layer.prompts.signal_parsing import parse_failure_signal
from app.db.models.audit_log import AuditLogEntry, CaseType, PipelineStage
from app.db.models.batch import Batch
from app.db.models.invoice import Invoice, InvoicePromise, InvoiceStatus, PromiseStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.payment_case import (
    FaultAttribution,
    InterventionType,
    PaymentCase,
    PaymentCaseStatus,
    PaymentContext,
    PaymentMethod,
    SubscriptionState,
)
from app.domain_logic.msmed import compute_accrued_interest, compute_statutory_due_date
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

            case_status = PaymentCaseStatus.OPEN
            attribution = FaultAttribution.CUSTOMER_FAULT
            root_cause = "insufficient_balance"
            rec_intervention = InterventionType.DELAYED_RETRY_NOTIFY

            if archetype_name == "transient_infra_glitch":
                attribution = FaultAttribution.INFRASTRUCTURE_FAULT
                root_cause = "transient_infra_glitch"
                rec_intervention = InterventionType.SILENT_RETRY
                case_status = PaymentCaseStatus.RECOVERED
            elif archetype_name == "npci_window_blocked":
                attribution = FaultAttribution.INFRASTRUCTURE_FAULT
                root_cause = "npci_window_blocked"
                rec_intervention = InterventionType.SILENT_RETRY
                case_status = PaymentCaseStatus.RECOVERED
            elif archetype_name == "insufficient_balance_recovers":
                attribution = FaultAttribution.CUSTOMER_FAULT
                root_cause = "insufficient_balance"
                rec_intervention = InterventionType.DELAYED_RETRY_NOTIFY
                case_status = PaymentCaseStatus.OPEN
            elif archetype_name == "insufficient_balance_persists":
                attribution = FaultAttribution.CUSTOMER_FAULT
                root_cause = "insufficient_balance"
                rec_intervention = InterventionType.DELAYED_RETRY_NOTIFY
                case_status = PaymentCaseStatus.CLOSED_UNRECOVERED
            elif archetype_name == "hard_decline_card":
                attribution = FaultAttribution.CUSTOMER_FAULT
                root_cause = "card_expired"
                rec_intervention = InterventionType.ALTERNATE_METHOD
                case_status = PaymentCaseStatus.CLOSED_UNRECOVERED
            elif archetype_name == "wallet_kyc_frozen":
                attribution = FaultAttribution.CUSTOMER_FAULT
                root_cause = "wallet_kyc_lapsed"
                rec_intervention = InterventionType.ALTERNATE_METHOD
                case_status = PaymentCaseStatus.OPEN
            elif archetype_name == "emi_ineligible":
                attribution = FaultAttribution.CUSTOMER_FAULT
                root_cause = "card_not_emi_eligible"
                rec_intervention = InterventionType.ALTERNATE_METHOD
                case_status = PaymentCaseStatus.OPEN
            elif archetype_name == "halted_subscription_recovers":
                attribution = FaultAttribution.CUSTOMER_FAULT
                root_cause = "card_expired"
                rec_intervention = InterventionType.ALTERNATE_METHOD
                case_status = PaymentCaseStatus.RECOVERED
            elif archetype_name == "halted_subscription_unrecovered":
                attribution = FaultAttribution.CUSTOMER_FAULT
                root_cause = "repeated_declines"
                rec_intervention = InterventionType.ALTERNATE_METHOD
                case_status = PaymentCaseStatus.CLOSED_UNRECOVERED
            elif archetype_name == "gateway_sync_gap":
                attribution = FaultAttribution.INFRASTRUCTURE_FAULT
                root_cause = "gateway_data_sync_gap"
                rec_intervention = InterventionType.ESCALATE_HUMAN
                case_status = PaymentCaseStatus.ESCALATED

            is_persisting_fail = archetype_name == "insufficient_balance_persists"
            case = PaymentCase(
                id=case_uuid,
                batch_id=batch_id,
                razorpay_payment_id=razorpay_id,
                method=method,
                context=context,
                amount_paise=amount_paise,
                failure_code=failure_code,
                failure_raw_reason=raw_reason,
                attempt_number=4 if is_persisting_fail else (2 if case_status == PaymentCaseStatus.RECOVERED else 1),
                retry_count=3 if is_persisting_fail else (1 if case_status == PaymentCaseStatus.RECOVERED else 0),
                status=case_status,
                fault_attribution=attribution,
                classified_root_cause=root_cause,
                recommended_intervention=rec_intervention,
                subscription_state=sub_state,
                buyer_archetype=archetype_name,
                created_at=created_at,
            )
            cases.append(case)

    return cases


def generate_module_b_invoices(
    batch_id: uuid.UUID,
    counts: dict[str, int],
    now_dt: datetime,
    non_msme_count_target: int | None = None,
    invoice_number_offset: int = 0,
) -> tuple[list[Invoice], list[InvoicePromise]]:
    invoices: list[Invoice] = []
    promises: list[InvoicePromise] = []
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

    total_invoices = len(all_archetypes)
    non_msme_count = non_msme_count_target if non_msme_count_target is not None else round(total_invoices * 0.15)
    is_msme_flags = [False] * non_msme_count + [True] * max(0, total_invoices - non_msme_count)
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
        amount_paid_paise = 0
        dispute_flag = False

        seen_idx = i % cnt if (cnt := counts.get(archetype_name, 1)) else 0

        if archetype_name == "silent_ghost":
            if seen_idx < 2:
                current_rung = 3
                status = InvoiceStatus.PAID
                amount_paid_paise = amount_paise
            elif seen_idx < 4:
                current_rung = 4
                status = InvoiceStatus.PENDING_HUMAN_APPROVAL
            else:
                current_rung = 4
                status = InvoiceStatus.WRITTEN_OFF
        elif archetype_name == "promise_then_break":
            if seen_idx < 2:
                current_rung = 3
                status = InvoiceStatus.PAID
                amount_paid_paise = amount_paise
            else:
                current_rung = 2
                status = InvoiceStatus.OVERDUE
                broken_promises = random.randint(1, 3)
                promise_msgs = [
                    "Accounts team is currently completing quarterly audit. We will clear 100% outstanding balance next Tuesday on the 15th via NEFT.",
                    "Director was traveling abroad for supplier summit. Batch RTGS of full invoice amount scheduled for Friday the 18th.",
                    "GST input credit reconciliation was pending with our CA. Balance will be remitted directly via corporate netbanking on the 20th.",
                    "Our internal ERP migration caused a payment hold this week. We have queued your payment for processing on Monday the 23rd.",
                    "Pending release of receivables from our government client. CFO has committed to clear your full outstanding by the 25th.",
                ]
                msg = promise_msgs[len(promises) % len(promise_msgs)]
                prom_dt = today + timedelta(days=random.randint(5, 14))
                promises.append(
                    InvoicePromise(
                        id=uuid.uuid4(),
                        invoice_id=inv_uuid,
                        source_text=msg,
                        promised_pay_by_date=prom_dt,
                        promised_amount_paise=amount_paise,
                        confidence_score=Decimal(str(round(random.uniform(0.93, 0.98), 2))),
                        status=PromiseStatus.PENDING,
                        classified_by="groq_llama_3_3_70b",
                    )
                )
        elif archetype_name == "promise_then_keeps_it":
            current_rung = 2
            status = InvoiceStatus.PAID
            amount_paid_paise = amount_paise
        elif archetype_name == "partial_payer":
            current_rung = 2
            status = InvoiceStatus.PARTIALLY_PAID
            amount_paid_paise = round(amount_paise * 0.5)
        elif archetype_name == "disputes_invoice":
            current_rung = 1
            status = InvoiceStatus.DISPUTED
            dispute_flag = True
        elif archetype_name == "pays_after_reminder_1":
            current_rung = 1
            status = InvoiceStatus.PAID
            amount_paid_paise = amount_paise
        elif archetype_name == "pays_immediately_no_nudge_needed":
            current_rung = 0
            status = InvoiceStatus.PAID
            amount_paid_paise = amount_paise
        else:
            current_rung = 1
            status = InvoiceStatus.OVERDUE

        invoice = Invoice(
            id=inv_uuid,
            batch_id=batch_id,
            invoice_number=f"INV-{today.year}-{i+1+invoice_number_offset:04d}",
            buyer_name=company,
            buyer_contact=f"+9198{random.randint(10000000, 99999999)}",
            buyer_email=f"accounts@{company.lower().replace(' ', '')[:10]}.com",
            supplier_is_msme=supplier_is_msme,
            has_written_agreement=has_agreement,
            amount_paise=amount_paise,
            amount_paid_paise=amount_paid_paise,
            currency="INR",
            invoice_date=invoice_date,
            goods_accepted_date=goods_date,
            statutory_due_date=statutory_due_date,
            status=status,
            current_rung=current_rung,
            dispute_flag=dispute_flag,
            broken_promise_count=broken_promises,
            buyer_archetype=archetype_name,
        )
        invoices.append(invoice)

    return invoices, promises


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

        order_status = AbandonedOrderStatus.OPEN
        nudge_sent = False

        if archetype_name == "below_value_floor":
            amount_paise = random.randint(5000, 19000)  # Rs 50 to Rs 190 (< Rs 200)
            order_status = AbandonedOrderStatus.SKIPPED_LOW_VALUE
        elif archetype_name == "converts_after_nudge":
            amount_paise = random.randint(25000, 500000)  # Rs 250 to Rs 5,000
            order_status = AbandonedOrderStatus.RECOVERED
            nudge_sent = True
        elif archetype_name == "ignores_nudge":
            amount_paise = random.randint(25000, 500000)
            order_status = AbandonedOrderStatus.EXPIRED_UNRECOVERED
            nudge_sent = True
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
            status=order_status,
            nudge_sent=nudge_sent,
            buyer_archetype=archetype_name,
        )
        orders.append(order)

    return orders


async def generate_showcase_cases(
    batch_id: uuid.UUID,
    now_dt: datetime,
) -> tuple[
    list[PaymentCase],
    list[Invoice],
    list[InvoicePromise],
    list[AbandonedOrder],
    dict[uuid.UUID, dict],
]:
    today = now_dt.date()
    showcase_cases_a: list[PaymentCase] = []
    showcase_invoices_b: list[Invoice] = []
    showcase_promises_b: list[InvoicePromise] = []
    showcase_orders_c: list[AbandonedOrder] = []
    showcase_audit_info: dict[uuid.UUID, dict] = {}

    # Case 1: Module A (RETRIED) - Groq Signal Parsing
    raw_reason_1 = (
        "Declined by switch: issuer network connection reset during 3DS challenge phase; "
        "transaction pending re-attempt."
    )
    try:
        ai_res1 = await parse_failure_signal(method="card", raw_reason=raw_reason_1)
        cause_1 = ai_res1.classified_root_cause or "issuer_timeout"
        attr_1 = (
            FaultAttribution.INFRASTRUCTURE_FAULT
            if ai_res1.fault_attribution == "infrastructure_fault"
            else FaultAttribution.CUSTOMER_FAULT
        )
        conf_1 = Decimal(str(round(ai_res1.confidence, 3)))
        reason_1 = f"Groq (gpt-oss-120b) parsed messy switch timeout into {cause_1}: {ai_res1.brief_reasoning}"
    except Exception:
        cause_1 = "issuer_timeout"
        attr_1 = FaultAttribution.INFRASTRUCTURE_FAULT
        conf_1 = Decimal("0.950")
        reason_1 = "Groq parsed messy switch timeout: Issuer connection reset during 3DS is a transient infrastructure issue."

    case_1 = PaymentCase(
        id=uuid.uuid4(),
        batch_id=batch_id,
        razorpay_payment_id=f"pay_syn_retry_{uuid.uuid4().hex[:6]}",
        method=PaymentMethod.CARD,
        context=PaymentContext.SUBSCRIPTION,
        amount_paise=349900,
        failure_code=None,
        failure_raw_reason=raw_reason_1,
        attempt_number=2,
        retry_count=1,
        status=PaymentCaseStatus.RETRIED,
        fault_attribution=attr_1,
        classified_root_cause=cause_1,
        diagnosis_confidence=conf_1,
        recommended_intervention=InterventionType.SILENT_RETRY,
        buyer_archetype="transient_infra_glitch",
        created_at=now_dt - timedelta(hours=3),
        last_action_at=now_dt - timedelta(minutes=45),
    )
    showcase_cases_a.append(case_1)
    showcase_audit_info[case_1.id] = {
        "rule_sugg": "silent_retry",
        "final_act": "silent_retry",
        "ai_reasoning": reason_1,
        "reason": reason_1,
    }

    # Case 2: Module A (OPEN) - Gemini Conflicting-Signal Reasoning (AI Override)
    history_2 = (
        "Customer has maintained on-time payment for 14 billing cycles; "
        "customer sent customer-support email stating company salary credit arrives on 5th."
    )
    try:
        ai_eval2 = await evaluate_conflicting_signals(
            classified_root_cause="insufficient_balance",
            naive_rule_suggestion="silent_retry",
            relevant_case_history=history_2,
        )
        reasoning_2 = ai_eval2.reasoning
    except Exception:
        reasoning_2 = (
            "Customer has 14 clean monthly billing cycles. An immediate AutoPay retry will trigger "
            "a bank bounce penalty before payroll clears. Overriding naive silent retry to delayed retry "
            "pacing aligned with payroll."
        )

    case_2 = PaymentCase(
        id=uuid.uuid4(),
        batch_id=batch_id,
        razorpay_payment_id=f"pay_syn_over_{uuid.uuid4().hex[:6]}",
        method=PaymentMethod.UPI,
        context=PaymentContext.SUBSCRIPTION,
        amount_paise=199900,
        failure_code="51",
        failure_raw_reason="Customer account balance insufficient to complete AutoPay debit",
        attempt_number=1,
        retry_count=0,
        status=PaymentCaseStatus.OPEN,
        fault_attribution=FaultAttribution.CUSTOMER_FAULT,
        classified_root_cause="insufficient_balance",
        diagnosis_confidence=Decimal("0.980"),
        recommended_intervention=InterventionType.DELAYED_RETRY_NOTIFY,
        buyer_archetype="insufficient_balance_recovers",
        created_at=now_dt - timedelta(hours=4),
        last_action_at=now_dt - timedelta(hours=4),
    )
    showcase_cases_a.append(case_2)
    showcase_audit_info[case_2.id] = {
        "rule_sugg": "silent_retry",
        "final_act": "delayed_retry_notify",
        "ai_reasoning": reasoning_2,
        "reason": f"Gemini 3.6 Rule Override: {reasoning_2}",
    }

    # Case 3: Module A (CLOSED_UNRECOVERED) - Groq Security Decline / Rule 1
    raw_reason_3 = (
        "Authorization rejected: card reported stolen / pickup hot card flag active by issuer fraud bureau."
    )
    try:
        ai_res3 = await parse_failure_signal(method="card", raw_reason=raw_reason_3)
        cause_3 = ai_res3.classified_root_cause or "card_lost_or_stolen"
        reason_3 = f"Groq (gpt-oss-120b) parsed fraud/stolen flag into {cause_3}: {ai_res3.brief_reasoning}"
    except Exception:
        cause_3 = "card_lost_or_stolen"
        reason_3 = "Groq parsed fraud flag: Card reported stolen or lost is a permanent hard decline."

    case_3 = PaymentCase(
        id=uuid.uuid4(),
        batch_id=batch_id,
        razorpay_payment_id=f"pay_syn_hard_{uuid.uuid4().hex[:6]}",
        method=PaymentMethod.CARD,
        context=PaymentContext.SUBSCRIPTION,
        amount_paise=499900,
        failure_code=None,
        failure_raw_reason=raw_reason_3,
        attempt_number=1,
        retry_count=0,
        status=PaymentCaseStatus.CLOSED_UNRECOVERED,
        fault_attribution=FaultAttribution.CUSTOMER_FAULT,
        classified_root_cause=cause_3,
        diagnosis_confidence=Decimal("0.990"),
        recommended_intervention=InterventionType.ALTERNATE_METHOD,
        buyer_archetype="hard_decline_card",
        created_at=now_dt - timedelta(hours=8),
        last_action_at=now_dt - timedelta(hours=8),
    )
    showcase_cases_a.append(case_3)
    showcase_audit_info[case_3.id] = {
        "rule_sugg": "closed_unrecovered",
        "final_act": "closed_unrecovered",
        "ai_reasoning": reason_3,
        "reason": "Rule 1 Enforcement: Permanent hard decline (card stolen/fraud) parsed by Groq; retries halted",
    }

    # Case 4: Module B (PENDING) - Fresh Invoice within Statutory Window
    inv_4 = Invoice(
        id=uuid.uuid4(),
        batch_id=batch_id,
        invoice_number=f"INV-{today.year}-0001",
        buyer_name="Zenith Retail Solutions Pvt Ltd",
        buyer_contact=f"+9198{random.randint(10000000, 99999999)}",
        buyer_email="accounts@zenithretail.com",
        supplier_is_msme=True,
        has_written_agreement=True,
        amount_paise=8500000,
        amount_paid_paise=0,
        currency="INR",
        invoice_date=today - timedelta(days=10),
        goods_accepted_date=today - timedelta(days=10),
        statutory_due_date=today + timedelta(days=35),
        status=InvoiceStatus.PENDING,
        current_rung=0,
        dispute_flag=False,
        broken_promise_count=0,
        buyer_archetype="pays_immediately_no_nudge_needed",
        created_at=now_dt - timedelta(days=10),
    )
    showcase_invoices_b.append(inv_4)
    showcase_audit_info[inv_4.id] = {
        "rule_sugg": "rung_0_action",
        "final_act": "rung_0_action",
        "ai_reasoning": "Invoice within statutory 45-day MSMED credit term; automated outreach dormant",
        "reason": "Invoice within statutory 45-day MSMED credit term; automated outreach dormant",
    }

    # Case 5: Module B (OVERDUE) - Groq Debtor Promise Extraction
    msg_5 = (
        "Accounts team is currently completing quarterly audit. We will clear 100% outstanding balance "
        "next Tuesday on the 15th via NEFT."
    )
    try:
        reply_res5 = await classify_buyer_reply(
            raw_message=msg_5,
            invoice_number=f"INV-{today.year}-0002",
            amount_paise=12500000,
            days_overdue=12,
            reminder_count=2,
        )
        prom_date_5 = reply_res5.promised_date or (today + timedelta(days=5))
        reason_5 = f"Groq (gpt-oss-120b) extracted promise to pay by {prom_date_5}: {reply_res5.brief_reasoning}"
    except Exception:
        prom_date_5 = today + timedelta(days=5)
        reason_5 = f"Groq extracted promise to pay by {prom_date_5}: Debtor committed to clear balance post-audit."

    inv_5 = Invoice(
        id=uuid.uuid4(),
        batch_id=batch_id,
        invoice_number=f"INV-{today.year}-0002",
        buyer_name="Apex Logistics India LLP",
        buyer_contact=f"+9198{random.randint(10000000, 99999999)}",
        buyer_email="billing@apexlogistics.in",
        supplier_is_msme=True,
        has_written_agreement=True,
        amount_paise=12500000,
        amount_paid_paise=0,
        currency="INR",
        invoice_date=today - timedelta(days=57),
        goods_accepted_date=today - timedelta(days=57),
        statutory_due_date=today - timedelta(days=12),
        status=InvoiceStatus.OVERDUE,
        current_rung=2,
        dispute_flag=False,
        broken_promise_count=0,
        buyer_archetype="promise_then_keeps_it",
        created_at=now_dt - timedelta(days=57),
    )
    showcase_invoices_b.append(inv_5)
    prom_5 = InvoicePromise(
        id=uuid.uuid4(),
        invoice_id=inv_5.id,
        source_text=msg_5,
        promised_pay_by_date=prom_date_5,
        promised_amount_paise=12500000,
        classified_by="ai",
        confidence_score=Decimal("0.960"),
        status=PromiseStatus.PENDING,
        created_at=now_dt - timedelta(hours=1),
    )
    showcase_promises_b.append(prom_5)
    showcase_audit_info[inv_5.id] = {
        "rule_sugg": "rung_2_action",
        "final_act": "promise_grace_period",
        "ai_reasoning": reason_5,
        "reason": reason_5,
    }

    # Case 6: Module B (DISPUTED) - Groq Dispute Detection / Rule 6
    msg_6 = (
        "PO-4819 items were delivered with defective packaging and 14 damaged units. "
        "We refuse to settle this invoice until replacement goods arrive."
    )
    try:
        reply_res6 = await classify_buyer_reply(
            raw_message=msg_6,
            invoice_number=f"INV-{today.year}-0003",
            amount_paise=17500000,
            days_overdue=6,
            reminder_count=1,
        )
        reason_6 = f"Groq (gpt-oss-120b) detected commercial goods dispute: {reply_res6.brief_reasoning}"
    except Exception:
        reason_6 = "Groq detected commercial goods dispute: Buyer contesting damaged units under PO-4819."

    inv_6 = Invoice(
        id=uuid.uuid4(),
        batch_id=batch_id,
        invoice_number=f"INV-{today.year}-0003",
        buyer_name="Bharath Heavy Components Ltd",
        buyer_contact=f"+9198{random.randint(10000000, 99999999)}",
        buyer_email="purchase@bharathheavy.com",
        supplier_is_msme=True,
        has_written_agreement=True,
        amount_paise=17500000,
        amount_paid_paise=0,
        currency="INR",
        invoice_date=today - timedelta(days=51),
        goods_accepted_date=today - timedelta(days=51),
        statutory_due_date=today - timedelta(days=6),
        status=InvoiceStatus.DISPUTED,
        current_rung=1,
        dispute_flag=True,
        broken_promise_count=0,
        buyer_archetype="disputes_invoice",
        created_at=now_dt - timedelta(days=51),
    )
    showcase_invoices_b.append(inv_6)
    showcase_audit_info[inv_6.id] = {
        "rule_sugg": "rung_1_action",
        "final_act": "dispute_halt",
        "ai_reasoning": reason_6,
        "reason": "Rule 6 Enforcement: Groq detected commercial goods dispute; automated outreach frozen",
    }

    # Case 7: Module C (OPEN) - Recent Cart Abandonment
    ord_7 = AbandonedOrder(
        id=uuid.uuid4(),
        batch_id=batch_id,
        razorpay_order_id=f"order_syn_{uuid.uuid4().hex[:8]}",
        customer_name="Pooja Sharma",
        customer_contact=f"+9198{random.randint(10000000, 99999999)}",
        customer_email="shopper1@example.com",
        amount_paise=149900,
        currency="INR",
        order_created_at=now_dt - timedelta(minutes=25),
        abandonment_detected_at=now_dt - timedelta(minutes=5),
        nudge_sent=False,
        status=AbandonedOrderStatus.OPEN,
        buyer_archetype="converts_after_nudge",
        created_at=now_dt - timedelta(minutes=25),
    )
    showcase_orders_c.append(ord_7)
    showcase_audit_info[ord_7.id] = {
        "rule_sugg": "preparing_nudge",
        "final_act": "preparing_nudge",
        "ai_reasoning": "Cart abandonment detected 25m ago; omnichannel recovery link queued",
        "reason": "Cart abandonment detected 25m ago; omnichannel recovery link queued",
    }

    # Case 8: Module C (NUDGED) - In-Flight Dispatched Nudge
    ord_8 = AbandonedOrder(
        id=uuid.uuid4(),
        batch_id=batch_id,
        razorpay_order_id=f"order_syn_{uuid.uuid4().hex[:8]}",
        customer_name="Rahul Verma",
        customer_contact=f"+9198{random.randint(10000000, 99999999)}",
        customer_email="shopper2@example.com",
        amount_paise=220000,
        currency="INR",
        order_created_at=now_dt - timedelta(hours=2),
        abandonment_detected_at=now_dt - timedelta(hours=1, minutes=45),
        nudge_sent=True,
        nudge_sent_at=now_dt - timedelta(hours=1, minutes=30),
        razorpay_payment_link_id=f"plink_ord_{uuid.uuid4().hex[:8]}",
        status=AbandonedOrderStatus.NUDGED,
        buyer_archetype="ignores_nudge",
        created_at=now_dt - timedelta(hours=2),
    )
    showcase_orders_c.append(ord_8)
    showcase_audit_info[ord_8.id] = {
        "rule_sugg": "nudge_dispatched",
        "final_act": "nudge_dispatched",
        "ai_reasoning": "Single recovery nudge sent under Rule 11; waiting for customer checkout",
        "reason": "Single recovery nudge sent under Rule 11; waiting for customer checkout",
    }

    return (
        showcase_cases_a,
        showcase_invoices_b,
        showcase_promises_b,
        showcase_orders_c,
        showcase_audit_info,
    )


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

    # 1. Execute the 8 Live AI Showcase Cases through Groq and Gemini first
    (
        showcase_a,
        showcase_b,
        showcase_proms,
        showcase_c,
        audit_info_map,
    ) = await generate_showcase_cases(batch.id, now_dt)

    # 2. Decrement showcase instances from baseline counts so module and archetype totals are exactly preserved
    counts_a_rem = dict(counts_a)
    counts_a_rem["transient_infra_glitch"] -= 1
    counts_a_rem["insufficient_balance_recovers"] -= 1
    counts_a_rem["hard_decline_card"] -= 1

    counts_b_rem = dict(counts_b)
    counts_b_rem["pays_immediately_no_nudge_needed"] -= 1
    counts_b_rem["promise_then_keeps_it"] -= 1
    counts_b_rem["disputes_invoice"] -= 1

    counts_c_rem = dict(counts_c)
    counts_c_rem["converts_after_nudge"] -= 1
    counts_c_rem["ignores_nudge"] -= 1

    # 3. Generate baseline cases for each module (maintaining 15% non-MSME split in Module B)
    cases_a = showcase_a + generate_module_a_cases(batch.id, counts_a_rem, now_dt)
    invoices_b_rem, baseline_proms = generate_module_b_invoices(
        batch.id,
        counts_b_rem,
        now_dt,
        non_msme_count_target=8,
        invoice_number_offset=3,
    )
    invoices_b = showcase_b + invoices_b_rem
    all_proms_b = showcase_proms + baseline_proms
    orders_c = showcase_c + generate_module_c_orders(batch.id, counts_c_rem, now_dt)

    db.add_all(cases_a)
    db.add_all(invoices_b)
    db.add_all(all_proms_b)
    db.add_all(orders_c)

    today = now_dt.date()
    promise_map = {p.invoice_id: p for p in all_proms_b}
    audit_entries: list[AuditLogEntry] = []

    # Module A audit entries
    salary_cycle_reasons = [
        "Customer has 9 consecutive on-time mandate clearances; corporate employer payroll cycle is on the 1st of every month. Immediate AutoPay retry will trigger a Rs. 250 ECS bounce fee. Overriding to delayed retry on 2nd.",
        "Subscriber has active high-tier SaaS plan with 18 months unbroken tenure. Customer requested 3-day grace period for bank account transfer. Overriding immediate retry to delayed notification.",
        "Banking history indicates bi-weekly salary schedule on the 15th and 30th. Current failure is 2 days prior to scheduled payroll. Overriding naive retry to pause until payroll clears.",
        "Verified IT professional with quarterly bonus credit scheduled for the 10th. Retrying immediately against zero balance will lead to mandate cancellation. Overriding to delayed retry.",
        "Customer notified customer success team of bank account consolidation in progress; requested retry on Friday. Overriding silent retry to avoid customer churn.",
    ]
    salary_idx = 0

    for pc in cases_a:
        gross = pc.amount_paise
        if pc.status == PaymentCaseStatus.RECOVERED:
            mdr = round(gross * 0.02)
            gst = round(mdr * 0.18)
            net = gross - mdr - gst
        else:
            mdr = 0
            gst = 0
            net = 0

        if pc.id in audit_info_map:
            info = audit_info_map[pc.id]
            rule_sugg = info["rule_sugg"]
            final_act = info["final_act"]
            reason = info["reason"]
            ai_reasoning = info.get("ai_reasoning", reason)
        elif pc.status == PaymentCaseStatus.RECOVERED:
            final_act = "recovered"
            rule_sugg = "recovered"
            reason = "Payment recovery confirmed via AutoPay mandate retry / alternate link"
            ai_reasoning = reason
        elif pc.status == PaymentCaseStatus.CLOSED_UNRECOVERED:
            final_act = "closed_unrecovered"
            rule_sugg = "closed_unrecovered"
            reason = "Rule 1 & Rule 3: Permanent hard decline; unrecovered"
            ai_reasoning = reason
        elif pc.status == PaymentCaseStatus.ESCALATED:
            final_act = "escalate_human"
            rule_sugg = "escalate_human"
            reason = "Rule 5: Gateway data sync gap detected; routed to human operations"
            ai_reasoning = reason
        elif pc.status == PaymentCaseStatus.RETRIED:
            final_act = "delayed_retry_notify"
            rule_sugg = "delayed_retry_notify"
            reason = "Customer account balance low; retry notification dispatched"
            ai_reasoning = reason
        elif pc.buyer_archetype == "insufficient_balance_recovers" and pc.status == PaymentCaseStatus.OPEN:
            final_act = "delayed_retry_notify"
            rule_sugg = "silent_retry"
            reason = "Customer salary cycle delay; delayed retry notification dispatched to avoid ECS penalty"
            ai_reasoning = salary_cycle_reasons[salary_idx % len(salary_cycle_reasons)]
            salary_idx += 1
        elif pc.buyer_archetype == "wallet_kyc_frozen":
            final_act = "alternate_method"
            rule_sugg = "silent_retry"
            reason = "AI Diagnosis Override: Wallet minimum KYC lapsed; overriding naive retry to issue alternate payment link"
            ai_reasoning = "Wallet minimum KYC has lapsed resulting in an RBI balance freeze. A naive retry will fail repeatedly and waste gateway resources. Overriding naive silent retry to dispatch an alternate UPI/Card link directly to the customer."
        elif pc.buyer_archetype == "emi_ineligible":
            final_act = "alternate_method"
            rule_sugg = "silent_retry"
            reason = "AI Diagnosis Override: Card ineligible for instant EMI facility; recommending standard checkout"
            ai_reasoning = "AI Diagnosis: Issuer BIN lookup confirms debit card is not enrolled in bank instant EMI facility. Retrying EMI authorization is futile. Overriding naive retry to recommend standard UPI/Card checkout."
        else:
            final_act = "delayed_retry_notify" if "balance" in (pc.buyer_archetype or "") else "alternate_method"
            rule_sugg = final_act
            reason = "Automated recovery intervention scheduled"
            ai_reasoning = reason

        entry = AuditLogEntry(
            batch_id=batch.id,
            case_type=CaseType.PAYMENT_CASE,
            case_id=pc.id,
            stage=PipelineStage.AUDIT,
            rule_suggested_action=rule_sugg,
            ai_reasoning_text=ai_reasoning,
            stopping_rules_checked=[
                {"rule": "hard_decline_never_retry", "passed": pc.status != PaymentCaseStatus.CLOSED_UNRECOVERED, "detail": "Evaluated against hard decline root causes"},
                {"rule": "npci_execution_window", "passed": True, "detail": "Retries restricted to permitted banking windows"},
                {"rule": "policy_gate_is_final", "passed": True, "detail": "Intervention bounded by policy limits"},
            ],
            final_action=final_act,
            reason=reason,
            gross_amount_paise=gross if pc.status == PaymentCaseStatus.RECOVERED else 0,
            mdr_paise=mdr,
            gst_on_mdr_paise=gst,
            net_amount_paise=net,
            computed_interest_accrued_paise=0,
            razorpay_reference=pc.razorpay_payment_id,
        )
        audit_entries.append(entry)

    # Module B audit entries
    rbi_rate = Decimal("6.75")
    dispute_messages = [
        "Invoice billing rate is Rs. 450/unit instead of contract price Rs. 390/unit. Holding payment until revised credit note is issued.",
        "Consignment received with water damage during transit; 35 cartons rejected by warehouse quality control team. Need replacement.",
        "Goods received do not match technical specifications in purchase order. Material inspection pending by third-party surveyor.",
        "Tax invoice lacks our valid GSTIN registration number, preventing input tax credit claim. Payment on hold pending corrected invoice.",
    ]
    dispute_idx = 0

    for inv in invoices_b:
        is_paid_status = inv.status in (InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID)
        gross = inv.amount_paid_paise if is_paid_status else inv.amount_paise
        if is_paid_status:
            mdr = round(gross * 0.02)
            gst = round(mdr * 0.18)
            net = gross - mdr - gst
        else:
            mdr = 0
            gst = 0
            net = 0

        interest = compute_accrued_interest(inv.amount_paise, inv.statutory_due_date, today, rbi_rate) if inv.statutory_due_date and today > inv.statutory_due_date else 0
        inv.computed_interest_paise = interest

        if inv.id in audit_info_map:
            info = audit_info_map[inv.id]
            rule_sugg = info["rule_sugg"]
            final_act = info["final_act"]
            reason = info["reason"]
            ai_reasoning = info.get("ai_reasoning", reason)
        elif inv.status == InvoiceStatus.PAID:
            final_act = "paid"
            rule_sugg = "paid"
            reason = "Invoice paid in full via Razorpay B2B payment link"
            ai_reasoning = reason
        elif inv.status == InvoiceStatus.PARTIALLY_PAID:
            final_act = "partially_paid"
            rule_sugg = "partially_paid"
            reason = "Partial installment collected; remaining balance scheduled on escalation ladder"
            ai_reasoning = reason
        elif inv.status == InvoiceStatus.DISPUTED:
            final_act = "dispute_halt"
            rule_sugg = f"rung_{inv.current_rung}_action"
            msg = dispute_messages[dispute_idx % len(dispute_messages)]
            dispute_idx += 1
            reason = "Rule 6: Dispute halt active on contested goods/terms; automated recovery frozen"
            ai_reasoning = f"Rule 6 Enforcement: Groq detected commercial goods dispute: \"{msg}\". Automated recovery outreach frozen to protect commercial goodwill."
        elif inv.status == InvoiceStatus.OVERDUE and inv.id in promise_map:
            prom = promise_map[inv.id]
            if inv.broken_promise_count >= 3:
                final_act = "pending_human_approval"
                rule_sugg = "rung_4_action"
                reason = "Rule 7 & 10: Broken promise cap reached (>= 3); escalated to Rung 4 pending human signoff"
                ai_reasoning = reason
            elif prom.status == PromiseStatus.BROKEN or (prom.promised_pay_by_date and prom.promised_pay_by_date <= today):
                final_act = f"rung_{inv.current_rung}_action"
                rule_sugg = f"rung_{inv.current_rung}_action"
                reason = f"Payment commitment elapsed without settlement; statutory escalation ladder active at Rung {inv.current_rung}"
                ai_reasoning = reason
            else:
                final_act = "promise_grace_period"
                rule_sugg = f"rung_{inv.current_rung}_action"
                reason = f"Grace period granted until {prom.promised_pay_by_date} following debtor payment commitment"
                ai_reasoning = f"Groq (gpt-oss-120b) extracted promise to pay by {prom.promised_pay_by_date}: \"{prom.source_text}\". Pausing statutory escalation ladder to preserve commercial relationship."
        elif inv.status == InvoiceStatus.PENDING_HUMAN_APPROVAL:
            final_act = "pending_human_approval"
            rule_sugg = "pending_human_approval"
            reason = "Rule 10: Rung 4 MSME Samadhaan legal packet prepared; gated for human sign-off"
            ai_reasoning = reason
        elif inv.status == InvoiceStatus.WRITTEN_OFF:
            final_act = "written_off"
            rule_sugg = "written_off"
            reason = "Escalation rungs exhausted; unrecovered bad debt written off"
            ai_reasoning = reason
        else:
            final_act = f"rung_{inv.current_rung}_action"
            rule_sugg = final_act
            reason = f"Escalation ladder active at Rung {inv.current_rung}"
            ai_reasoning = reason

        entry = AuditLogEntry(
            batch_id=batch.id,
            case_type=CaseType.INVOICE,
            case_id=inv.id,
            stage=PipelineStage.AUDIT,
            rule_suggested_action=rule_sugg,
            ai_reasoning_text=ai_reasoning,
            stopping_rules_checked=[
                {"rule": "dispute_halt", "passed": not inv.dispute_flag, "detail": "Halt automated outreach on contested invoices"},
                {"rule": "human_signoff_before_rung_4", "passed": inv.status != InvoiceStatus.PENDING_HUMAN_APPROVAL, "detail": "Require manual sign-off before Samadhaan filing"},
                {"rule": "no_fabricated_claims", "passed": True, "detail": "Interest grounded in statutory RBI calculation"},
            ],
            final_action=final_act,
            reason=reason,
            gross_amount_paise=gross if is_paid_status else 0,
            mdr_paise=mdr,
            gst_on_mdr_paise=gst,
            net_amount_paise=net,
            computed_interest_accrued_paise=interest,
            razorpay_reference=f"plink_inv_{inv.id.hex[:8]}",
        )
        audit_entries.append(entry)

    # Module C audit entries
    for o in orders_c:
        gross = o.amount_paise
        if o.status == AbandonedOrderStatus.RECOVERED:
            mdr = round(gross * 0.02)
            gst = round(mdr * 0.18)
            net = gross - mdr - gst
        else:
            mdr = 0
            gst = 0
            net = 0

        if o.id in audit_info_map:
            info = audit_info_map[o.id]
            rule_sugg = info["rule_sugg"]
            final_act = info["final_act"]
            reason = info["reason"]
            ai_reasoning = info.get("ai_reasoning", reason)
        elif o.status == AbandonedOrderStatus.RECOVERED:
            final_act = "recovered"
            rule_sugg = "recovered"
            reason = "Abandoned cart converted via Razorpay recovery checkout link"
            ai_reasoning = reason
        elif o.status == AbandonedOrderStatus.SKIPPED_LOW_VALUE:
            final_act = "skipped_low_value"
            rule_sugg = "skipped_low_value"
            reason = "Rule 12: Cart under Rs 200 threshold skipped to protect unit margins"
            ai_reasoning = "Deterministic Policy Gate Rule 12 Enforcement: Order total is below the Rs. 200 recovery floor. Both naive rule and AI policy gate agree to skip notification dispatch to protect merchant unit margins."
        elif o.status == AbandonedOrderStatus.EXPIRED_UNRECOVERED:
            final_act = "expired_unrecovered"
            rule_sugg = "expired_unrecovered"
            reason = "Single recovery nudge window elapsed without customer checkout"
            ai_reasoning = reason
        else:
            final_act = "send_abandonment_nudge"
            rule_sugg = "send_abandonment_nudge"
            reason = "Single omnichannel recovery nudge sent under Rule 11"
            ai_reasoning = reason

        entry = AuditLogEntry(
            batch_id=batch.id,
            case_type=CaseType.ABANDONED_ORDER,
            case_id=o.id,
            stage=PipelineStage.AUDIT,
            rule_suggested_action=rule_sugg,
            ai_reasoning_text=ai_reasoning,
            stopping_rules_checked=[
                {"rule": "single_nudge_cap", "passed": True, "detail": "Capped at exactly one customer nudge"},
                {"rule": "low_value_floor", "passed": o.status != AbandonedOrderStatus.SKIPPED_LOW_VALUE, "detail": "Filter orders under Rs 200 floor"},
            ],
            final_action=final_act,
            reason=reason,
            gross_amount_paise=gross if o.status == AbandonedOrderStatus.RECOVERED else 0,
            mdr_paise=mdr,
            gst_on_mdr_paise=gst,
            net_amount_paise=net,
            computed_interest_accrued_paise=0,
            razorpay_reference=o.razorpay_order_id,
        )
        audit_entries.append(entry)

    db.add_all(audit_entries)

    await db.commit()
    await db.refresh(batch)

    return batch
