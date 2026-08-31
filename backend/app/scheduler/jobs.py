import asyncio
from datetime import date, datetime, timedelta, timezone
import logging
from sqlalchemy import select

from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.order import AbandonedOrder, AbandonedOrderStatus
from app.db.models.payment_case import PaymentCase, PaymentCaseStatus
from app.db.session import async_session_factory
from app.pipeline.run import run_pipeline_for_invoice, run_pipeline_for_order, run_pipeline_for_payment_case

logger = logging.getLogger("scheduler")

# Background scheduler state
_scheduler_task: asyncio.Task | None = None
_stop_event = asyncio.Event()


async def check_module_b_invoices():
    # Advance invoices past statutory due date or overdue intervals
    now_date = date.today()
    async with async_session_factory() as db:
        res = await db.execute(
            select(Invoice).where(
                Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
                Invoice.dispute_flag == False,
            )
        )
        invoices = res.scalars().all()

        for inv in invoices:
            statutory_due = inv.statutory_due_date or inv.invoice_date
            if not statutory_due:
                continue

            days_overdue = (now_date - statutory_due).days
            target_rung = inv.current_rung

            if days_overdue >= 0 and inv.current_rung == 0:
                target_rung = 1
            elif days_overdue >= 7 and inv.current_rung == 1:
                target_rung = 2
            elif days_overdue >= 14 and inv.current_rung == 2:
                target_rung = 3
            elif days_overdue >= 30 and inv.current_rung == 3:
                target_rung = 4

            if target_rung > inv.current_rung:
                logger.info(f"Scheduler: Advancing Invoice {inv.id} from Rung {inv.current_rung} to {target_rung}")
                await run_pipeline_for_invoice(invoice_id=inv.id, db=db)


async def check_module_c_orders():
    # Advance abandoned orders that were created > 30 minutes ago
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    async with async_session_factory() as db:
        res = await db.execute(
            select(AbandonedOrder).where(
                AbandonedOrder.status == AbandonedOrderStatus.OPEN,
                AbandonedOrder.order_created_at <= cutoff_time,
                AbandonedOrder.nudge_sent == False,
            )
        )
        orders = res.scalars().all()

        for o in orders:
            logger.info(f"Scheduler: Processing Abandoned Order {o.id}")
            await run_pipeline_for_order(order_id=o.id, db=db)


async def check_module_a_retries():
    # Process Module A cases whose delayed retry cooldown has elapsed
    now_utc = datetime.now(timezone.utc)
    cutoff_time = now_utc - timedelta(hours=48)
    async with async_session_factory() as db:
        res = await db.execute(
            select(PaymentCase).where(
                PaymentCase.status == PaymentCaseStatus.OPEN,
                PaymentCase.recommended_intervention == "delayed_retry_notify",
                PaymentCase.last_action_at <= cutoff_time,
            )
        )
        cases = res.scalars().all()

        for pc in cases:
            logger.info(f"Scheduler: Retrying PaymentCase {pc.id}")
            await run_pipeline_for_payment_case(case_id=pc.id, db=db)


async def scheduler_loop(interval_seconds: int = 15):
    logger.info(f"Scheduler loop started (interval={interval_seconds}s)")
    while not _stop_event.is_set():
        try:
            await check_module_b_invoices()
            await check_module_c_orders()
            await check_module_a_retries()
        except Exception as e:
            logger.error(f"Scheduler tick error: {e}")

        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass


def start_scheduler(interval_seconds: int = 15):
    global _scheduler_task, _stop_event
    _stop_event.clear()
    _scheduler_task = asyncio.create_task(scheduler_loop(interval_seconds=interval_seconds))


def stop_scheduler():
    global _scheduler_task, _stop_event
    _stop_event.set()
    if _scheduler_task:
        _scheduler_task.cancel()
