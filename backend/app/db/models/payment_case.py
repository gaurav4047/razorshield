import enum
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
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


class PaymentMethod(str, enum.Enum):
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"


class PaymentContext(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"


class SubscriptionState(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    HALTED = "halted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FaultAttribution(str, enum.Enum):
    CUSTOMER_FAULT = "customer_fault"
    INFRASTRUCTURE_FAULT = "infrastructure_fault"
    UNKNOWN = "unknown"


class InterventionType(str, enum.Enum):
    SILENT_RETRY = "silent_retry"
    DELAYED_RETRY_NOTIFY = "delayed_retry_notify"
    ESCALATE_HUMAN = "escalate_human"
    ALTERNATE_METHOD = "alternate_method"


class PaymentCaseStatus(str, enum.Enum):
    OPEN = "open"
    RETRIED = "retried"
    RECOVERED = "recovered"
    ESCALATED = "escalated"
    CLOSED_UNRECOVERED = "closed_unrecovered"


class PaymentCase(Base):
    __tablename__ = "payment_cases"

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

    razorpay_payment_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    razorpay_subscription_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(
            PaymentMethod,
            name="payment_method",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    context: Mapped[PaymentContext] = mapped_column(
        SQLEnum(
            PaymentContext,
            name="payment_context",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    subscription_state: Mapped[SubscriptionState | None] = mapped_column(
        SQLEnum(
            SubscriptionState,
            name="subscription_state",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
    )

    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False, server_default="INR", default="INR")

    failure_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_raw_reason: Mapped[str] = mapped_column(Text, nullable=False)

    attempt_number: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1", default=1)

    fault_attribution: Mapped[FaultAttribution] = mapped_column(
        SQLEnum(
            FaultAttribution,
            name="fault_attribution",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=FaultAttribution.UNKNOWN.value,
        default=FaultAttribution.UNKNOWN,
    )
    classified_root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)

    recommended_intervention: Mapped[InterventionType | None] = mapped_column(
        SQLEnum(
            InterventionType,
            name="intervention_type",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
    )
    npci_execution_window_conflict: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        default=False,
    )

    status: Mapped[PaymentCaseStatus] = mapped_column(
        SQLEnum(
            PaymentCaseStatus,
            name="payment_case_status",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=PaymentCaseStatus.OPEN.value,
        default=PaymentCaseStatus.OPEN,
    )
    retry_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0", default=0)
    last_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    buyer_archetype: Mapped[str | None] = mapped_column(Text, nullable=True)
    razorpay_payment_link_id: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    batch: Mapped["Batch"] = relationship("Batch", back_populates="payment_cases")

    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="chk_payment_cases_amount_paise_positive"),
        Index("idx_payment_cases_batch_status", "batch_id", "status"),
        Index(
            "idx_payment_cases_subscription",
            "razorpay_subscription_id",
            postgresql_where=text("razorpay_subscription_id IS NOT NULL"),
        ),
    )
