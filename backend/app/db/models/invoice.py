import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    OVERDUE = "overdue"
    DISPUTED = "disputed"
    PARTIALLY_PAID = "partially_paid"
    PENDING_HUMAN_APPROVAL = "pending_human_approval"
    PAID = "paid"
    WRITTEN_OFF = "written_off"


class PromiseStatus(str, enum.Enum):
    PENDING = "pending"
    KEPT = "kept"
    BROKEN = "broken"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=False,
    )

    invoice_number: Mapped[str] = mapped_column(Text, nullable=False)
    buyer_name: Mapped[str] = mapped_column(Text, nullable=False)
    buyer_contact: Mapped[str] = mapped_column(Text, nullable=False)
    buyer_email: Mapped[str] = mapped_column(Text, nullable=False)

    supplier_is_msme: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    has_written_agreement: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)

    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_paid_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0", default=0)
    currency: Mapped[str] = mapped_column(Text, nullable=False, server_default="INR", default="INR")

    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    goods_accepted_date: Mapped[date] = mapped_column(Date, nullable=False)
    statutory_due_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[InvoiceStatus] = mapped_column(
        SQLEnum(
            InvoiceStatus,
            name="invoice_status",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=InvoiceStatus.PENDING.value,
        default=InvoiceStatus.PENDING,
    )
    current_rung: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default="0",
        default=0,
    )

    dispute_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    broken_promise_count: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default="0",
        default=0,
    )

    buyer_archetype: Mapped[str] = mapped_column(Text, nullable=False)
    razorpay_payment_link_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    batch: Mapped["Batch"] = relationship("Batch", back_populates="invoices")
    promises: Mapped[list["InvoicePromise"]] = relationship(
        "InvoicePromise",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="chk_invoices_amount_paise_positive"),
        CheckConstraint("amount_paid_paise >= 0", name="chk_invoices_amount_paid_non_negative"),
        CheckConstraint("current_rung BETWEEN 0 AND 4", name="chk_invoices_current_rung_range"),
        Index("idx_invoices_batch_status", "batch_id", "status"),
        Index(
            "idx_invoices_statutory_due_date",
            "statutory_due_date",
            postgresql_where=text("status IN ('pending', 'overdue')"),
        ),
    )


class InvoicePromise(Base):
    __tablename__ = "invoice_promises"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    promised_pay_by_date: Mapped[date] = mapped_column(Date, nullable=False)
    promised_amount_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    classified_by: Mapped[str] = mapped_column(Text, nullable=False, default="ai")
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)

    status: Mapped[PromiseStatus] = mapped_column(
        SQLEnum(
            PromiseStatus,
            name="promise_status",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=PromiseStatus.PENDING.value,
        default=PromiseStatus.PENDING,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="promises")

    __table_args__ = (
        Index("idx_invoice_promises_invoice", "invoice_id"),
    )
