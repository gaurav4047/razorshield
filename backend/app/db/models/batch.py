import uuid
from datetime import datetime
from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    payment_cases: Mapped[list["PaymentCase"]] = relationship(
        "PaymentCase",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    abandoned_orders: Mapped[list["AbandonedOrder"]] = relationship(
        "AbandonedOrder",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list["AuditLogEntry"]] = relationship(
        "AuditLogEntry",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
