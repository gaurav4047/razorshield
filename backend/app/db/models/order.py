import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AbandonedOrderStatus(str, enum.Enum):
    OPEN = "open"
    NUDGED = "nudged"
    RECOVERED = "recovered"
    EXPIRED_UNRECOVERED = "expired_unrecovered"
    SKIPPED_LOW_VALUE = "skipped_low_value"


class AbandonedOrder(Base):
    __tablename__ = "abandoned_orders"

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

    razorpay_order_id: Mapped[str] = mapped_column(Text, nullable=False)
    customer_name: Mapped[str] = mapped_column(Text, nullable=False)
    customer_contact: Mapped[str] = mapped_column(Text, nullable=False)
    customer_email: Mapped[str] = mapped_column(Text, nullable=False)

    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False, server_default="INR", default="INR")

    order_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    abandonment_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    nudge_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    nudge_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    razorpay_payment_link_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[AbandonedOrderStatus] = mapped_column(
        SQLEnum(
            AbandonedOrderStatus,
            name="abandoned_order_status",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=AbandonedOrderStatus.OPEN.value,
        default=AbandonedOrderStatus.OPEN,
    )

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

    batch: Mapped["Batch"] = relationship("Batch", back_populates="abandoned_orders")

    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="chk_abandoned_orders_amount_paise_positive"),
        Index("idx_abandoned_orders_batch_status", "batch_id", "status"),
    )
