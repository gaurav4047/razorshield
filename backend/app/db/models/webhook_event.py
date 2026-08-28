from datetime import datetime
from typing import Any
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RawWebhookEvent(Base):
    __tablename__ = "raw_webhook_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    razorpay_event_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    signature_verified: Mapped[bool] = mapped_column(Boolean, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "idx_raw_webhook_events_dedup",
            "razorpay_event_id",
            unique=True,
            postgresql_where=text("razorpay_event_id IS NOT NULL"),
        ),
        Index(
            "idx_raw_webhook_events_unprocessed",
            "processed",
            postgresql_where=text("processed = false"),
        ),
    )
