from datetime import date
from typing import Literal
from pydantic import BaseModel


class SignalParsingOutput(BaseModel):
    classified_root_cause: str
    fault_attribution: Literal["customer_fault", "infrastructure_fault"]
    confidence: float
    brief_reasoning: str


class ReplyClassificationOutput(BaseModel):
    classified_as: Literal["promise_to_pay", "claims_already_paid", "dispute", "stall", "unclear"]
    confidence: float
    promised_date: date | None = None
    promised_amount_paise: int | None = None
    brief_reasoning: str


class MessageDraftOutput(BaseModel):
    message_text: str
    cites_interest_figure: bool


class ConflictingSignalOutput(BaseModel):
    recommended_intervention: Literal["silent_retry", "delayed_retry_notify", "escalate_human", "alternate_method"]
    agrees_with_default: bool
    reasoning: str


class BatchPatternOutput(BaseModel):
    pattern_found: bool
    pattern_description: str | None = None
    affected_case_count: int | None = None
    confidence: float
