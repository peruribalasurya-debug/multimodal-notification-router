"""Stage 1: context assembly for the message notification router.

Loads every dataset/*.csv once, joins user/group/business/history context onto
a single incoming message, and retrieves the top-k most relevant historical
messages (same sender/group/business channel first, ranked by text similarity
within that channel) along with the recipient's recorded reactions to them.

See docs/architecture.md (Stage 1) and docs/routing_rubric.md for the design
this implements.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _clean(value: Any) -> Any:
    """Convert pandas/numpy scalars (incl. NaN) to plain JSON-friendly Python values."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _row_to_dict(row: pd.Series | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: _clean(v) for k, v in row.items()}


def _in_dnd_window(created_at: str, window: str | None) -> bool | None:
    """True if created_at's time-of-day falls inside a 'HH:MM-HH:MM' window (wraps midnight)."""
    if not window or not isinstance(window, str) or "-" not in window:
        return None
    try:
        msg_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M").time()
        start_s, end_s = window.split("-")
        start = datetime.strptime(start_s.strip(), "%H:%M").time()
        end = datetime.strptime(end_s.strip(), "%H:%M").time()
    except ValueError:
        return None
    if start <= end:
        return start <= msg_time <= end
    return msg_time >= start or msg_time <= end


@dataclass
class Dataset:
    """All dataset/*.csv files loaded once, ready for repeated lookups."""

    messages: pd.DataFrame
    users: pd.DataFrame
    groups: pd.DataFrame
    group_members: pd.DataFrame
    business_accounts: pd.DataFrame
    user_business_history: pd.DataFrame
    message_history: pd.DataFrame
    message_events: pd.DataFrame
    images: pd.DataFrame
    voice_notes: pd.DataFrame
    daily_notification_summary: pd.DataFrame

    @classmethod
    def load(cls, dataset_dir: str = "dataset") -> "Dataset":
        def read(name: str) -> pd.DataFrame:
            return pd.read_csv(os.path.join(dataset_dir, name))

        return cls(
            messages=read("messages.csv"),
            users=read("users.csv"),
            groups=read("groups.csv"),
            group_members=read("group_members.csv"),
            business_accounts=read("business_accounts.csv"),
            user_business_history=read("user_business_history.csv"),
            message_history=read("message_history.csv"),
            message_events=read("message_events.csv"),
            images=read("images.csv"),
            voice_notes=read("voice_notes.csv"),
            daily_notification_summary=read("daily_notification_summary.csv"),
        )


