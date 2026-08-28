"""Initial schema setup

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

invoice_status = sa.Enum(
    "pending",
    "overdue",
    "disputed",
    "partially_paid",
    "pending_human_approval",
    "paid",
    "written_off",
    name="invoice_status",
)

promise_status = sa.Enum("pending", "kept", "broken", name="promise_status")

payment_method = sa.Enum("upi", "card", "netbanking", "wallet", "emi", name="payment_method")
payment_context = sa.Enum("subscription", "one_time", name="payment_context")
subscription_state = sa.Enum("active", "pending", "halted", "completed", "cancelled", name="subscription_state")
fault_attribution = sa.Enum("customer_fault", "infrastructure_fault", "unknown", name="fault_attribution")
intervention_type = sa.Enum("silent_retry", "delayed_retry_notify", "escalate_human", "alternate_method", name="intervention_type")
payment_case_status = sa.Enum("open", "retried", "recovered", "escalated", "closed_unrecovered", name="payment_case_status")

abandoned_order_status = sa.Enum("open", "nudged", "recovered", "expired_unrecovered", "skipped_low_value", name="abandoned_order_status")

case_type = sa.Enum("invoice", "payment_case", "abandoned_order", name="case_type")
pipeline_stage = sa.Enum("diagnose", "policy_gate", "execute", "audit", name="pipeline_stage")


def upgrade() -> None:
    # 1. Enable pgcrypto extension
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # 2. batches table
    op.create_table(
        "batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. invoices table
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_number", sa.Text(), nullable=False),
        sa.Column("buyer_name", sa.Text(), nullable=False),
        sa.Column("buyer_contact", sa.Text(), nullable=False),
        sa.Column("buyer_email", sa.Text(), nullable=False),
        sa.Column("supplier_is_msme", sa.Boolean(), nullable=False),
        sa.Column("has_written_agreement", sa.Boolean(), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("amount_paid_paise", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("currency", sa.Text(), server_default="INR", nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("goods_accepted_date", sa.Date(), nullable=False),
        sa.Column("statutory_due_date", sa.Date(), nullable=False),
        sa.Column("status", invoice_status, server_default="pending", nullable=False),
        sa.Column("current_rung", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("dispute_flag", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("broken_promise_count", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("buyer_archetype", sa.Text(), nullable=False),
        sa.Column("razorpay_payment_link_id", sa.Text(), nullable=True),
        sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount_paise > 0", name="chk_invoices_amount_paise_positive"),
        sa.CheckConstraint("amount_paid_paise >= 0", name="chk_invoices_amount_paid_non_negative"),
        sa.CheckConstraint("current_rung BETWEEN 0 AND 4", name="chk_invoices_current_rung_range"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_invoices_batch_status", "invoices", ["batch_id", "status"])
    op.create_index(
        "idx_invoices_statutory_due_date",
        "invoices",
        ["statutory_due_date"],
        postgresql_where=sa.text("status IN ('pending', 'overdue')"),
    )

    # invoice_promises table
    op.create_table(
        "invoice_promises",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("promised_pay_by_date", sa.Date(), nullable=False),
        sa.Column("promised_amount_paise", sa.BigInteger(), nullable=True),
        sa.Column("classified_by", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("status", promise_status, server_default="pending", nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_invoice_promises_invoice", "invoice_promises", ["invoice_id"])

    # 4. payment_cases table
    op.create_table(
        "payment_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("razorpay_payment_id", sa.Text(), nullable=True),
        sa.Column("razorpay_subscription_id", sa.Text(), nullable=True),
        sa.Column("razorpay_order_id", sa.Text(), nullable=True),
        sa.Column("method", payment_method, nullable=False),
        sa.Column("context", payment_context, nullable=False),
        sa.Column("subscription_state", subscription_state, nullable=True),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.Text(), server_default="INR", nullable=False),
        sa.Column("failure_code", sa.Text(), nullable=True),
        sa.Column("failure_raw_reason", sa.Text(), nullable=False),
        sa.Column("attempt_number", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("fault_attribution", fault_attribution, server_default="unknown", nullable=False),
        sa.Column("classified_root_cause", sa.Text(), nullable=True),
        sa.Column("diagnosis_confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("recommended_intervention", intervention_type, nullable=True),
        sa.Column("npci_execution_window_conflict", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("status", payment_case_status, server_default="open", nullable=False),
        sa.Column("retry_count", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("last_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("razorpay_payment_link_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount_paise > 0", name="chk_payment_cases_amount_paise_positive"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_payment_cases_batch_status", "payment_cases", ["batch_id", "status"])
    op.create_index(
        "idx_payment_cases_subscription",
        "payment_cases",
        ["razorpay_subscription_id"],
        postgresql_where=sa.text("razorpay_subscription_id IS NOT NULL"),
    )

    # 5. abandoned_orders table
    op.create_table(
        "abandoned_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("razorpay_order_id", sa.Text(), nullable=False),
        sa.Column("customer_name", sa.Text(), nullable=False),
        sa.Column("customer_contact", sa.Text(), nullable=False),
        sa.Column("customer_email", sa.Text(), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.Text(), server_default="INR", nullable=False),
        sa.Column("order_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("abandonment_detected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("nudge_sent", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("nudge_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("razorpay_payment_link_id", sa.Text(), nullable=True),
        sa.Column("status", abandoned_order_status, server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount_paise > 0", name="chk_abandoned_orders_amount_paise_positive"),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_abandoned_orders_batch_status", "abandoned_orders", ["batch_id", "status"])

    # 6. audit_log table
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_type", case_type, nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("stage", pipeline_stage, nullable=False),
        sa.Column("rule_suggested_action", sa.Text(), nullable=True),
        sa.Column("ai_reasoning_text", sa.Text(), nullable=True),
        sa.Column("stopping_rules_checked", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("final_action", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("gross_amount_paise", sa.BigInteger(), nullable=True),
        sa.Column("mdr_paise", sa.BigInteger(), nullable=True),
        sa.Column("gst_on_mdr_paise", sa.BigInteger(), nullable=True),
        sa.Column("net_amount_paise", sa.BigInteger(), nullable=True),
        sa.Column("computed_interest_accrued_paise", sa.BigInteger(), nullable=True),
        sa.Column("razorpay_reference", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_log_batch_time", "audit_log", ["batch_id", sa.text("timestamp DESC")])
    op.create_index("idx_audit_log_case", "audit_log", ["case_type", "case_id", sa.text("timestamp DESC")])

    # 7. raw_webhook_events table
    op.create_table(
        "raw_webhook_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("razorpay_event_id", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("signature_verified", sa.Boolean(), nullable=False),
        sa.Column("processed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_raw_webhook_events_dedup",
        "raw_webhook_events",
        ["razorpay_event_id"],
        unique=True,
        postgresql_where=sa.text("razorpay_event_id IS NOT NULL"),
    )
    op.create_index(
        "idx_raw_webhook_events_unprocessed",
        "raw_webhook_events",
        ["processed"],
        postgresql_where=sa.text("processed = false"),
    )


def downgrade() -> None:
    op.drop_table("raw_webhook_events")
    op.drop_table("audit_log")
    op.execute("DROP TYPE pipeline_stage;")
    op.execute("DROP TYPE case_type;")
    op.drop_table("abandoned_orders")
    op.execute("DROP TYPE abandoned_order_status;")
    op.drop_table("payment_cases")
    op.execute("DROP TYPE payment_case_status;")
    op.execute("DROP TYPE intervention_type;")
    op.execute("DROP TYPE fault_attribution;")
    op.execute("DROP TYPE subscription_state;")
    op.execute("DROP TYPE payment_context;")
    op.execute("DROP TYPE payment_method;")
    op.drop_table("invoice_promises")
    op.execute("DROP TYPE promise_status;")
    op.drop_table("invoices")
    op.execute("DROP TYPE invoice_status;")
    op.drop_table("batches")
