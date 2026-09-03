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
            select(Invoice.id, Invoice.current_rung, Invoice.statutory_due_date, Invoice.invoice_date).where(
                Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
                Invoice.dispute_flag == False,
            )
        )
        invoice_rows = res.all()

    for inv_id, current_rung, statutory_due, invoice_date in invoice_rows:
        due_date = statutory_due or invoice_date
        if not due_date:
            continue

        days_overdue = (now_date - due_date).days
        target_rung = current_rung

        if days_overdue >= 0 and current_rung == 0:
            target_rung = 1
        elif days_overdue >= 7 and current_rung == 1:
            target_rung = 2
        elif days_overdue >= 14 and current_rung == 2:
            target_rung = 3
        elif days_overdue >= 30 and current_rung == 3:
            target_rung = 4

        if target_rung > current_rung:
            logger.info(f"Scheduler: Advancing Invoice {inv_id} from Rung {current_rung} to {target_rung}")
            try:
                async with async_session_factory() as case_db:
                    await run_pipeline_for_invoice(invoice_id=inv_id, db=case_db)
            except Exception as e:
                logger.error(f"Scheduler error processing invoice {inv_id}: {e}")


async def check_module_c_orders():
    # Advance abandoned orders that were created > 30 minutes ago
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    async with async_session_factory() as db:
        res = await db.execute(
            select(AbandonedOrder.id).where(
                AbandonedOrder.status == AbandonedOrderStatus.OPEN,
                AbandonedOrder.order_created_at <= cutoff_time,
                AbandonedOrder.nudge_sent == False,
            )
        )
        order_ids = res.scalars().all()

    for o_id in order_ids:
        logger.info(f"Scheduler: Processing Abandoned Order {o_id}")
        try:
            async with async_session_factory() as case_db:
                await run_pipeline_for_order(order_id=o_id, db=case_db)
        except Exception as e:
            logger.error(f"Scheduler error processing order {o_id}: {e}")


async def check_module_a_retries():
    # Process Module A cases whose delayed retry cooldown has elapsed
    now_utc = datetime.now(timezone.utc)
    cutoff_time = now_utc - timedelta(hours=48)
    async with async_session_factory() as db:
        res = await db.execute(
            select(PaymentCase.id).where(
                PaymentCase.status == PaymentCaseStatus.OPEN,
                PaymentCase.recommended_intervention == "delayed_retry_notify",
                PaymentCase.last_action_at <= cutoff_time,
            )
        )
        case_ids = res.scalars().all()

    for pc_id in case_ids:
        logger.info(f"Scheduler: Retrying PaymentCase {pc_id}")
        try:
            async with async_session_factory() as case_db:
                await run_pipeline_for_payment_case(case_id=pc_id, db=case_db)
        except Exception as e:
            logger.error(f"Scheduler error retrying payment case {pc_id}: {e}")



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