class ContextAssembler:
    """Builds a structured context dict for a single incoming message."""

    def __init__(self, dataset_dir: str = "dataset", top_k: int = 3):
        self.data = Dataset.load(dataset_dir)
        self.top_k = top_k

    # -- individual join helpers -------------------------------------------------

    def _get_user(self, user_id: str) -> dict[str, Any] | None:
        rows = self.data.users[self.data.users.user_id == user_id]
        return _row_to_dict(rows.iloc[0]) if len(rows) else None

    def _get_sender(self, sender_user_id: Any) -> dict[str, Any] | None:
        if pd.isna(sender_user_id):
            return None
        return self._get_user(sender_user_id)

    def _get_group_context(
        self, group_id: Any, user_id: str, sender_user_id: Any = None
    ) -> dict[str, Any] | None:
        if pd.isna(group_id):
            return None
        group_rows = self.data.groups[self.data.groups.group_id == group_id]
        member_rows = self.data.group_members[
            (self.data.group_members.group_id == group_id)
            & (self.data.group_members.user_id == user_id)
        ]

        sender_membership = None
        if sender_user_id is not None and not pd.isna(sender_user_id):
            sender_rows = self.data.group_members[
                (self.data.group_members.group_id == group_id)
                & (self.data.group_members.user_id == sender_user_id)
            ]
            sender_membership = _row_to_dict(sender_rows.iloc[0]) if len(sender_rows) else None

        return {
            "group": _row_to_dict(group_rows.iloc[0]) if len(group_rows) else None,
            "membership": _row_to_dict(member_rows.iloc[0]) if len(member_rows) else None,
            # the SENDER's role in this group — distinct from the recipient's own
            # membership above. The rubric treats "sender is a group admin" as a
            # decisive trust signal for same-day operational/safety notify decisions,
            # independent of the recipient's own role.
            "sender_membership": sender_membership,
        }

    def _get_business_context(self, business_id: Any, user_id: str) -> dict[str, Any] | None:
        if pd.isna(business_id):
            return None
        biz_rows = self.data.business_accounts[
            self.data.business_accounts.business_id == business_id
        ]
        history_rows = self.data.user_business_history[
            (self.data.user_business_history.business_id == business_id)
            & (self.data.user_business_history.user_id == user_id)
        ]
        return {
            "business": _row_to_dict(biz_rows.iloc[0]) if len(biz_rows) else None,
            "relationship": _row_to_dict(history_rows.iloc[0]) if len(history_rows) else None,
        }

    def _get_daily_load(self, user_id: str, created_at: str) -> dict[str, Any] | None:
        date = created_at.split(" ")[0]
        rows = self.data.daily_notification_summary[
            (self.data.daily_notification_summary.user_id == user_id)
            & (self.data.daily_notification_summary.date == date)
        ]
        today = _row_to_dict(rows.iloc[0]) if len(rows) else None

        user_rows = self.data.daily_notification_summary[
            self.data.daily_notification_summary.user_id == user_id
        ]
        baseline_mean = (
            float(user_rows.notifications_sent.mean()) if len(user_rows) else None
        )
        return {"today": today, "user_14d_mean_notifications_sent": baseline_mean}

    # -- evidence retrieval --------------------------------------------------

    def _channel_filter(self, message: pd.Series) -> pd.DataFrame:
        """Historical messages received by the same user, from the same channel."""
        history = self.data.message_history
        same_user = history.user_id == message.user_id

        conv_type = message.conversation_type
        if conv_type == "personal":
            same_channel = history.sender_user_id == message.sender_user_id
        elif conv_type == "group":
            same_channel = history.group_id == message.group_id
        elif conv_type == "business":
            same_channel = history.business_id == message.business_id
        else:
            same_channel = pd.Series(False, index=history.index)

        return history[same_user & same_channel]

    def _rank_by_similarity(
        self, candidates: pd.DataFrame, query_text: str
    ) -> list[tuple[str, float]]:
        """Rank candidate history rows by TF-IDF cosine similarity to query_text."""
        texts = candidates.message_text.fillna("").tolist()
        query = query_text if isinstance(query_text, str) else ""

        if not texts or not query.strip():
            # Nothing to compare against, or the query itself is empty (e.g. a
            # not-yet-transcribed voice message) — return channel order as-is.
            return [(mid, 0.0) for mid in candidates.message_id.tolist()]

        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            matrix = vectorizer.fit_transform(texts + [query])
        except ValueError:
            # Vocabulary was empty after stopword removal (very short/odd text).
            return [(mid, 0.0) for mid in candidates.message_id.tolist()]

        query_vec = matrix[-1]
        candidate_vecs = matrix[:-1]
        sims = cosine_similarity(candidate_vecs, query_vec).ravel()

        ranked = sorted(
            zip(candidates.message_id.tolist(), sims.tolist()),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return ranked

    def _get_evidence(self, message: pd.Series) -> list[dict[str, Any]]:
        candidates = self._channel_filter(message)
        if candidates.empty:
            return []

        ranked = self._rank_by_similarity(candidates, message.message_text)
        top_ids = [mid for mid, _score in ranked[: self.top_k]]
        score_by_id = dict(ranked)

        evidence = []
        for mid in top_ids:
            hist_row = candidates[candidates.message_id == mid].iloc[0]
            event_rows = self.data.message_events[
                (self.data.message_events.message_id == mid)
                & (self.data.message_events.user_id == message.user_id)
            ]
            evidence.append(
                {
                    "message_id": mid,
                    "similarity_score": round(float(score_by_id[mid]), 4),
                    "created_at": _clean(hist_row.created_at),
                    "message_text": _clean(hist_row.message_text),
                    "media_type": _clean(hist_row.media_type),
                    "forwarded_count": _clean(hist_row.forwarded_count),
                    "reaction": _row_to_dict(event_rows.iloc[0]) if len(event_rows) else None,
                }
            )
        return evidence

    # -- public API -----------------------------------------------------------

    def build_context(self, message_id: str) -> dict[str, Any]:
        """Build context for a message_id that exists in dataset/messages.csv."""
        rows = self.data.messages[self.data.messages.message_id == message_id]
        if rows.empty:
            raise KeyError(f"message_id {message_id!r} not found in messages.csv")
        return self.build_context_for_row(rows.iloc[0])

    def build_context_for_row(self, message: pd.Series) -> dict[str, Any]:
        """Build context directly from a message row (e.g. from sample_messages.csv,
        which has the same input columns as messages.csv but isn't itself in it)."""
        user = self._get_user(message.user_id)
        dnd_overlap = (
            _in_dnd_window(message.created_at, user.get("do_not_disturb_window"))
            if user
            else None
        )

        return {
            "message": _row_to_dict(message),
            "recipient": {
                "user_id": message.user_id,
                "profile": user,
                "in_quiet_hours": dnd_overlap,
            },
            "sender": self._get_sender(message.sender_user_id),
            "group_context": self._get_group_context(
                message.group_id, message.user_id, message.sender_user_id
            ),
            "business_context": self._get_business_context(
                message.business_id, message.user_id
            ),
            "daily_notification_load": self._get_daily_load(
                message.user_id, message.created_at
            ),
            "evidence": self._get_evidence(message),
        }


# ---------------------------------------------------------------------------
# Quick test: print assembled context for one text, one image, one voice message
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    assembler = ContextAssembler(dataset_dir="dataset", top_k=3)
    msgs = assembler.data.messages

    picks: dict[str, str | None] = {"text": None, "image": None, "voice": None}
    for _, row in msgs.iterrows():
        if picks["text"] is None and pd.isna(row.media_type):
            picks["text"] = row.message_id
        elif picks["image"] is None and row.media_type == "image":
            picks["image"] = row.message_id
        elif picks["voice"] is None and row.media_type == "voice":
            picks["voice"] = row.message_id
        if all(picks.values()):
            break

    for kind, message_id in picks.items():
        if message_id is None:
            print(f"=== {kind.upper()}: no example found in messages.csv ===\n")
            continue
        print(f"=== {kind.upper()} message: {message_id} ===")
        context = assembler.build_context(message_id)
        print(json.dumps(context, indent=2, ensure_ascii=False))
        print()
