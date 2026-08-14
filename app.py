"""Streamlit live-demo front end for the multimodal notification router.

Reuses the real pipeline (src/context.py, src/media.py, src/router.py,
src/cascade_router.py, src/cheap_classifier.py) against the real dataset/ --
this is not a mock. A visitor picks a preset persona (a real user_id with real
relationship/group/business history, since personalization needs that context
to mean anything), types or uploads a message, and sees the same
rules -> cheap-classifier -> LLM cascade that reports/cascade_benchmark.md
measures, with a toggle to force any single tier and watch the decision change.

Run: streamlit run app.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent
os.chdir(REPO_ROOT)  # router.py/context.py resolve dataset/ and docs/ relative to cwd

SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# -- server-side secret handling ---------------------------------------------
# ANTHROPIC_API_KEY is read here from Streamlit secrets (server-side only --
# never sent to the browser) or the environment/.env, and pushed into
# os.environ *before* any Router/CascadeRouter is constructed below, since
# those classes read the env var once in __init__. It is never displayed,
# logged, or echoed back in the UI anywhere in this file.
def _configure_api_key() -> bool:
    key = None
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        key = None
    key = key or os.environ.get("ANTHROPIC_API_KEY")
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key
    return bool(key)


_HAS_API_KEY = _configure_api_key()

from cheap_classifier import CheapClassifier, load_training_data  # noqa: E402
from cascade_router import (  # noqa: E402
    TIER_LLM,
    TIER_LLM_UNAVAILABLE,
    TIER_MIXED,
    TIER_TIER2_FULL,
    CascadeRouter,
)
from context import ContextAssembler  # noqa: E402
from media import MediaExtractor  # noqa: E402

# ---------------------------------------------------------------------------
# Personas -- real user_ids paired with real recipients/senders/groups/
# businesses already in dataset/, so evidence retrieval and the
# rules/classifier/LLM all see genuine relationship history, not placeholders.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Persona:
    key: str
    name: str
    user_id: str
    conversation_type: str  # "personal" | "group" | "business"
    blurb: str
    group_id: Optional[str] = None
    business_id: Optional[str] = None
    sender_user_id: Optional[str] = None


PERSONAS = [
    Persona(
        key="priya",
        name="Priya (u_032) -- Myntra Marketplace group",
        user_id="u_032",
        conversation_type="group",
        group_id="group_005",
        sender_user_id="u_048",
        blurb="Opened a near-identical peer listing from this same seller before -- receptive to marketplace posts.",
    ),
    Persona(
        key="rohan",
        name="Rohan (u_033) -- Myntra Marketplace group",
        user_id="u_033",
        conversation_type="group",
        group_id="group_005",
        sender_user_id="u_048",
        blurb="Dismissed and muted a near-identical peer listing from this same seller before -- the mirror image of Priya.",
    ),
    Persona(
        key="aditi",
        name="Aditi (u_002) -- Mehra Family group",
        user_id="u_002",
        conversation_type="group",
        group_id="group_001",
        sender_user_id="u_001",
        blurb="A regular member of the Mehra Family group; the sender is one of this group's admins.",
    ),
    Persona(
        key="kabir",
        name="Kabir (u_009) -- personal chat",
        user_id="u_009",
        conversation_type="personal",
        sender_user_id="u_050",
        blurb="This sender has a history of direct OTP/KYC-verification demands to Kabir -- a known scam pattern.",
    ),
    Persona(
        key="meera",
        name="Meera (u_040) -- business: Loan Verification Desk",
        user_id="u_040",
        conversation_type="business",
        business_id="business_098",
        blurb="Has repeatedly dismissed and opted out of this unverified business (no official domain on file).",
    ),
    Persona(
        key="vikram",
        name="Vikram (u_004) -- business: MakeMyTrip",
        user_id="u_004",
        conversation_type="business",
        business_id="business_005",
        blurb="Verified travel business with a confirmed booking on file; opted into promotions and engages regularly.",
    ),
]
PERSONA_BY_KEY = {p.key: p for p in PERSONAS}

MODE_RULES = "rules"
MODE_CASCADE = "cascade"
MODE_FULL_LLM = "full_llm"

_SOURCE_LABELS = {
    TIER_TIER2_FULL: "Tier 2 -- cheap classifier resolved both fields locally (no LLM call)",
    TIER_MIXED: "Tier 1 + Tier 2 mix -- classifier's action, rules' message_type (no LLM call)",
    TIER_LLM: "Tier 3 -- escalated to the LLM",
    TIER_LLM_UNAVAILABLE: "Tier 3 unavailable (no server API key) -- fell back to Tier 1 rules",
    "tier1_rules_forced": "Tier 1 rules only (forced by the mode toggle)",
    "llm_forced": "Full LLM (forced by the mode toggle)",
    "rules_no_api_key": "Rules only -- no ANTHROPIC_API_KEY configured on the server",
    "rules_fallback_after_llm_failure": "Rules fallback -- the forced LLM call failed or returned invalid output",
}

_ACTION_COLORS = {"notify": "#16a34a", "digest": "#d97706", "mute": "#dc2626"}

_IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "bmp"}
_VOICE_EXTS = {"wav", "mp3", "m4a", "ogg", "flac", "webm"}

DAILY_LLM_CAP = int(os.environ.get("DEMO_DAILY_LLM_CAP", "50"))
COUNTER_PATH = SRC_DIR / ".cache" / "demo_daily_usage.json"


# ---------------------------------------------------------------------------
# Daily LLM-call budget -- a file-backed counter (not per-session state) since
# a hosted demo can have multiple concurrent visitors sharing one real API
# budget. Counts genuine fresh API calls only (Router.usage_stats["api_calls"]
# + image-vision calls), never cache hits, so it tracks real cost, not requests.
# ---------------------------------------------------------------------------


def _load_counter() -> dict[str, Any]:
    today = date.today().isoformat()
    if COUNTER_PATH.exists():
        try:
            data = json.loads(COUNTER_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
        if data.get("date") == today:
            return data
    return {"date": today, "count": 0}


def _save_counter(data: dict[str, Any]) -> None:
    COUNTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    COUNTER_PATH.write_text(json.dumps(data), encoding="utf-8")


def _record_llm_calls(n: int) -> int:
    data = _load_counter()
    if n > 0:
        data["count"] += n
        _save_counter(data)
    return data["count"]


# ---------------------------------------------------------------------------
# Pipeline construction -- one shared CascadeRouter (it subclasses Router, so
# its inherited _route_via_rules / _route_via_llm / _apply_overrides cover the
# forced rules-only and forced full-LLM modes too; only .route() runs the
# full 3-tier cascade), cached so it survives Streamlit reruns.
# ---------------------------------------------------------------------------


class UploadAwareMediaExtractor(MediaExtractor):
    """Lets an uploaded file stand in for an images.csv/voice_notes.csv row
    without writing to those files -- resolve_media_path is the only method
    extract_for_message uses to go from (media_type, media_id) to a file path."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._upload_paths: dict[str, str] = {}
        self.image_llm_calls = 0

    def register_upload(self, media_id: str, file_path: str) -> None:
        self._upload_paths[media_id] = file_path

    def resolve_media_path(self, media_type: str, media_id: str) -> Optional[str]:
        if media_id in self._upload_paths:
            return self._upload_paths[media_id]
        return super().resolve_media_path(media_type, media_id)

    def _extract_image_via_llm(self, file_path: str) -> dict[str, Any]:
        self.image_llm_calls += 1
        return super()._extract_image_via_llm(file_path)


