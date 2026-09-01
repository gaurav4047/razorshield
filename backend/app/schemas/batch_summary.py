import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    description: str | None = None
    created_at: datetime


class UnrecoveredExceptionItem(BaseModel):
    reference: str
    case_type: str
    status: str
    amount_paise: int
    reason: str | None = None


class ExceptionBreakdown(BaseModel):
    low_value_floor_skipped: int = 0
    disputed_invoices_halted: int = 0
    hard_declines_halted: int = 0
    samadhaan_filing_pending: int = 0


class BatchSummary(BaseModel):
    batch_id: uuid.UUID
    label: str
    total_cases: int
    total_at_risk_paise: int
    total_at_risk_inr: float
    gross_recovered_paise: int
    gross_recovered_inr: float
    mdr_fees_paise: int
    gst_on_mdr_paise: int
    net_recovered_paise: int
    net_recovered_inr: float
    total_interest_accrued_paise: int
    total_interest_accrued_inr: float
    recovery_rate: float
    partially_paid_count: int = 0
    partially_paid_amount_paise: int = 0
    partially_paid_amount_inr: float = 0.0
    exception_count: int = 0
    exceptions_breakdown: ExceptionBreakdown = ExceptionBreakdown()
    exceptions: list[UnrecoveredExceptionItem] = []
    modules: dict[str, dict] = {}
