"""Safety invariants that must never regress:

1. Any scam/spam classification results in action=mute -- enforced by
   Router._apply_overrides override (a), unconditionally, regardless of whether
   the classification came from the rule-based fallback or the LLM path.
2. The unverified-sender + payment + urgency heuristic (override (b)) upgrades an
   otherwise-non-scam classification to scam when the sender is unknown/unverified
   and the message uses payment or urgency language typical of a scam.
"""

from __future__ import annotations

from conftest import FakeAnthropicClient, make_message_row


# ---------------------------------------------------------------------------
# (a) scam/spam -> mute, regardless of source
# ---------------------------------------------------------------------------

def test_scam_via_rules_forces_mute(dataset_builder, make_router):
    dataset_builder.add_user("u_1")
    router = make_router()

    msg = make_message_row(
        user_id="u_1", conversation_type="personal", sender_user_id="u_stranger",
        message_text="Security alert: OTP may have leaked. Verify now at account-login.in "
        "or your profile may be temporarily blocked.",
    )
    result = router.route(msg)

    assert result["message_type"] == "scam"
    assert result["action"] == "mute"


def test_spam_via_rules_forces_mute(dataset_builder, make_router):
    dataset_builder.add_user("u_1")
    dataset_builder.add_business("biz_1", verified=0, age_days=10)
    router = make_router()

    msg = make_message_row(
        user_id="u_1", conversation_type="business", business_id="biz_1", sender_user_id=None,
        message_text="Huge discount! 70% off everything, limited time deal, don't miss out!",
    )
    result = router.route(msg)

    assert result["message_type"] == "spam"
    assert result["action"] == "mute"


def test_llm_scam_classification_still_forced_to_mute(dataset_builder, make_router):
    """Even if the upstream classifier (here, a mocked LLM) inconsistently pairs
    message_type=scam with action=notify, the post-hoc override must still force
    mute -- this invariant must not depend on the LLM 'getting it right'."""
    dataset_builder.add_user("u_1")
    router = make_router()
    router._client = FakeAnthropicClient({
        "action": "notify",  # deliberately inconsistent with message_type=scam
        "message_type": "scam",
        "reason": "This looks like a phishing attempt.",
        "confidence": 0.9,
        "evidence_message_ids": [],
    })

    msg = make_message_row(user_id="u_1", message_text="anything")
    result = router.route(msg)

    assert result["message_type"] == "scam"
    assert result["action"] == "mute"


def test_llm_spam_classification_still_forced_to_mute(dataset_builder, make_router):
    dataset_builder.add_user("u_1")
    router = make_router()
    router._client = FakeAnthropicClient({
        "action": "digest",  # deliberately inconsistent with message_type=spam
        "message_type": "spam",
        "reason": "Unsolicited marketing.",
        "confidence": 0.8,
        "evidence_message_ids": [],
    })

    msg = make_message_row(user_id="u_1", message_text="anything")
    result = router.route(msg)

    assert result["message_type"] == "spam"
    assert result["action"] == "mute"


# ---------------------------------------------------------------------------
# (b) unverified/unknown sender + payment/urgency language -> scam
# ---------------------------------------------------------------------------

def test_unverified_sender_payment_urgency_heuristic_fires_via_rules(dataset_builder, make_router):
    """A business message that would otherwise resolve to a mundane classification
    (untrusted-but-not-obviously-scammy business content) must be upgraded to scam
    when the sender is unverified with no on-file relationship AND the text carries
    payment + urgency language -- this is override (b), distinct from the
    credential-pattern rule (1) that catches OTP/PIN-style phishing directly."""
    dataset_builder.add_user("u_1")
    dataset_builder.add_business(
        "biz_new", verified=0, age_days=15,
        official_domain="realbank.com", domain_used="realbank.com",
    )
    router = make_router()

    msg = make_message_row(
        user_id="u_1", conversation_type="business", business_id="biz_new", sender_user_id=None,
        message_text="Your bill of Rs 2,000 is due immediately, failure to pay will result "
        "in service suspension.",
    )
    result = router.route(msg)

    assert result["message_type"] == "scam"
    assert result["action"] == "mute"


def test_unverified_sender_payment_urgency_heuristic_fires_even_when_llm_disagrees(
    dataset_builder, make_router
):
    """Same heuristic, but starting from a mocked LLM that confidently (and
    incorrectly) calls it routine business content -- the override must still
    catch it, proving the heuristic is not bypassable via the LLM path."""
    dataset_builder.add_user("u_1")
    dataset_builder.add_business(
        "biz_new", verified=0, age_days=15,
        official_domain="realbank.com", domain_used="realbank.com",
    )
    router = make_router()
    router._client = FakeAnthropicClient({
        "action": "digest",
        "message_type": "business_update",
        "reason": "Routine billing notice.",
        "confidence": 0.6,
        "evidence_message_ids": [],
    })

    msg = make_message_row(
        user_id="u_1", conversation_type="business", business_id="biz_new", sender_user_id=None,
        message_text="Your bill of Rs 2,000 is due immediately, failure to pay will result "
        "in service suspension.",
    )
    result = router.route(msg)

    assert result["message_type"] == "scam"
    assert result["action"] == "mute"


def test_verified_business_with_relationship_payment_reminder_is_not_flagged_as_scam(
    dataset_builder, make_router
):
    """Control case: the same kind of payment-urgency-flavored language from a
    verified, known business with an on-file relationship must NOT trigger the
    unverified-sender heuristic -- confirms the heuristic is trust-gated, not a
    blanket payment+urgency-language filter."""
    dataset_builder.add_user("u_1")
    dataset_builder.add_business(
        "biz_trusted", verified=1, age_days=2000,
        official_domain="realbank.com", domain_used="realbank.com",
    )
    dataset_builder.add_relationship("u_1", "biz_trusted", why="active_bank_account")
    router = make_router()

    msg = make_message_row(
        user_id="u_1", conversation_type="business", business_id="biz_trusted", sender_user_id=None,
        # Same urgency-laden phrasing as the attack test above -- only the sender's
        # trust profile (verified + on-file relationship) differs, isolating that
        # as the variable the heuristic actually gates on.
        message_text="Your bill of Rs 2,000 is due immediately, failure to pay will result "
        "in service suspension.",
    )
    result = router.route(msg)

    assert result["message_type"] != "scam"
    assert result["action"] != "mute"