@st.cache_resource(show_spinner="Loading dataset and fitting the tier-2 classifier...")
def _load_pipeline() -> CascadeRouter:
    context_assembler = ContextAssembler(dataset_dir="dataset", top_k=3)
    media_extractor = UploadAwareMediaExtractor(dataset_dir="dataset")
    classifier = CheapClassifier().fit(load_training_data())
    return CascadeRouter(
        dataset_dir="dataset",
        classifier=classifier,
        context_assembler=context_assembler,
        media_extractor=media_extractor,
    )


router = _load_pipeline()

# ---------------------------------------------------------------------------
# Architecture diagram (sidebar) -- mirrors the pipeline in README.md's mermaid
# diagram; matplotlib is already a project dependency (used for the confusion
# matrices), so this needs no extra package and renders identically everywhere.
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner=False)
def _build_architecture_figure():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    boxes = [
        (10, "Incoming message\ncontext + media extraction", "#1f2937"),
        (8.4, "Tier 1 -- Rules\nalways runs, free, instant", "#1f2937"),
        (6.8, "Tier 2 -- Cheap classifier\naction >=0.9 & safe pattern\ntype >=0.9 & validated class", "#1f2937"),
        (5.0, "Tier 3 -- LLM escalation\nclaude-haiku-4-5", "#1f2937"),
        (3.2, "Safety overrides\nscam/spam->mute, evidence check,\nconfidence calibration", "#1f2937"),
        (1.6, "Routing decision\naction, message_type, reason,\nconfidence, evidence", "#1f2937"),
    ]
    fig, ax = plt.subplots(figsize=(4.2, 7.4))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11.2)
    ax.axis("off")

    for y, label, color in boxes:
        box = FancyBboxPatch(
            (0.6, y - 0.55), 8.8, 1.1,
            boxstyle="round,pad=0.08,rounding_size=0.12",
            linewidth=1.2, edgecolor=color, facecolor="#f3f4f6",
        )
        ax.add_patch(box)
        ax.text(5.0, y, label, ha="center", va="center", fontsize=7.6, color=color, linespacing=1.4)

    # sequential arrows down the stack
    for (y1, *_), (y2, *_) in zip(boxes, boxes[1:]):
        ax.add_patch(FancyArrowPatch((5.0, y1 - 0.55), (5.0, y2 + 0.55), arrowstyle="-|>", mutation_scale=10, color="#6b7280"))

    # tier-2 -> safety-overrides bypass when tier 2 resolves the message locally
    bypass = FancyArrowPatch(
        (9.3, 6.8), (9.3, 3.2), connectionstyle="arc3,rad=0.5",
        arrowstyle="-|>", mutation_scale=9, color="#16a34a", linewidth=1.1, linestyle="--",
    )
    ax.add_patch(bypass)
    ax.text(9.9, 5.0, "resolved\nlocally", ha="left", va="center", fontsize=6.2, color="#16a34a", rotation=90)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Message construction + routing
