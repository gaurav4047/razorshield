from datetime import date, timedelta
from decimal import Decimal


def compute_statutory_due_date(goods_accepted_date: date, has_written_agreement: bool) -> date:
    days = 45 if has_written_agreement else 15
    return goods_accepted_date + timedelta(days=days)


def compute_fallback_due_date(invoice_date: date, credit_period_days: int = 30) -> date:
    return invoice_date + timedelta(days=credit_period_days)


def compute_accrued_interest(
    amount_paise: int,
    statutory_due_date: date,
    as_of_date: date,
    rbi_bank_rate: Decimal,
) -> int:
    if as_of_date <= statutory_due_date:
        return 0

    days_overdue = (as_of_date - statutory_due_date).days
    monthly_rate = (rbi_bank_rate * Decimal(3)) / Decimal(12)
    months_overdue = Decimal(days_overdue) / Decimal(30)
    accrued = Decimal(amount_paise) * (
        (Decimal(1) + (monthly_rate / Decimal(100))) ** months_overdue - Decimal(1)
    )
    return round(float(accrued))
