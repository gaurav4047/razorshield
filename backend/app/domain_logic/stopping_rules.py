from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from typing import Any

from app.db.models.payment_case import FaultAttribution, InterventionType, PaymentContext, PaymentMethod
from app.domain_logic.intervention_types import HARD_DECLINE_ROOT_CAUSES

IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))
LOW_VALUE_FLOOR_PAISE = 20000  # Rs 200


@dataclass
class StoppingRuleCheck:
    rule: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass
class PolicyGateResult:
    allowed: bool
    final_action: str
    reason: str
    stopping_rules_checked: list[dict[str, Any]] = field(default_factory=list)
    rule_recommendation: str | None = None
    npci_window_conflict: bool = False
    reschedule_at: datetime | None = None


def is_within_npci_blocked_window(target_time: datetime) -> bool:
    ist_time = target_time.astimezone(IST_TIMEZONE)
    current_time = ist_time.time()
    # Blocked window: 10:00:00 to 13:00:00 IST
    return time(10, 0) <= current_time < time(13, 0)


def get_next_npci_allowed_window(target_time: datetime) -> datetime:
    ist_time = target_time.astimezone(IST_TIMEZONE)
    # Reschedule to 13:00:01 IST of the same day
    rescheduled = ist_time.replace(hour=13, minute=0, second=1, microsecond=0)
    return rescheduled.astimezone(timezone.utc)


def check_module_a_policy_gate(
    method: PaymentMethod,
    context: PaymentContext,
    classified_root_cause: str | None,
    recommended_intervention: InterventionType | None,
    attempt_number: int = 1,
    retry_count: int = 0,
    last_action_at: datetime | None = None,
    now: datetime | None = None,
) -> PolicyGateResult:
    current_now = now or datetime.now(timezone.utc)
    rules_checked: list[StoppingRuleCheck] = []
    final_action = recommended_intervention.value if recommended_intervention else "escalate_human"
    allowed = True
    reason = "Policy gate approved recommended intervention."
    rule_rec = None
    npci_conflict = False
    reschedule_target = None

    # Rule 5: gateway_sync_gap_override
    if classified_root_cause == "gateway_data_sync_gap":
        rules_checked.append(
            StoppingRuleCheck(
                rule="gateway_sync_gap_override",
                passed=False,
                detail="Netbanking data sync gap detected; forcing human escalation to prevent double-charge",
            )
        )
        final_action = InterventionType.ESCALATE_HUMAN.value
        reason = "Gateway data sync gap requires human escalation"
        return PolicyGateResult(
            allowed=True,
            final_action=final_action,
            reason=reason,
            stopping_rules_checked=[r.to_dict() for r in rules_checked],
            rule_recommendation=recommended_intervention.value if recommended_intervention else None,
        )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="gateway_sync_gap_override",
                passed=True,
                detail="No gateway sync gap detected",
            )
        )

    # Rule 1: hard_decline_never_retry
    is_hard_decline = classified_root_cause in HARD_DECLINE_ROOT_CAUSES
    if is_hard_decline:
        if final_action in (InterventionType.SILENT_RETRY.value, InterventionType.DELAYED_RETRY_NOTIFY.value):
            rules_checked.append(
                StoppingRuleCheck(
                    rule="hard_decline_never_retry",
                    passed=False,
                    detail=f"Hard decline cause ({classified_root_cause}) cannot be retried; forcing alternate payment method",
                )
            )
            rule_rec = final_action
            final_action = InterventionType.ALTERNATE_METHOD.value
            reason = f"Hard decline ({classified_root_cause}) overridden to alternate_method"
        else:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="hard_decline_never_retry",
                    passed=True,
                    detail=f"Hard decline ({classified_root_cause}) routed to alternate_method",
                )
            )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="hard_decline_never_retry",
                passed=True,
                detail="Not a hard decline cause",
            )
        )

    # Rule 2: npci_execution_window & UPI retry ceiling (1 original + max 3 retries)
    if method == PaymentMethod.UPI:
        # Check retry ceiling
        if attempt_number > 4 or retry_count >= 3:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="npci_execution_window",
                    passed=False,
                    detail=f"NPCI AutoPay retry ceiling reached ({attempt_number} attempts, {retry_count} retries); forcing escalate_human",
                )
            )
            rule_rec = final_action
            final_action = InterventionType.ESCALATE_HUMAN.value
            reason = "NPCI retry ceiling reached"
        elif final_action in (InterventionType.SILENT_RETRY.value, InterventionType.DELAYED_RETRY_NOTIFY.value):
            if is_within_npci_blocked_window(current_now):
                npci_conflict = True
                reschedule_target = get_next_npci_allowed_window(current_now)
                rules_checked.append(
                    StoppingRuleCheck(
                        rule="npci_execution_window",
                        passed=False,
                        detail=f"Current time is inside blocked NPCI 10:00-13:00 IST window; rescheduled to {reschedule_target.isoformat()}",
                    )
                )
                reason = "Rescheduled outside NPCI peak window"
            else:
                rules_checked.append(
                    StoppingRuleCheck(
                        rule="npci_execution_window",
                        passed=True,
                        detail="Current execution time is within permitted NPCI window",
                    )
                )
        else:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="npci_execution_window",
                    passed=True,
                    detail="Action does not involve UPI charge execution",
                )
            )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="npci_execution_window",
                passed=True,
                detail="Non-UPI payment method",
            )
        )

    # Rule 3: retry_cap
    if context == PaymentContext.SUBSCRIPTION and method == PaymentMethod.CARD:
        if retry_count >= 1:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="retry_cap",
                    passed=False,
                    detail=f"Card subscription halted-link retry cap reached ({retry_count}); escalating to human",
                )
            )
            rule_rec = final_action
            final_action = InterventionType.ESCALATE_HUMAN.value
            reason = "Halted subscription retry cap exceeded"
        else:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="retry_cap",
                    passed=True,
                    detail="Subscription within single-recovery-link cap",
                )
            )
    elif method != PaymentMethod.UPI:
        if retry_count >= 3:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="retry_cap",
                    passed=False,
                    detail=f"Standard retry cap reached ({retry_count}); escalating to human",
                )
            )
            rule_rec = final_action
            final_action = InterventionType.ESCALATE_HUMAN.value
            reason = "Retry cap exceeded"
        else:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="retry_cap",
                    passed=True,
                    detail="Within standard retry cap",
                )
            )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="retry_cap",
                passed=True,
                detail="Covered under NPCI AutoPay rule",
            )
        )

    # Rule 4: customer_contact_cooldown (48 hours)
    if final_action in (InterventionType.DELAYED_RETRY_NOTIFY.value, InterventionType.ALTERNATE_METHOD.value):
        if last_action_at and (current_now - last_action_at) < timedelta(hours=48):
            hours_since = (current_now - last_action_at).total_seconds() / 3600
            rules_checked.append(
                StoppingRuleCheck(
                    rule="customer_contact_cooldown",
                    passed=False,
                    detail=f"Contact cooldown active ({hours_since:.1f}h since last contact, required 48h); action blocked",
                )
            )
            allowed = False
            final_action = "blocked_contact_cooldown"
            reason = "Blocked by 48-hour customer contact cooldown"
        else:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="customer_contact_cooldown",
                    passed=True,
                    detail="No contact cooldown restriction",
                )
            )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="customer_contact_cooldown",
                passed=True,
                detail="Non-customer facing action",
            )
        )

    # Rule 13: policy_gate_is_final
    rules_checked.append(
        StoppingRuleCheck(
            rule="policy_gate_is_final",
            passed=True,
            detail="Policy gate validation finalized",
        )
    )

    return PolicyGateResult(
        allowed=allowed,
        final_action=final_action,
        reason=reason,
        stopping_rules_checked=[r.to_dict() for r in rules_checked],
        rule_recommendation=rule_rec,
        npci_window_conflict=npci_conflict,
        reschedule_at=reschedule_target,
    )


