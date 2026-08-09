"""Shared fixtures for the router test suite.

Every test builds its own small, self-contained dataset via `DatasetBuilder`
instead of depending on the content of the real dataset/ directory -- these
tests check invariants of the CODE, not of any particular dataset snapshot, so
they must keep passing even if dataset/*.csv changes or is replaced.

No test ever calls a real LLM, OCR engine, or ASR model: the `no_real_api_key`
fixture (autouse) strips ANTHROPIC_API_KEY before every test regardless of what
a developer's local .env holds, and tests that need to exercise the LLM path
inject a FakeAnthropicClient (below) directly.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

import pandas as pd
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
for _p in (SRC_DIR, REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from media import MediaExtractor  # noqa: E402
from router import Router  # noqa: E402


@pytest.fixture(autouse=True)
def no_real_api_key(monkeypatch):
    """Every test runs with ANTHROPIC_API_KEY unset, regardless of a local .env --
    guarantees Router/MediaExtractor never construct a real anthropic.Anthropic
    client by accident. Tests exercising the LLM path inject FakeAnthropicClient
    directly onto router._client / media._anthropic_client instead."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


# ---------------------------------------------------------------------------
# Dataset builder -- writes a minimal, valid dataset/ directory on demand
# ---------------------------------------------------------------------------

MESSAGES_COLUMNS = [
    "message_id", "user_id", "conversation_type", "group_id", "business_id",
    "sender_user_id", "created_at", "message_text", "media_type", "media_id",
    "forwarded_count",
]
USERS_COLUMNS = [
    "user_id", "do_not_disturb_window", "messages_opened_30d", "messages_replied_30d",
    "notifications_dismissed_30d", "messages_reported_30d",
]
GROUPS_COLUMNS = [
    "group_id", "group_name", "group_type", "member_count", "admin_count",
    "created_at", "messages_30d",
]
GROUP_MEMBERS_COLUMNS = [
    "group_id", "user_id", "role", "joined_at", "messages_sent_30d", "messages_read_30d",
    "replies_sent_30d", "notifications_dismissed_30d", "group_muted_by_user",
]
BUSINESS_COLUMNS = [
    "business_id", "display_name", "brand_name", "category", "verified",
    "official_domain", "domain_used_by_sender", "account_age_days",
    "messages_sent_30d", "user_reports_30d", "domain_used_by_sender_age_days",
]
UBH_COLUMNS = [
    "user_id", "business_id", "why_user_knows_account", "last_activity_at",
    "allows_promotions", "promotions_opted_out_at", "activity_count_180d",
    "messages_opened_30d", "messages_dismissed_30d", "messages_replied_30d", "last_reply_at",
]
MESSAGE_HISTORY_COLUMNS = MESSAGES_COLUMNS
MESSAGE_EVENTS_COLUMNS = [
    "user_id", "message_id", "message_opened", "message_replied", "reaction_time_minutes",
    "notification_dismissed", "muted_after_message", "message_reported",
]
IMAGES_COLUMNS = ["image_id", "file_path"]
VOICE_NOTES_COLUMNS = ["voice_note_id", "file_path"]
DAILY_SUMMARY_COLUMNS = ["user_id", "date", "notifications_sent"]


