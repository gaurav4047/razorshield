from app.config import settings
from app.domain_logic.escalation_ladder import RUNG_METADATA


def draft_reminder_message(
    invoice_number: str,
    buyer_name: str,
    amount_paise: int,
    days_overdue: int,
    current_rung: int,
    computed_interest_paise: int,
    supplier_is_msme: bool,
    payment_link_url: str | None = None,
) -> str:
    amount_inr = amount_paise / 100
    interest_inr = computed_interest_paise / 100
    total_due_inr = amount_inr + (interest_inr if supplier_is_msme and current_rung >= 2 else 0)

    link_str = f" You can settle this invoice directly via: {payment_link_url}" if payment_link_url else ""

    if current_rung == 1:
        return (
            f"Dear {buyer_name}, this is a gentle reminder that invoice {invoice_number} for Rs {amount_inr:,.2f} "
            f"has reached its statutory due date.{link_str} Please process payment at your earliest convenience."
        )

    if current_rung == 2:
        if supplier_is_msme:
            return (
                f"Dear {buyer_name}, invoice {invoice_number} is now {days_overdue} days overdue (Principal: Rs {amount_inr:,.2f}). "
                f"Per Section 16 of the MSMED Act 2006, statutory penal compound interest of Rs {interest_inr:,.2f} has accrued, "
                f"bringing the total payable amount to Rs {total_due_inr:,.2f}.{link_str} Please settle immediately to avoid further accrual."
            )
        else:
            return (
                f"Dear {buyer_name}, invoice {invoice_number} for Rs {amount_inr:,.2f} is now {days_overdue} days overdue.{link_str} "
                f"Please arrange for immediate clearance as per standard commercial terms."
            )

    if current_rung == 3:
        if supplier_is_msme:
            return (
                f"FORMAL OVERDUE NOTICE: Invoice {invoice_number} remains unpaid ({days_overdue} days overdue). "
                f"Total outstanding is Rs {total_due_inr:,.2f} (Principal: Rs {amount_inr:,.2f} + Statutory MSMED Compound Interest: Rs {interest_inr:,.2f}).{link_str} "
                f"This matter is being escalated to the finance controller."
            )
        else:
            return (
                f"FORMAL OVERDUE NOTICE: Invoice {invoice_number} is {days_overdue} days overdue for Rs {amount_inr:,.2f}.{link_str} "
                f"This matter is being escalated to your finance controller."
            )

    if current_rung == 4:
        return (
            f"FINAL DEMAND NOTICE BEFORE STATUTORY FILING: Invoice {invoice_number} is {days_overdue} days overdue. "
            f"Total due under MSMED Act is Rs {total_due_inr:,.2f} (Principal: Rs {amount_inr:,.2f} + Interest: Rs {interest_inr:,.2f}). "
            f"Documentation is being prepared for filing on the MSME Samadhaan portal."
        )

    return f"Reminder regarding invoice {invoice_number} for Rs {amount_inr:,.2f}."
