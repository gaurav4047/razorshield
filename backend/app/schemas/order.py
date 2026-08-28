import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.db.models.order import AbandonedOrderStatus


class AbandonedOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_id: uuid.UUID
    razorpay_order_id: str
    customer_name: str
    customer_contact: str
    customer_email: str
    amount_paise: int
    currency: str
    order_created_at: datetime
    abandonment_detected_at: datetime | None = None
    nudge_sent: bool
    nudge_sent_at: datetime | None = None
    razorpay_payment_link_id: str | None = None
    status: AbandonedOrderStatus
    created_at: datetime
    updated_at: datetime
