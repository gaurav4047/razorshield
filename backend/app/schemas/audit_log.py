import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict
from app.db.models.audit_log import CaseType, PipelineStage


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: uuid.UUID
    case_type: CaseType
    case_id: uuid.UUID
    timestamp: datetime
    stage: PipelineStage
    rule_suggested_action: str | None = None
    ai_reasoning_text: str | None = None
    stopping_rules_checked: list[dict[str, Any]] = []
    final_action: str
    reason: str
    gross_amount_paise: int | None = None
    mdr_paise: int | None = None
    gst_on_mdr_paise: int | None = None
    net_amount_paise: int | None = None
    computed_interest_accrued_paise: int | None = None
    razorpay_reference: str | None = None
    created_at: datetime