class DatasetBuilder:
    """Accumulates rows in memory; `.write()` dumps every required dataset/*.csv
    (even empty ones) so ContextAssembler/MediaExtractor never hit a missing-file
    error regardless of which tables a given test actually populates."""

    def __init__(self, root: str):
        self.root = root
        self.users: list[dict] = []
        self.groups: list[dict] = []
        self.group_members: list[dict] = []
        self.business_accounts: list[dict] = []
        self.user_business_history: list[dict] = []
        self.message_history: list[dict] = []
        self.message_events: list[dict] = []
        self.images: list[dict] = []
        self.voice_notes: list[dict] = []
        self.daily_notification_summary: list[dict] = []

    def add_user(self, user_id, *, dnd="00:00-00:00", opened=0, replied=0, dismissed=0, reported=0):
        self.users.append(dict(
            user_id=user_id, do_not_disturb_window=dnd, messages_opened_30d=opened,
            messages_replied_30d=replied, notifications_dismissed_30d=dismissed,
            messages_reported_30d=reported,
        ))
        return self

    def add_group(self, group_id, *, name=None, gtype="family", members=5, admins=1,
                  created="2024-01-01", msgs30d=10):
        self.groups.append(dict(
            group_id=group_id, group_name=name or group_id, group_type=gtype,
            member_count=members, admin_count=admins, created_at=created, messages_30d=msgs30d,
        ))
        return self

    def add_group_member(self, group_id, user_id, *, role="member", joined="2024-01-01",
                          sent=0, read=0, replies=0, dismissed=0, muted=0):
        self.group_members.append(dict(
            group_id=group_id, user_id=user_id, role=role, joined_at=joined,
            messages_sent_30d=sent, messages_read_30d=read, replies_sent_30d=replies,
            notifications_dismissed_30d=dismissed, group_muted_by_user=muted,
        ))
        return self

    def add_business(self, business_id, *, name=None, category="other", verified=1,
                      official_domain="example.com", domain_used="example.com", age_days=1000,
                      sent30d=100, reports30d=0, sender_domain_age=1000):
        self.business_accounts.append(dict(
            business_id=business_id, display_name=name or business_id, brand_name=name or business_id,
            category=category, verified=verified, official_domain=official_domain,
            domain_used_by_sender=domain_used, account_age_days=age_days,
            messages_sent_30d=sent30d, user_reports_30d=reports30d,
            domain_used_by_sender_age_days=sender_domain_age,
        ))
        return self

    def add_relationship(self, user_id, business_id, *, why="active_bank_account",
                          last_activity="2026-07-01 00:00", allows_promotions=0, opted_out_at=None,
                          activity_180d=1, opened30d=0, dismissed30d=0, replied30d=0, last_reply=None):
        self.user_business_history.append(dict(
            user_id=user_id, business_id=business_id, why_user_knows_account=why,
            last_activity_at=last_activity, allows_promotions=allows_promotions,
            promotions_opted_out_at=opted_out_at, activity_count_180d=activity_180d,
            messages_opened_30d=opened30d, messages_dismissed_30d=dismissed30d,
            messages_replied_30d=replied30d, last_reply_at=last_reply,
        ))
        return self

    def add_history_message(self, message_id, user_id, *, conversation_type="personal",
                             group_id=None, business_id=None, sender_user_id=None,
                             created_at="2026-07-01 10:00", text="", media_type=None,
                             media_id=None, forwarded=0):
        self.message_history.append(dict(
            message_id=message_id, user_id=user_id, conversation_type=conversation_type,
            group_id=group_id, business_id=business_id, sender_user_id=sender_user_id,
            created_at=created_at, message_text=text, media_type=media_type, media_id=media_id,
            forwarded_count=forwarded,
        ))
        return self

    def add_event(self, message_id, user_id, *, opened=0, replied=0, reaction_minutes=None,
                  dismissed=0, muted=0, reported=0):
        self.message_events.append(dict(
            user_id=user_id, message_id=message_id, message_opened=opened, message_replied=replied,
            reaction_time_minutes=reaction_minutes, notification_dismissed=dismissed,
            muted_after_message=muted, message_reported=reported,
        ))
        return self

    def add_image(self, image_id, file_path):
        self.images.append(dict(image_id=image_id, file_path=file_path))
        return self

    def add_voice_note(self, voice_note_id, file_path):
        self.voice_notes.append(dict(voice_note_id=voice_note_id, file_path=file_path))
        return self

    def write(self) -> str:
        os.makedirs(self.root, exist_ok=True)

        def dump(name: str, columns: list[str], rows: list[dict]) -> None:
            df = pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)
            df.to_csv(os.path.join(self.root, name), index=False)

        dump("messages.csv", MESSAGES_COLUMNS, [])  # not read by row-based routing; must exist
        dump("users.csv", USERS_COLUMNS, self.users)
        dump("groups.csv", GROUPS_COLUMNS, self.groups)
        dump("group_members.csv", GROUP_MEMBERS_COLUMNS, self.group_members)
        dump("business_accounts.csv", BUSINESS_COLUMNS, self.business_accounts)
        dump("user_business_history.csv", UBH_COLUMNS, self.user_business_history)
        dump("message_history.csv", MESSAGE_HISTORY_COLUMNS, self.message_history)
        dump("message_events.csv", MESSAGE_EVENTS_COLUMNS, self.message_events)
        dump("images.csv", IMAGES_COLUMNS, self.images)
        dump("voice_notes.csv", VOICE_NOTES_COLUMNS, self.voice_notes)
        dump("daily_notification_summary.csv", DAILY_SUMMARY_COLUMNS, self.daily_notification_summary)

        return self.root