# ---------------------------------------------------------------------------


def _build_message_row(persona: Persona, message_text: str, media_type: Optional[str], media_id: Optional[str], forwarded_count: int) -> pd.Series:
    return pd.Series({
        "message_id": f"demo_{uuid.uuid4().hex[:10]}",
        "user_id": persona.user_id,
        "conversation_type": persona.conversation_type,
        "group_id": persona.group_id,
        "business_id": persona.business_id,
        "sender_user_id": persona.sender_user_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "message_text": message_text or None,
        "media_type": media_type,
        "media_id": media_id,
        "forwarded_count": forwarded_count,
    })


def _run_routing(message: pd.Series, mode: str) -> dict[str, Any]:
    before_router_calls = router.usage_stats["api_calls"]
    before_img_calls = router.media.image_llm_calls
    saved_vision_client = None

    if mode == MODE_RULES:
        # Force zero API cost: image extraction defaults to the vision LLM
        # whenever a key is configured, independent of the classification
        # mode -- disable it here so "rules-only" genuinely means $0.
        saved_vision_client = router.media._anthropic_client
        router.media._anthropic_client = None

    try:
        ctx = router.context.build_context_for_row(message)
        media_result = router.media.extract_for_message(message)

        if mode == MODE_CASCADE:
            result = router.route(message)
        elif mode == MODE_RULES:
            raw = router._route_via_rules(message, ctx, media_result)
            result = router._apply_overrides(message, ctx, media_result, raw)
            result["_source"] = "tier1_rules_forced"
        else:  # MODE_FULL_LLM
            if not router.llm_available:
                raw = router._route_via_rules(message, ctx, media_result)
                result = router._apply_overrides(message, ctx, media_result, raw)
                result["_source"] = "rules_no_api_key"
            else:
                llm_raw = router._route_via_llm(message, ctx, media_result)
                if llm_raw is None:
                    raw = router._route_via_rules(message, ctx, media_result)
                    result = router._apply_overrides(message, ctx, media_result, raw)
                    result["_source"] = "rules_fallback_after_llm_failure"
                else:
                    result = router._apply_overrides(message, ctx, media_result, llm_raw)
                    result["_source"] = "llm_forced"
    finally:
        if saved_vision_client is not None or mode == MODE_RULES:
            router.media._anthropic_client = saved_vision_client

    result["_ctx"] = ctx
    result["_media_result"] = media_result
    delta = (router.usage_stats["api_calls"] - before_router_calls) + (router.media.image_llm_calls - before_img_calls)
    result["_llm_calls_this_request"] = delta
    result["_daily_total_after"] = _record_llm_calls(delta)
    return result


