from app.db.models.payment_case import PaymentMethod
from app.domain_logic.settlement import compute_settlement


def test_standard_settlement():
    # 100,000 paise (Rs 1,000)
    # Fee: 2% = 2,000 paise
    # GST on fee: 18% of 2000 = 360 paise
    # Net: 100000 - 2000 - 360 = 97640 paise
    breakdown = compute_settlement(100000, PaymentMethod.CARD)
    assert breakdown.gross_amount_paise == 100000
    assert breakdown.mdr_paise == 2000
    assert breakdown.gst_on_mdr_paise == 360
    assert breakdown.net_amount_paise == 97640


def test_rupay_credit_on_upi_settlement():
    # 100,000 paise (Rs 1,000)
    # Fee: 2.15% = 2,150 paise
    # GST: 18% of 2150 = 387 paise
    # Net: 100000 - 2150 - 387 = 97463 paise
    breakdown = compute_settlement(100000, PaymentMethod.UPI, is_rupay_credit_on_upi=True)
    assert breakdown.gross_amount_paise == 100000
    assert breakdown.mdr_paise == 2150
    assert breakdown.gst_on_mdr_paise == 387
    assert breakdown.net_amount_paise == 97463


def test_cardless_emi_settlement():
    # 100,000 paise (Rs 1,000)
    # Fee: 3% = 3,000 paise
    # GST: 18% of 3000 = 540 paise
    # Net: 100000 - 3000 - 540 = 96460 paise
    breakdown = compute_settlement(100000, PaymentMethod.EMI, is_cardless_emi=True)
    assert breakdown.gross_amount_paise == 100000
    assert breakdown.mdr_paise == 3000
    assert breakdown.gst_on_mdr_paise == 540
    assert breakdown.net_amount_paise == 96460