def check_module_b_policy_gate(
    dispute_flag: bool,
    broken_promise_count: int,
    current_rung: int,
    target_rung: int,
    last_contact_at: datetime | None,
    computed_interest_paise: int | None,
    supplier_is_msme: bool,
    human_approved: bool = False,
    now: datetime | None = None,
) -> PolicyGateResult:
    current_now = now or datetime.now(timezone.utc)
    rules_checked: list[StoppingRuleCheck] = []
    allowed = True
    final_action = f"rung_{target_rung}_action"
    reason = f"Advanced to rung {target_rung}"
    rule_rec = None

    # Rule 6: dispute_halt (MUST be checked first)
    if dispute_flag:
        rules_checked.append(
            StoppingRuleCheck(
                rule="dispute_halt",
                passed=False,
                detail="Dispute active; all automated communication halted permanently",
            )
        )
        allowed = False
        final_action = "blocked_dispute_halt"
        reason = "Automated workflow halted due to active buyer dispute"
        return PolicyGateResult(
            allowed=False,
            final_action=final_action,
            reason=reason,
            stopping_rules_checked=[r.to_dict() for r in rules_checked],
        )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="dispute_halt",
                passed=True,
                detail="No dispute flagged",
            )
        )

    # Rule 7: broken_promise_cap (>= 3 broken promises forces rung 4)
    if broken_promise_count >= 3:
        if target_rung < 4:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="broken_promise_cap",
                    passed=False,
                    detail=f"{broken_promise_count} broken promises on file; forcing escalation to rung 4",
                )
            )
            rule_rec = final_action
            target_rung = 4
            final_action = "draft_msme_samadhaan_filing"
            reason = "3 or more broken promises forced rung 4 escalation"
        else:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="broken_promise_cap",
                    passed=True,
                    detail=f"{broken_promise_count} broken promises; already at rung 4",
                )
            )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="broken_promise_cap",
                passed=True,
                detail=f"{broken_promise_count} broken promises (cap is 3)",
            )
        )

    # Rule 8: contact_frequency_cap (7 days)
    if last_contact_at and (current_now - last_contact_at) < timedelta(days=7):
        days_since = (current_now - last_contact_at).total_seconds() / 86400
        rules_checked.append(
            StoppingRuleCheck(
                rule="contact_frequency_cap",
                passed=False,
                detail=f"Contact frequency cooldown active ({days_since:.1f} days since last contact, cap is 7 days)",
            )
        )
        allowed = False
        final_action = "blocked_contact_frequency_cap"
        reason = "Blocked by 7-day outbound contact frequency cap"
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="contact_frequency_cap",
                passed=True,
                detail="Contact frequency cap passed",
            )
        )

    # Rule 9: no_fabricated_claims
    if supplier_is_msme and target_rung >= 2:
        if computed_interest_paise is None or computed_interest_paise < 0:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="no_fabricated_claims",
                    passed=False,
                    detail="Statutory interest must be explicitly calculated before drafting rung 2+ notices",
                )
            )
            allowed = False
            final_action = "blocked_missing_interest_figure"
            reason = "Missing or invalid statutory interest figure"
        else:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="no_fabricated_claims",
                    passed=True,
                    detail=f"Valid computed interest ({computed_interest_paise} paise) verified",
                )
            )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="no_fabricated_claims",
                passed=True,
                detail="Not citing MSMED interest or below rung 2",
            )
        )

    # Rule 10: human_signoff_before_rung_4
    if target_rung == 4:
        if not human_approved:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="human_signoff_before_rung_4",
                    passed=False,
                    detail="MSME Samadhaan packet drafted; requires human signoff before filing",
                )
            )
            final_action = "pending_human_approval"
            reason = "Rung 4 reached; waiting for operator approval"
        else:
            rules_checked.append(
                StoppingRuleCheck(
                    rule="human_signoff_before_rung_4",
                    passed=True,
                    detail="Human approval verified for rung 4 filing",
                )
            )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="human_signoff_before_rung_4",
                passed=True,
                detail="Below rung 4",
            )
        )

    # Rule 13: policy_gate_is_final
    rules_checked.append(
        StoppingRuleCheck(
            rule="policy_gate_is_final",
            passed=True,
            detail="Policy gate evaluation complete",
        )
    )

    return PolicyGateResult(
        allowed=allowed,
        final_action=final_action,
        reason=reason,
        stopping_rules_checked=[r.to_dict() for r in rules_checked],
        rule_recommendation=rule_rec,
    )


