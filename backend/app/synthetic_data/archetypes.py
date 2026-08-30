from dataclasses import dataclass
from typing import Literal
from app.db.models.payment_case import PaymentContext, PaymentMethod


@dataclass(frozen=True)
class ArchetypeDefinition:
    name: str
    module: Literal["A", "B", "C"]
    share_percentage: float
    description: str
    min_floor: int = 3  # General safety floor of 3 for every archetype


# ==============================================================================
# Module A — Payment & Mandate Failure Archetypes (Target: 60 cases)
# ==============================================================================
MODULE_A_ARCHETYPES: dict[str, ArchetypeDefinition] = {
    "transient_infra_glitch": ArchetypeDefinition(
        name="transient_infra_glitch",
        module="A",
        share_percentage=20.0,
        description="Infrastructure fault (issuer timeout, session timeout, network glitch). Silent retry succeeds.",
        min_floor=3,
    ),
    "npci_window_blocked": ArchetypeDefinition(
        name="npci_window_blocked",
        module="A",
        share_percentage=15.0,
        description="UPI AutoPay debit attempted in blocked 10:00-13:00 IST window. Rescheduled successfully.",
        min_floor=5,  # Higher floor of 5 specifically for pattern-detection sample size requirement
    ),
    "insufficient_balance_recovers": ArchetypeDefinition(
        name="insufficient_balance_recovers",
        module="A",
        share_percentage=15.0,
        description="Customer-fault low balance; retries successfully after delayed notification (salary cycle).",
        min_floor=3,
    ),
    "insufficient_balance_persists": ArchetypeDefinition(
        name="insufficient_balance_persists",
        module="A",
        share_percentage=10.0,
        description="Customer-fault low balance; fails on retry as well, remains in honest exception list.",
        min_floor=3,
    ),
    "hard_decline_card": ArchetypeDefinition(
        name="hard_decline_card",
        module="A",
        share_percentage=10.0,
        description="Hard decline (card expired or stolen). Never retried; routes straight to alternate method.",
        min_floor=3,
    ),
    "wallet_kyc_frozen": ArchetypeDefinition(
        name="wallet_kyc_frozen",
        module="A",
        share_percentage=10.0,
        description="Wallet KYC lapsed or freeze. Routes to alternate payment link.",
        min_floor=3,
    ),
    "emi_ineligible": ArchetypeDefinition(
        name="emi_ineligible",
        module="A",
        share_percentage=8.0,
        description="Card ineligible for EMI or credit utilization exceeded. Routes to alternate method.",
        min_floor=3,
    ),
    "halted_subscription_recovers": ArchetypeDefinition(
        name="halted_subscription_recovers",
        module="A",
        share_percentage=7.0,
        description="Halted subscription recovered via single recovery payment link.",
        min_floor=3,
    ),
    "halted_subscription_unrecovered": ArchetypeDefinition(
        name="halted_subscription_unrecovered",
        module="A",
        share_percentage=3.0,
        description="Halted subscription recovery link ignored; stays in unrecovered exception list.",
        min_floor=3,
    ),
    "gateway_sync_gap": ArchetypeDefinition(
        name="gateway_sync_gap",
        module="A",
        share_percentage=2.0,
        description="Gateway sync gap in netbanking. Mandatory hard override to escalate_human; never retried.",
        min_floor=3,
    ),
}

# ==============================================================================
# Module B — B2B Receivables Archetypes (Target: 50 cases)
# ==============================================================================
MODULE_B_ARCHETYPES: dict[str, ArchetypeDefinition] = {
    "pays_after_reminder_1": ArchetypeDefinition(
        name="pays_after_reminder_1",
        module="B",
        share_percentage=30.0,
        description="Pays in full shortly after initial rung 1 reminder.",
        min_floor=3,
    ),
    "promise_then_keeps_it": ArchetypeDefinition(
        name="promise_then_keeps_it",
        module="B",
        share_percentage=15.0,
        description="Replies with specific promise date and settles on time.",
        min_floor=3,
    ),
    "promise_then_break": ArchetypeDefinition(
        name="promise_then_break",
        module="B",
        share_percentage=15.0,
        description="Promises payment but defaults; triggers broken promise tracking up to rung 4 cap.",
        min_floor=3,
    ),
    "disputes_invoice": ArchetypeDefinition(
        name="disputes_invoice",
        module="B",
        share_percentage=10.0,
        description="Replies with genuine dispute; triggers immediate dispute_halt stopping rule.",
        min_floor=3,
    ),
    "partial_payer": ArchetypeDefinition(
        name="partial_payer",
        module="B",
        share_percentage=10.0,
        description="Pays partial amount via payment link, status becomes partially_paid.",
        min_floor=3,
    ),
    "silent_ghost": ArchetypeDefinition(
        name="silent_ghost",
        module="B",
        share_percentage=15.0,
        description="Never responds; escalates through rungs 1->4 to pending human approval.",
        min_floor=3,
    ),
    "pays_immediately_no_nudge_needed": ArchetypeDefinition(
        name="pays_immediately_no_nudge_needed",
        module="B",
        share_percentage=5.0,
        description="Paid before statutory due date; control group where no action is taken.",
        min_floor=3,
    ),
}

# ==============================================================================
# Module C — Checkout Abandonment Archetypes (Target: 25 cases)
# ==============================================================================
MODULE_C_ARCHETYPES: dict[str, ArchetypeDefinition] = {
    "converts_after_nudge": ArchetypeDefinition(
        name="converts_after_nudge",
        module="C",
        share_percentage=40.0,
        description="Converts via Payment Link shortly after single nudge is dispatched.",
        min_floor=3,
    ),
    "ignores_nudge": ArchetypeDefinition(
        name="ignores_nudge",
        module="C",
        share_percentage=40.0,
        description="Nudge sent once but customer ignores; stays in nudged exception list.",
        min_floor=3,
    ),
    "below_value_floor": ArchetypeDefinition(
        name="below_value_floor",
        module="C",
        share_percentage=20.0,
        description="Order below Rs 200 floor; skipped immediately without contact.",
        min_floor=3,
    ),
}
