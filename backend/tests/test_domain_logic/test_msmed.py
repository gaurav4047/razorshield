from datetime import date
from decimal import Decimal
from app.config import settings
from app.domain_logic.msmed import compute_accrued_interest, compute_fallback_due_date, compute_statutory_due_date


def test_statutory_due_date_with_agreement():
    goods_accepted = date(2026, 1, 1)
    assert compute_statutory_due_date(goods_accepted, has_written_agreement=True) == date(2026, 2, 15)


def test_statutory_due_date_without_agreement():
    goods_accepted = date(2026, 1, 1)
    assert compute_statutory_due_date(goods_accepted, has_written_agreement=False) == date(2026, 1, 16)


def test_fallback_due_date():
    invoice_dt = date(2026, 3, 1)
    assert compute_fallback_due_date(invoice_dt, 30) == date(2026, 3, 31)


def test_msmed_interest_before_or_on_due_date():
    due = date(2026, 5, 1)
    rbi_rate = settings.RBI_BANK_RATE
    assert compute_accrued_interest(1000000, due, date(2026, 4, 30), rbi_rate) == 0
    assert compute_accrued_interest(1000000, due, date(2026, 5, 1), rbi_rate) == 0


def test_msmed_interest_current_rate_5_50():
    # Principal: 10,000,000 paise (Rs 1,00,000)
    # 15 days overdue -> 0.5 months
    # Rate: 5.50% -> monthly 1.375% = 0.01375
    # Accrued = 10000000 * ((1 + 0.01375)^0.5 - 1) = 68515 paise (Rs 685.15)
    due = date(2026, 1, 1)
    as_of = date(2026, 1, 16)
    rbi_rate = Decimal("5.50")
    assert compute_accrued_interest(10000000, due, as_of, rbi_rate) == 68515


def test_msmed_interest_hand_computed_one_month():
    # Principal: 100,000 paise (Rs 1,000)
    # 30 days overdue -> exactly 1.0 month fraction
    # Monthly rate = (6.75 * 3) / 12 = 1.6875% = 0.016875
    # Accrued = 100000 * 0.016875 = 1687.5 paise -> round to 1688 paise
    due = date(2026, 1, 1)
    as_of = date(2026, 1, 31)
    rbi_rate = Decimal("6.75")
    assert compute_accrued_interest(100000, due, as_of, rbi_rate) == 1688


def test_msmed_interest_hand_computed_twelve_days():
    # Principal: 18,450,000 paise (Rs 184,500)
    # 12 days overdue -> 12/30 = 0.4 months
    # Rate: 6.75% -> monthly 1.6875% = 0.016875
    # Accrued = 18450000 * ((1 + 0.016875)^0.4 - 1) = 123913 paise
    due = date(2026, 6, 1)
    as_of = date(2026, 6, 13)
    rbi_rate = Decimal("6.75")
    assert compute_accrued_interest(18450000, due, as_of, rbi_rate) == 123913
