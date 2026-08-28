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


class BatchSummary(BaseModel):
    batch_id: uuid.UUID
    total_at_risk_paise: int
    gross_recovered_paise: int
    net_recovered_paise: int
    recovery_rate_pct: float
    exception_count: int
    exceptions: list[UnrecoveredExceptionItem] = []