def check_module_c_policy_gate(
    amount_paise: int,
    nudge_sent: bool,
) -> PolicyGateResult:
    rules_checked: list[StoppingRuleCheck] = []

    # Rule 12: low_value_floor
    if amount_paise < LOW_VALUE_FLOOR_PAISE:
        rules_checked.append(
            StoppingRuleCheck(
                rule="low_value_floor",
                passed=False,
                detail=f"Order amount ({amount_paise} paise) is below Rs 200 floor ({LOW_VALUE_FLOOR_PAISE} paise)",
            )
        )
        return PolicyGateResult(
            allowed=False,
            final_action="skipped_low_value",
            reason="Order amount below minimum recovery value floor",
            stopping_rules_checked=[r.to_dict() for r in rules_checked],
        )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="low_value_floor",
                passed=True,
                detail=f"Order amount ({amount_paise} paise) meets value floor",
            )
        )

    # Rule 11: single_nudge_cap
    if nudge_sent:
        rules_checked.append(
            StoppingRuleCheck(
                rule="single_nudge_cap",
                passed=False,
                detail="Nudge already sent for this order; strictly capped at 1 nudge",
            )
        )
        return PolicyGateResult(
            allowed=False,
            final_action="blocked_single_nudge_cap",
            reason="Checkout abandonment nudge already delivered",
            stopping_rules_checked=[r.to_dict() for r in rules_checked],
        )
    else:
        rules_checked.append(
            StoppingRuleCheck(
                rule="single_nudge_cap",
                passed=True,
                detail="No prior nudge sent",
            )
        )

    # Rule 13: policy_gate_is_final
    rules_checked.append(
        StoppingRuleCheck(
            rule="policy_gate_is_final",
            passed=True,
            detail="Policy gate evaluation complete",
        )
    )

    return PolicyGateResult(
        allowed=True,
        final_action="send_abandonment_nudge",
        reason="Checkout abandonment recovery nudge approved",
        stopping_rules_checked=[r.to_dict() for r in rules_checked],
    )
