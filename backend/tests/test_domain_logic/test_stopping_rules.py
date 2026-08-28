from datetime import datetime, timedelta, timezone
from app.db.models.payment_case import InterventionType, PaymentContext, PaymentMethod
from app.domain_logic.stopping_rules import (
    check_module_a_policy_gate,
    check_module_b_policy_gate,
    check_module_c_policy_gate,
)


def test_module_a_hard_decline_forced_alternate_method():
    # Hard decline recommended retry -> MUST force alternate_method
    res = check_module_a_policy_gate(
        method=PaymentMethod.CARD,
        context=PaymentContext.ONE_TIME,
        classified_root_cause="card_expired",
        recommended_intervention=InterventionType.SILENT_RETRY,
    )
    assert res.allowed is True
    assert res.final_action == InterventionType.ALTERNATE_METHOD.value
    assert res.rule_recommendation == InterventionType.SILENT_RETRY.value


def test_module_a_hard_decline_redundancy_all_causes_override_bad_upstream():
    # Test that even if an upstream bug passes SILENT_RETRY or DELAYED_RETRY_NOTIFY for any hard decline cause,
    # stopping_rules.py catches and overrides it to ALTERNATE_METHOD.
    hard_causes = ["card_lost_or_stolen", "card_expired", "mandate_expired"]
    for cause in hard_causes:
        # Simulate upstream erroneously recommending DELAYED_RETRY_NOTIFY
        res = check_module_a_policy_gate(
            method=PaymentMethod.CARD if "card" in cause else PaymentMethod.UPI,
            context=PaymentContext.SUBSCRIPTION,
            classified_root_cause=cause,
            recommended_intervention=InterventionType.DELAYED_RETRY_NOTIFY,
        )
        assert res.final_action == InterventionType.ALTERNATE_METHOD.value
        assert res.rule_recommendation == InterventionType.DELAYED_RETRY_NOTIFY.value
        # Verify the hard_decline_never_retry rule in stopping_rules_checked flagged the override
        rule_check = next(r for r in res.stopping_rules_checked if r["rule"] == "hard_decline_never_retry")
        assert rule_check["passed"] is False
        assert "forcing alternate payment method" in rule_check["detail"]


def test_module_a_gateway_sync_gap_override():
    # Sync gap -> MUST force escalate_human
    res = check_module_a_policy_gate(
        method=PaymentMethod.NETBANKING,
        context=PaymentContext.ONE_TIME,
        classified_root_cause="gateway_data_sync_gap",
        recommended_intervention=InterventionType.SILENT_RETRY,
    )
    assert res.final_action == InterventionType.ESCALATE_HUMAN.value


def test_module_a_npci_window_and_retry_cap():
    now_utc = datetime(2026, 8, 27, 5, 30, tzinfo=timezone.utc)  # 11:00 AM IST (blocked 10-13)
    res = check_module_a_policy_gate(
        method=PaymentMethod.UPI,
        context=PaymentContext.ONE_TIME,
        classified_root_cause="insufficient_balance",
        recommended_intervention=InterventionType.DELAYED_RETRY_NOTIFY,
        now=now_utc,
    )
    assert res.npci_window_conflict is True
    assert res.reschedule_at is not None

    # Test UPI retry ceiling (1 original + 3 retries)
    res_ceiling = check_module_a_policy_gate(
        method=PaymentMethod.UPI,
        context=PaymentContext.ONE_TIME,
        classified_root_cause="upi_bank_server_unavailable",
        recommended_intervention=InterventionType.SILENT_RETRY,
        attempt_number=5,
        retry_count=3,
        now=now_utc,
    )
    assert res_ceiling.final_action == InterventionType.ESCALATE_HUMAN.value


def test_module_a_contact_cooldown_48h():
    now_utc = datetime.now(timezone.utc)
    recent_contact = now_utc - timedelta(hours=24)
    res = check_module_a_policy_gate(
        method=PaymentMethod.CARD,
        context=PaymentContext.ONE_TIME,
        classified_root_cause="insufficient_credit_limit",
        recommended_intervention=InterventionType.DELAYED_RETRY_NOTIFY,
        last_action_at=recent_contact,
        now=now_utc,
    )
    assert res.allowed is False
    assert res.final_action == "blocked_contact_cooldown"


def test_module_b_dispute_halt_rule():
    # Active dispute -> MUST block immediately
    res = check_module_b_policy_gate(
        dispute_flag=True,
        broken_promise_count=0,
        current_rung=1,
        target_rung=2,
        last_contact_at=None,
        computed_interest_paise=50000,
        supplier_is_msme=True,
    )
    assert res.allowed is False
    assert res.final_action == "blocked_dispute_halt"


def test_module_b_broken_promise_cap():
    # >= 3 broken promises forces rung 4
    res = check_module_b_policy_gate(
        dispute_flag=False,
        broken_promise_count=3,
        current_rung=1,
        target_rung=2,
        last_contact_at=None,
        computed_interest_paise=50000,
        supplier_is_msme=True,
        human_approved=False,
    )
    assert res.final_action == "pending_human_approval"


def test_module_b_contact_frequency_cap_7d():
    now_utc = datetime.now(timezone.utc)
    recent_contact = now_utc - timedelta(days=3)
    res = check_module_b_policy_gate(
        dispute_flag=False,
        broken_promise_count=0,
        current_rung=1,
        target_rung=2,
        last_contact_at=recent_contact,
        computed_interest_paise=50000,
        supplier_is_msme=True,
        now=now_utc,
    )
    assert res.allowed is False
    assert res.final_action == "blocked_contact_frequency_cap"


def test_module_c_low_value_floor_and_single_nudge():
    # Amount below Rs 200 (20,000 paise)
    res_low = check_module_c_policy_gate(amount_paise=15000, nudge_sent=False)
    assert res_low.allowed is False
    assert res_low.final_action == "skipped_low_value"

    # Single nudge cap
    res_nudged = check_module_c_policy_gate(amount_paise=50000, nudge_sent=True)
    assert res_nudged.allowed is False
    assert res_nudged.final_action == "blocked_single_nudge_cap"

    # Eligible order
    res_ok = check_module_c_policy_gate(amount_paise=50000, nudge_sent=False)
    assert res_ok.allowed is True
    assert res_ok.final_action == "send_abandonment_nudge"
