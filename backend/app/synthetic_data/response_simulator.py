from datetime import date, timedelta
import random
from typing import Any

from app.razorpay_client.client import create_payment_link

# At least 4-5 distinct realistic phrasings per response category per 06_synthetic_data.md §6
DISPUTE_MESSAGES = [
    "We dispute this invoice amount. 25% of the delivered units were defective and rejected by our QC team.",
    "This amount is incorrect. We agreed with your sales rep on a 15% trade discount for this bulk lot.",
    "Goods received were damaged in transit and we have already filed a formal damage claim. We will not pay until resolved.",
    "We never authorized or received the supplementary service charges billed in line item 3. Please revise the bill.",
    "We are contesting this billing. The delivery was over two weeks late, causing production downtime on our end.",
]

PROMISE_MESSAGES = [
    "Our accounts department will process this payment in the upcoming weekly cycle on Friday.",
    "Approved by finance controller. Payment of Rs {amount} will be disbursed by next Tuesday.",
    "We have scheduled the RTGS transfer for the 15th of this month.",
    "Sorry for the delay, our director was traveling. We will clear the outstanding balance by {date}.",
    "The payment voucher has been prepared and funds will be released within 5 business days.",
]

STALL_MESSAGES = [
    "Our finance head is currently out of the office. We will look into this once she returns.",
    "Checking with our internal accounts and warehouse team to verify the delivery challan.",
    "We are currently undergoing our quarterly internal financial audit; payments are temporarily queued.",
    "Our ERP system is undergoing maintenance this week. We will get back to you shortly.",
    "Under review with our procurement division. We will update you soon.",
]

CLAIMS_PAID_MESSAGES = [
    "We have already transferred the full amount yesterday via NEFT (UTR ref: SBIN009827183). Please verify your statement.",
    "Payment was already cleared last week via IMPS. Kindly check with your bank.",
    "We settled this invoice along with last month's batch. Reference transaction id: HDFC8829104.",
    "Check was deposited at your branch 3 days ago. It should reflect in your account today.",
    "Our records show this bill was paid on the 28th. Please re-reconcile on your end.",
]


def get_simulated_buyer_reply(archetype: str, amount_inr: float = 50000.0) -> str | None:
    if archetype == "disputes_invoice":
        return random.choice(DISPUTE_MESSAGES)

    if archetype in ("promise_then_keeps_it", "promise_then_break"):
        promised_dt = (date.today() + timedelta(days=random.randint(3, 7))).strftime("%Y-%m-%d")
        msg_template = random.choice(PROMISE_MESSAGES)
        return msg_template.format(amount=f"{amount_inr:,.2f}", date=promised_dt)

    return None


def should_settle_at_rung(archetype: str, current_rung: int, is_second_chance_case: bool = False) -> bool:
    """Evaluates whether an archetype settles at the current escalation rung."""
    if archetype == "pays_immediately_no_nudge_needed" and current_rung == 0:
        return True
    if archetype == "pays_after_reminder_1" and current_rung == 1:
        return True
    if archetype == "promise_then_keeps_it" and current_rung in (1, 2):
        return True
    # Second-chance recovery at Rung 3 grounded in MSME Samadhaan pre-hearing data
    if is_second_chance_case and current_rung == 3 and archetype in ("promise_then_break", "silent_ghost"):
        return True
    return False


async def trigger_live_payment_link_recovery(
    amount_paise: int,
    reference_id: str,
    description: str,
    customer_name: str = "Test Customer",
    customer_email: str = "customer@example.com",
    customer_contact: str = "+919876543210",
) -> dict[str, Any]:
    return await create_payment_link(
        amount_paise=amount_paise,
        reference_id=reference_id,
        description=description,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_contact=customer_contact,
    )
