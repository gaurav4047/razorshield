from datetime import date
from typing import TypedDict


class RungDefinition(TypedDict):
    rung: int
    action_name: str
    tone: str
    cites_interest: bool
    requires_human_approval: bool


RUNG_METADATA: dict[int, RungDefinition] = {
    0: {
        "rung": 0,
        "action_name": "none",
        "tone": "none",
        "cites_interest": False,
        "requires_human_approval": False,
    },
    1: {
        "rung": 1,
        "action_name": "first_reminder_with_payment_link",
        "tone": "neutral_informational",
        "cites_interest": False,
        "requires_human_approval": False,
    },
    2: {
        "rung": 2,
        "action_name": "second_reminder_with_interest",
        "tone": "firmer_factual",
        "cites_interest": True,
        "requires_human_approval": False,
    },
    3: {
        "rung": 3,
        "action_name": "formal_notice_cc_controller",
        "tone": "formal",
        "cites_interest": True,
        "requires_human_approval": False,
    },
    4: {
        "rung": 4,
        "action_name": "draft_msme_samadhaan_filing",
        "tone": "escalation",
        "cites_interest": True,
        "requires_human_approval": True,
    },
}


def compute_escalation_rung(
    statutory_due_date: date,
    as_of_date: date,
    broken_promise_count: int = 0,
) -> int:
    if broken_promise_count >= 3:
        return 4

    if as_of_date < statutory_due_date:
        return 0

    days_overdue = (as_of_date - statutory_due_date).days

    if days_overdue < 7:
        return 1
    if days_overdue < 14:
        return 2
    if days_overdue < 30:
        return 3
    return 4
