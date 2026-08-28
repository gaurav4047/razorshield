import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.db.models.invoice import InvoiceStatus, PromiseStatus


class InvoicePromiseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    source_text: str
    promised_pay_by_date: date
    promised_amount_paise: int | None = None
    classified_by: str
    confidence_score: Decimal | None = None
    status: PromiseStatus
    resolved_at: datetime | None = None
    created_at: datetime


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_id: uuid.UUID
    invoice_number: str
    buyer_name: str
    buyer_contact: str
    buyer_email: str
    supplier_is_msme: bool
    has_written_agreement: bool
    amount_paise: int
    amount_paid_paise: int
    currency: str
    invoice_date: date
    goods_accepted_date: date
    statutory_due_date: date
    status: InvoiceStatus
    current_rung: int
    dispute_flag: bool
    broken_promise_count: int
    buyer_archetype: str
    razorpay_payment_link_id: str | None = None
    last_contact_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    promises: list[InvoicePromiseRead] = []
