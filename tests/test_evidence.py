"""Evidence invariants that must never regress:

3. Evidence validity -- cited IDs must exist in message_history.csv and belong to
   the message's own receiving user; anything else (a hallucinated ID, or a real
   ID that belongs to someone else) is dropped by Router._validate_evidence_ids,
   regardless of which classifier (LLM or rules) proposed it.
4. Evidence policy -- when the rule-based path's deciding signal is a dismissed
   prior message, the cited evidence is exactly that message and nothing else
   (not padded out to look like more support than actually exists).
"""

from __future__ import annotations

from conftest import FakeAnthropicClient, make_message_row


# ---------------------------------------------------------------------------
# 3. Evidence validity
# ---------------------------------------------------------------------------

def test_hallucinated_evidence_id_is_dropped(dataset_builder, make_router):
    dataset_builder.add_user("u_1")
    dataset_builder.add_history_message(
        "message_h1", "u_1", conversation_type="personal", sender_user_id="u_sender", text="hi"
    )
    router = make_router()
    router._client = FakeAnthropicClient({
        "action": "digest", "message_type": "personal", "reason": "test",
        "confidence": 0.6, "evidence_message_ids": ["message_h1", "message_does_not_exist_999"],
    })

    msg = make_message_row(user_id="u_1", sender_user_id="u_sender", message_text="hello again")
    result = router.route(msg)

    cited = set(result["evidence_message_ids"].split(";")) if result["evidence_message_ids"] != "none" else set()
    assert cited == {"message_h1"}
    assert "message_does_not_exist_999" not in cited


def test_evidence_id_belonging_to_different_user_is_dropped(dataset_builder, make_router):
    dataset_builder.add_user("u_1")
    dataset_builder.add_user("u_2")
    dataset_builder.add_history_message(
        "message_h1", "u_1", conversation_type="personal", sender_user_id="u_sender", text="mine"
    )
    dataset_builder.add_history_message(
        "message_h2", "u_2", conversation_type="personal", sender_user_id="u_sender", text="not mine"
    )
    router = make_router()
    router._client = FakeAnthropicClient({
        "action": "digest", "message_type": "personal", "reason": "test",
        "confidence": 0.6, "evidence_message_ids": ["message_h1", "message_h2"],
    })

    msg = make_message_row(user_id="u_1", sender_user_id="u_sender", message_text="hello again")
    result = router.route(msg)

    cited = set(result["evidence_message_ids"].split(";")) if result["evidence_message_ids"] != "none" else set()
    assert cited == {"message_h1"}
    assert "message_h2" not in cited


def test_valid_same_user_evidence_id_is_kept(dataset_builder, make_router):
    dataset_builder.add_user("u_1")
    dataset_builder.add_history_message(
        "message_h1", "u_1", conversation_type="personal", sender_user_id="u_sender", text="mine"
    )
    router = make_router()
    router._client = FakeAnthropicClient({
        "action": "digest", "message_type": "personal", "reason": "test",
        "confidence": 0.6, "evidence_message_ids": ["message_h1"],
    })

    msg = make_message_row(user_id="u_1", sender_user_id="u_sender", message_text="hello again")
    result = router.route(msg)

    assert result["evidence_message_ids"] == "message_h1"


def test_no_evidence_cited_yields_none_string(dataset_builder, make_router):
    dataset_builder.add_user("u_1")
    router = make_router()
    router._client = FakeAnthropicClient({
        "action": "digest", "message_type": "unknown", "reason": "test",
        "confidence": 0.55, "evidence_message_ids": [],
    })

    msg = make_message_row(user_id="u_1", message_text="hello")
    result = router.route(msg)

    assert result["evidence_message_ids"] == "none"


def test_all_hallucinated_evidence_drops_to_none(dataset_builder, make_router):
    dataset_builder.add_user("u_1")
    router = make_router()
    router._client = FakeAnthropicClient({
        "action": "digest", "message_type": "unknown", "reason": "test",
        "confidence": 0.55, "evidence_message_ids": ["message_fake_1", "message_fake_2"],
    })

    msg = make_message_row(user_id="u_1", message_text="hello")
    result = router.route(msg)

    assert result["evidence_message_ids"] == "none"


# ---------------------------------------------------------------------------
# 4. Evidence policy -- cites exactly the relevant dismissed evidence, no more
# ---------------------------------------------------------------------------

def test_dismissed_prior_listing_is_cited_exactly_and_alone(dataset_builder, make_router):
    """A group marketplace listing from a sender whose *only* prior listing in
    that channel was dismissed by this user must be muted on that basis, citing
    exactly that one dismissed message -- not zero (the decision *is* evidence-
    driven) and not more than one (there's nothing else relevant to cite)."""
    dataset_builder.add_user("u_1")
    dataset_builder.add_group("group_1")
    dataset_builder.add_group_member("group_1", "u_1", role="member")
    dataset_builder.add_group_member("group_1", "u_seller", role="member")

    dataset_builder.add_history_message(
        "message_prior", "u_1", conversation_type="group", group_id="group_1",
        sender_user_id="u_seller", text="Selling a bike lock, barely used, pickup near gate. DM if interested.",
    )
    dataset_builder.add_event("message_prior", "u_1", dismissed=1, muted=1)

    router = make_router()
    msg = make_message_row(
        user_id="u_1", conversation_type="group", group_id="group_1", sender_user_id="u_seller",
        message_text="Selling a bike helmet, barely used, pickup near gate. DM if interested.",
    )
    result = router.route(msg)

    assert result["action"] == "mute"
    assert result["message_type"] == "promotion"
    assert result["evidence_message_ids"] == "message_prior"


def test_no_dismissal_history_marketplace_listing_is_digested_with_that_evidence(
    dataset_builder, make_router
):
    """Control case: the same kind of listing, but the prior interaction in that
    channel was positive (opened, not dismissed) -- expect digest, still citing
    that single prior message as the (positive) evidence behind the decision."""
    dataset_builder.add_user("u_1")
    dataset_builder.add_group("group_1")
    dataset_builder.add_group_member("group_1", "u_1", role="member")
    dataset_builder.add_group_member("group_1", "u_seller", role="member")

    dataset_builder.add_history_message(
        "message_prior", "u_1", conversation_type="group", group_id="group_1",
        sender_user_id="u_seller", text="Selling a bike lock, barely used, pickup near gate. DM if interested.",
    )
    dataset_builder.add_event("message_prior", "u_1", opened=1)

    router = make_router()
    msg = make_message_row(
        user_id="u_1", conversation_type="group", group_id="group_1", sender_user_id="u_seller",
        message_text="Selling a bike helmet, barely used, pickup near gate. DM if interested.",
    )
    result = router.route(msg)

    assert result["action"] == "digest"
    assert result["message_type"] == "promotion"
    assert result["evidence_message_ids"] == "message_prior"
