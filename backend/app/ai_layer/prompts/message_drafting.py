import re
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai_layer.model_router import AiTask, get_model_for_task
from app.ai_layer.output_schemas import MessageDraftOutput
from app.config import settings
from app.domain_logic.escalation_ladder import RUNG_METADATA


async def draft_b2b_reminder_gemini(
    invoice_number: str,
    buyer_name: str,
    amount_paise: int,
    days_overdue: int,
    current_rung: int,
    computed_interest_paise: int,
    supplier_is_msme: bool,
    register: str = "standard business English",
    payment_link_url: str | None = None,
) -> MessageDraftOutput:
    amount_inr = amount_paise / 100
    interest_inr = computed_interest_paise / 100
    rung_info = RUNG_METADATA.get(current_rung, {})
    rung_tone = rung_info.get("tone", "polite")

    system_prompt = (
        "Draft a payment reminder message for a B2B invoice. Use the exact tone "
        "specified for this escalation rung. You MUST cite only the exact interest "
        "figure provided — never calculate or state any other number.\n\n"
        f"Invoice: {invoice_number}, amount Rs {amount_inr:,.2f}, {days_overdue} days overdue\n"
        f"Escalation rung: {current_rung} — tone: {rung_tone}\n"
        f"Computed accrued interest (use this exact figure, do not alter it): Rs {interest_inr:,.2f}\n"
        f"Statutory basis: {'MSMED Act 2006, Sections 15-16' if supplier_is_msme else 'standard commercial terms — do NOT mention MSMED Act for this invoice'}\n"
        f"Register: {register}\n\n"
        "Do not include any threat or claim beyond what is stated above. Do not imply "
        "legal action has been filed — at most, reference that continued non-payment "
        "may lead to formal escalation."
    )

    user_prompt = (
        f"Recipient: {buyer_name}\n"
        f"Payment Link: {payment_link_url or 'Included upon dispatch'}\n"
        "Generate the reminder text."
    )

    try:
        model = get_model_for_task(AiTask.MESSAGE_DRAFTING)
        structured_llm = model.with_structured_output(MessageDraftOutput)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        result: MessageDraftOutput = await structured_llm.ainvoke(messages)

        if supplier_is_msme and current_rung >= 2 and computed_interest_paise > 0:
            formatted_commas = f"{interest_inr:,.2f}"
            formatted_plain = f"{interest_inr:.2f}"
            interest_int_str = str(int(interest_inr))
            cites = (
                formatted_commas in result.message_text
                or formatted_plain in result.message_text
                or interest_int_str in result.message_text
            )
            result.cites_interest_figure = cites

        return result
    except Exception:
        fallback_text = draft_reminder_message(
            invoice_number=invoice_number,
            buyer_name=buyer_name,
            amount_paise=amount_paise,
            days_overdue=days_overdue,
            current_rung=current_rung,
            computed_interest_paise=computed_interest_paise,
            supplier_is_msme=supplier_is_msme,
            payment_link_url=payment_link_url,
        )
        return MessageDraftOutput(
            message_text=fallback_text,
            cites_interest_figure=(current_rung >= 2 and supplier_is_msme and computed_interest_paise > 0),
        )


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
