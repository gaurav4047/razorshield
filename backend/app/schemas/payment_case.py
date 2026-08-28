import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.db.models.payment_case import (
    FaultAttribution,
    InterventionType,
    PaymentCaseStatus,
    PaymentContext,
    PaymentMethod,
    SubscriptionState,
)


class PaymentCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_id: uuid.UUID
    razorpay_payment_id: str | None = None
    razorpay_subscription_id: str | None = None
    razorpay_order_id: str | None = None
    method: PaymentMethod
    context: PaymentContext
    subscription_state: SubscriptionState | None = None
    amount_paise: int
    currency: str
    failure_code: str | None = None
    failure_raw_reason: str
    attempt_number: int
    fault_attribution: FaultAttribution
    classified_root_cause: str | None = None
    diagnosis_confidence: Decimal | None = None
    recommended_intervention: InterventionType | None = None
    npci_execution_window_conflict: bool
    status: PaymentCaseStatus
    retry_count: int
    last_action_at: datetime | None = None
    razorpay_payment_link_id: str | None = None
    created_at: datetime
    updated_at: datetime
