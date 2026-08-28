import enum
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CaseType(str, enum.Enum):
    INVOICE = "invoice"
    PAYMENT_CASE = "payment_case"
    ABANDONED_ORDER = "abandoned_order"


class PipelineStage(str, enum.Enum):
    DIAGNOSE = "diagnose"
    POLICY_GATE = "policy_gate"
    EXECUTE = "execute"
    AUDIT = "audit"


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=False,
    )

    case_type: Mapped[CaseType] = mapped_column(
        SQLEnum(CaseType, name="case_type", native_enum=True),
        nullable=False,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    stage: Mapped[PipelineStage] = mapped_column(
        SQLEnum(PipelineStage, name="pipeline_stage", native_enum=True),
        nullable=False,
    )

    rule_suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_reasoning_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    stopping_rules_checked: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        default=list,
    )

    final_action: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    gross_amount_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mdr_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    gst_on_mdr_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    net_amount_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    computed_interest_accrued_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    razorpay_reference: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    batch: Mapped["Batch"] = relationship("Batch", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_log_batch_time", "batch_id", timestamp.desc()),
        Index("idx_audit_log_case", "case_type", "case_id", timestamp.desc()),
    )