@pytest.fixture
def dataset_builder(tmp_path) -> DatasetBuilder:
    return DatasetBuilder(str(tmp_path / "dataset"))


def make_message_row(**overrides: Any) -> pd.Series:
    """A minimal Router.route()-input row, overridable per test."""
    defaults = dict(
        message_id="msg_test", user_id="u_test", conversation_type="personal",
        group_id=None, business_id=None, sender_user_id="u_sender",
        created_at="2026-08-01 10:00", message_text="hello", media_type=None,
        media_id=None, forwarded_count=0,
    )
    defaults.update(overrides)
    return pd.Series(defaults)


@pytest.fixture
def make_router(dataset_builder, tmp_path):
    """Builds a Router wired to the (still-mutable) dataset_builder's dataset, with
    every cache path redirected under tmp_path -- never touches src/.cache/. Call
    the returned factory AFTER populating dataset_builder."""

    def _make() -> Router:
        dataset_dir = dataset_builder.write()
        media_extractor = MediaExtractor(dataset_dir, cache_path=str(tmp_path / "media_cache.json"))
        return Router(
            dataset_dir=dataset_dir,
            media_extractor=media_extractor,
            response_cache_path=str(tmp_path / "llm_response_cache.json"),
        )

    return _make


@pytest.fixture
def make_media_extractor(dataset_builder, tmp_path):
    """Builds a bare MediaExtractor (no Router) wired to an isolated cache path."""

    def _make() -> MediaExtractor:
        dataset_dir = dataset_builder.write()
        return MediaExtractor(dataset_dir, cache_path=str(tmp_path / "media_cache.json"))

    return _make


# ---------------------------------------------------------------------------
# Fake Anthropic client -- mimics just enough of the SDK's response shape for
# router.py's _call_llm_once / media.py's _extract_image_via_llm to consume.
# ---------------------------------------------------------------------------

class _FakeUsage:
    def __init__(self, input_tokens: int = 10, output_tokens: int = 5):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = 0
        self.cache_read_input_tokens = 0


class _FakeTextBlock:
    type = "text"

    def __init__(self, text: str):
        self.text = text


class _FakeResponse:
    def __init__(self, text: str, stop_reason: str = "end_turn"):
        self.content = [_FakeTextBlock(text)]
        self.stop_reason = stop_reason
        self.usage = _FakeUsage()


class _FakeMessagesAPI:
    def __init__(self, payloads: list[Any], stop_reason: str = "end_turn"):
        self._payloads = payloads
        self._stop_reason = stop_reason
        self.calls: list[dict] = []

    def create(self, **kwargs: Any) -> _FakeResponse:
        self.calls.append(kwargs)
        idx = min(len(self.calls) - 1, len(self._payloads) - 1)
        payload = self._payloads[idx]
        text = payload if isinstance(payload, str) else json.dumps(payload)
        return _FakeResponse(text, stop_reason=self._stop_reason)


class FakeAnthropicClient:
    """Drop-in replacement for `anthropic.Anthropic()`. `responses` is either a
    single dict/str (returned for every call) or a list (one entry consumed per
    call, last entry repeats once exhausted) -- lets a test script a retry."""

    def __init__(self, responses: Any, stop_reason: str = "end_turn"):
        payloads = responses if isinstance(responses, list) else [responses]
        self.messages = _FakeMessagesAPI(payloads, stop_reason=stop_reason)

    @property
    def call_count(self) -> int:
        return len(self.messages.calls)