def _detect_media_type(uploaded_file) -> Optional[str]:
    ext = Path(uploaded_file.name).suffix.lower().lstrip(".")
    mime = uploaded_file.type or ""
    if ext in _IMAGE_EXTS or mime.startswith("image/"):
        return "image"
    if ext in _VOICE_EXTS or mime.startswith("audio/"):
        return "voice"
    return None


def _save_upload(uploaded_file) -> tuple[Optional[str], str]:
    media_type = _detect_media_type(uploaded_file)
    media_id = f"upload_{uuid.uuid4().hex[:10]}"
    ext = Path(uploaded_file.name).suffix or ""
    tmp_dir = Path(tempfile.gettempdir()) / "notification_router_demo_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"{media_id}{ext}"
    tmp_path.write_bytes(uploaded_file.getvalue())
    router.media.register_upload(media_id, str(tmp_path))
    return media_type, media_id


def _format_reaction(reaction: Optional[dict[str, Any]]) -> str:
    if not reaction:
        return "no reaction on file"
    if reaction.get("message_reported") == 1:
        return "reported"
    if reaction.get("muted_after_message") == 1:
        return "muted the sender afterward"
    if reaction.get("notification_dismissed") == 1:
        return "dismissed without opening"
    if reaction.get("message_opened") == 1:
        minutes = reaction.get("reaction_time_minutes")
        return f"opened ({minutes:.0f} min)" if isinstance(minutes, (int, float)) else "opened"
    return "no reaction on file"


def _evidence_details(result: dict[str, Any], user_id: str) -> list[dict[str, Any]]:
    ids_str = result.get("evidence_message_ids") or "none"
    ids = [] if ids_str == "none" else ids_str.split(";")
    by_id = {e["message_id"]: e for e in (result.get("_ctx") or {}).get("evidence") or []}
    details = []
    for mid in ids:
        if mid in by_id:
            e = by_id[mid]
            details.append({"message_id": mid, "message_text": e.get("message_text"), "reaction": _format_reaction(e.get("reaction"))})
            continue
        # fall back to a raw lookup for any cited id retrieval didn't surface
        rows = router.context.data.message_history[router.context.data.message_history.message_id == mid]
        if rows.empty:
            continue
        events = router.context.data.message_events[
            (router.context.data.message_events.message_id == mid) & (router.context.data.message_events.user_id == user_id)
        ]
        reaction = events.iloc[0].to_dict() if len(events) else None
        details.append({"message_id": mid, "message_text": rows.iloc[0].message_text, "reaction": _format_reaction(reaction)})
    return details


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Multimodal Notification Router -- Live Demo", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("Architecture")
    st.pyplot(_build_architecture_figure(), use_container_width=True)
    st.caption(
        "Tier 2's two fields are gated independently: action needs >=0.9 confidence and "
        "no safety/urgency/credential pattern match; message_type needs >=0.9 confidence "
        "AND membership in the 6 classes that had enough training data to validate. "
        "Either field failing its own gate escalates just that message to the LLM."
    )

    st.divider()
    st.header("Routing mode")
    mode_choice = st.radio(
        "Force a specific tier, or let the cascade decide:",
        options=[MODE_CASCADE, MODE_RULES, MODE_FULL_LLM],
        format_func=lambda m: {MODE_CASCADE: "Cascade (default)", MODE_RULES: "Rules only", MODE_FULL_LLM: "Full LLM"}[m],
        help="Cascade runs the real 3-tier pipeline. Rules only and Full LLM force a single tier so you can compare.",
    )

    st.divider()
    st.header("Daily LLM budget")
    counter = _load_counter()
    st.progress(min(counter["count"] / DAILY_LLM_CAP, 1.0))
    st.caption(f"{counter['count']} / {DAILY_LLM_CAP} LLM calls used today (resets at midnight local time on the server).")
    st.caption(f"Server LLM access: {'configured' if _HAS_API_KEY else 'not configured -- every mode falls back to rules-only'}.")

    if st.session_state.history:
        st.divider()
        if st.button("Clear conversation"):
            st.session_state.history = []
            st.rerun()

