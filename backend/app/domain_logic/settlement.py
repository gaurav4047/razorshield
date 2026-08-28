from dataclasses import dataclass
from decimal import Decimal
from app.db.models.payment_case import PaymentMethod

STANDARD_FEE_RATE = Decimal("0.02")
RUPAY_CREDIT_ON_UPI_FEE_RATE = Decimal("0.0215")
CARDLESS_EMI_FEE_RATE = Decimal("0.03")
GST_RATE = Decimal("0.18")


@dataclass(frozen=True)
class SettlementBreakdown:
    gross_amount_paise: int
    mdr_paise: int
    gst_on_mdr_paise: int
    net_amount_paise: int
    settlement_note: str


def compute_settlement(
    gross_amount_paise: int,
    method: PaymentMethod,
    is_rupay_credit_on_upi: bool = False,
    is_cardless_emi: bool = False,
) -> SettlementBreakdown:
    if is_rupay_credit_on_upi and method == PaymentMethod.UPI:
        fee_rate = RUPAY_CREDIT_ON_UPI_FEE_RATE
    elif is_cardless_emi and method == PaymentMethod.EMI:
        fee_rate = CARDLESS_EMI_FEE_RATE
    else:
        fee_rate = STANDARD_FEE_RATE

    mdr_paise = round(gross_amount_paise * float(fee_rate))
    gst_on_mdr_paise = round(mdr_paise * float(GST_RATE))
    net_amount_paise = gross_amount_paise - mdr_paise - gst_on_mdr_paise

    return SettlementBreakdown(
        gross_amount_paise=gross_amount_paise,
        mdr_paise=mdr_paise,
        gst_on_mdr_paise=gst_on_mdr_paise,
        net_amount_paise=net_amount_paise,
        settlement_note="T+2 business days, batched with other settlements, matched by settlement_id not bank UTR",
    )