st.title("Multimodal Notification Router")
st.caption("Live demo -- routes a message through the real pipeline and dataset behind this project.")

persona_key = st.selectbox(
    "Simulated recipient",
    options=[p.key for p in PERSONAS],
    format_func=lambda k: PERSONA_BY_KEY[k].name,
)
persona = PERSONA_BY_KEY[persona_key]
st.caption(persona.blurb)

for turn in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(f"**{turn['persona_name']}**")
        st.write(turn["message_text"] or "*(no text -- media only)*")
        if turn.get("media_label"):
            st.caption(turn["media_label"])
    with st.chat_message("assistant"):
        st.markdown(turn["result_html"], unsafe_allow_html=True)
        st.progress(turn["confidence"], text=f"confidence: {turn['confidence']:.0%}")
        if turn.get("evidence"):
            with st.expander(f"Cited evidence ({len(turn['evidence'])})"):
                for ev in turn["evidence"]:
                    st.markdown(f"- **{ev['message_id']}** ({ev['reaction']}): {ev['message_text']!r}")
        st.caption(turn["meta_caption"])

with st.form("route_form", clear_on_submit=True):
    message_text = st.text_area("Message", placeholder="Type or paste a WhatsApp-style message...", height=90)
    uploaded_file = st.file_uploader("Attach an image or voice note (optional)", type=sorted(_IMAGE_EXTS | _VOICE_EXTS))
    with st.expander("Advanced"):
        forwarded_count = st.number_input("Forwarded count", min_value=0, max_value=20, value=0, step=1)
    submitted = st.form_submit_button("Route this message", use_container_width=True)

if submitted:
    if not message_text.strip() and uploaded_file is None:
        st.warning("Type a message or attach a file first.")
    else:
        media_type = media_id = None
        media_label = None
        if uploaded_file is not None:
            media_type, media_id = _save_upload(uploaded_file)
            if media_type is None:
                st.warning(f"Couldn't recognize {uploaded_file.name!r} as an image or voice note; ignoring the attachment.")
                media_id = None
            else:
                media_label = f"[{media_type} attached: {uploaded_file.name}]"

        counter = _load_counter()
        cap_reached = counter["count"] >= DAILY_LLM_CAP
        effective_mode = MODE_RULES if (cap_reached and mode_choice != MODE_RULES) else mode_choice
        if cap_reached and mode_choice != MODE_RULES:
            st.info(
                f"Daily LLM budget ({DAILY_LLM_CAP} calls) is used up for today -- showing the "
                f"rules-only result instead of {('the cascade' if mode_choice == MODE_CASCADE else 'the full-LLM path')}. "
                "It resets at midnight local time on the server."
            )

        with st.spinner("Routing..."):
            message_row = _build_message_row(persona, message_text.strip(), media_type, media_id, int(forwarded_count))
            result = _run_routing(message_row, effective_mode)

        action = result["action"]
        color = _ACTION_COLORS.get(action, "#6b7280")
        badge = (
            f'<span style="background-color:{color};color:#fff;padding:3px 12px;border-radius:999px;'
            f'font-weight:700;font-size:0.95rem;letter-spacing:0.03em;">{action.upper()}</span>'
        )
        type_badge = (
            f'<span style="background-color:#374151;color:#fff;padding:2px 10px;border-radius:999px;'
            f'font-size:0.8rem;margin-left:8px;">{result["message_type"]}</span>'
        )
        confidence = min(max(float(result.get("confidence", 0.0)), 0.0), 1.0)
        result_html = f"{badge}{type_badge}<br><br><em>{result['reason']}</em>"

        evidence = _evidence_details(result, persona.user_id)
        source_label = _SOURCE_LABELS.get(result.get("_source", ""), result.get("_source", "unknown"))
        meta_caption = f"{source_label} · {result['_llm_calls_this_request']} LLM call(s) this request · {result['_daily_total_after']}/{DAILY_LLM_CAP} used today"

        st.session_state.history.append({
            "persona_name": persona.name,
            "message_text": message_text.strip(),
            "media_label": media_label,
            "result_html": result_html,
            "confidence": confidence,
            "evidence": evidence,
            "meta_caption": meta_caption,
        })
        st.session_state.history = st.session_state.history[-20:]
        st.rerun()
