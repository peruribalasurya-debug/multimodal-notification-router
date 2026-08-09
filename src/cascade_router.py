"""Three-tier classification cascade for the message notification router.

Tier 1 -- audited deterministic rules (Router._route_via_rules, as built).
    Always computed first (it's free and instant). Supplies a candidate
    action/message_type and, critically, the evidence_message_ids the other
    tiers reuse -- and its own message_type is used to complete tier 2's
    result when tier 2's message_type isn't trustworthy but its action is
    (see tier 2 below).

Tier 2 -- the cheap classifier (src/cheap_classifier.py), gated per-field on
    its own validated numbers (see reports from that module's CV run):
        - action: accepted only if confidence >= action_threshold (default
          0.9 -- validated at 92.3% accuracy / ~50% coverage).
        - message_type: accepted only if confidence >= message_type_threshold
          (default 0.9) AND the predicted class is in
          validated_message_type_classes (default: scam, forward, promotion,
          urgent, event, personal -- the 6 classes that had enough training
          examples for a trustworthy 5-fold CV score). business_update,
          greeting, payment, unknown, and spam are NEVER accepted from tier 2
          regardless of confidence -- those classes had no valid CV score at
          all.
    Three outcomes:
        - action AND message_type both accepted -> resolved fully at tier 2.
        - action accepted, message_type not, but tier 1 independently
          determined message_type (i.e. didn't fall through to its own
          generic catch-all, message_type=="unknown") -> resolved as a mix:
          tier 2's action + tier 1's message_type. This is NOT the same as
          "fully tier 2" -- reported separately in tier_stats.
        - anything else (action not accepted, or message_type not accepted
          and tier 1 also had nothing to offer) -> escalate the WHOLE message
          to tier 3. Never mixes an unaccepted tier-2 field with tier 3.

Tier 3 -- LLM escalation (Router._route_via_llm), for everything not resolved
    by tiers 1-2. Uses the router's own response cache, so a rerun over an
    unchanged prompt costs nothing.

The safety override layer (Router._apply_overrides -- scam/spam forces mute,
evidence validated against message_history.csv, reason normalized, confidence
calibrated) runs exactly once, last, on whatever the cascade produced,
regardless of which tier(s) contributed -- this is non-negotiable and not
configurable, matching every other entry point in this codebase.

CLI:
    python -m src.cascade_router            # runs the pure-LLM vs cascade
                                              # benchmark and writes
                                              # reports/cascade_benchmark.md
"""

from __future__ import annotations

import os
import sys
import time
from collections import Counter
from typing import Any, Optional

import numpy as np
import pandas as pd

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SRC_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from cheap_classifier import CheapClassifier, extract_context_features, feature_row_to_dataframe, load_training_data  # noqa: E402
from router import (  # noqa: E402
    CREDENTIAL_PATTERN, DEFAULT_MODEL, HARD_URGENCY_PATTERN, INJECTION_PATTERN, INPUT_COLUMNS,
    MESSAGE_TYPES, Router, _strip_negations,
)

DATASET_DIR = os.path.join(REPO_ROOT, "dataset")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")
BENCHMARK_PATH = os.path.join(REPORTS_DIR, "cascade_benchmark.md")

# -- configurable cascade gates (see cheap_classifier's CV report for the numbers behind these defaults) --
DEFAULT_ACTION_THRESHOLD = 0.9
DEFAULT_MESSAGE_TYPE_THRESHOLD = 0.9
# The 6 message_type classes that had >= MIN_CLASS_SIZE_FOR_CV training examples and
# therefore a trustworthy 5-fold CV score (56.2% overall, per-class F1 0.24-0.79).
# business_update / greeting / payment / unknown / spam are deliberately excluded --
# they had 1-4 training examples each and no valid CV estimate.
DEFAULT_VALIDATED_MESSAGE_TYPE_CLASSES = frozenset({"scam", "forward", "promotion", "urgent", "event", "personal"})

# Diagnosed via reports/cascade_benchmark.md's synth_003 case: the cheap classifier's
# action head was confidently (p=0.99) wrong on a genuine safety emergency, predicting
# mute instead of notify. Root cause, quantified against the training data
# (messages_llm_labeled_full.csv): of 25 training rows containing alarm vocabulary
# (immediately/emergency/urgent/now), 14 are mute (11 of them scam) vs only 9 notify (7
# urgent) -- a 56%/36% skew toward mute, because manufactured-urgency scam messages
# outnumber genuine emergencies in the real dataset. The classifier learned "alarm
# language leans mute" as a shortcut, which misfires specifically on genuine
# emergencies using similar vocabulary. Raising action_threshold doesn't help here --
# 0.99 already clears any reasonable bar -- so instead: messages matching these
# already-audited-as-general safety/urgency patterns (the same ones tier 1's rules 1/2
# and 6.5/7 use) are excluded from tier-2 action eligibility entirely, regardless of
# confidence, and fall through to escalation instead.
ACTION_INELIGIBILITY_PATTERNS = (INJECTION_PATTERN, CREDENTIAL_PATTERN, HARD_URGENCY_PATTERN)

TIER_TIER2_FULL = "tier2_full"
TIER_MIXED = "tier1_type_tier2_action"
TIER_LLM = "tier3_llm"
TIER_LLM_UNAVAILABLE = "tier3_unavailable_fallback_tier1"


class CascadeRouter(Router):
    """Router subclass that resolves messages through the tier1 -> tier2 ->
    tier3 cascade described in this module's docstring, instead of the base
    Router's LLM-primary-with-rules-fallback flow."""

    def __init__(
        self,
        dataset_dir: str = "dataset",
        model: str = DEFAULT_MODEL,
        classifier: Optional[CheapClassifier] = None,
        action_threshold: float = DEFAULT_ACTION_THRESHOLD,
        message_type_threshold: float = DEFAULT_MESSAGE_TYPE_THRESHOLD,
        validated_message_type_classes: Optional[frozenset[str]] = None,
        restrict_action_eligibility: bool = True,
        **router_kwargs: Any,
    ):
        super().__init__(dataset_dir=dataset_dir, model=model, **router_kwargs)
        self.classifier = classifier or CheapClassifier().fit(load_training_data())
        self.action_threshold = action_threshold
        self.message_type_threshold = message_type_threshold
        self.validated_message_type_classes = validated_message_type_classes or DEFAULT_VALIDATED_MESSAGE_TYPE_CLASSES
        # See ACTION_INELIGIBILITY_PATTERNS above -- confidence alone can't catch a
        # confidently-wrong prediction, so this is a categorical exclusion, not a gate.
        self.restrict_action_eligibility = restrict_action_eligibility
        self.tier_stats: Counter[str] = Counter()

    def _tier2_action_eligible(self, message: pd.Series, media_result: dict[str, Any]) -> bool:
        if not self.restrict_action_eligibility:
            return True
        text = _strip_negations(self._combined_text(message, media_result))
        return not any(pattern.search(text) for pattern in ACTION_INELIGIBILITY_PATTERNS)

    def route(self, message: pd.Series) -> dict[str, Any]:
        ctx = self.context.build_context_for_row(message)
        media_result = self.media.extract_for_message(message)

        # Tier 1: always computed -- free, and needed either as the final
        # candidate (mixed resolution) or as evidence-id source regardless.
        tier1_raw = self._route_via_rules(message, ctx, media_result)
        tier1_message_type_is_informed = tier1_raw["message_type"] != "unknown"

        # Tier 2
        features = extract_context_features(message, ctx, media_result)
        feature_df = feature_row_to_dataframe(features)
        proba = self.classifier.predict_proba(feature_df)

        action_classes, action_proba = proba["action"]["classes"], proba["action"]["proba"][0]
        type_classes, type_proba = proba["message_type"]["classes"], proba["message_type"]["proba"][0]
        tier2_action = action_classes[int(np.argmax(action_proba))]
        tier2_action_conf = float(action_proba.max())
        tier2_message_type = type_classes[int(np.argmax(type_proba))]
        tier2_message_type_conf = float(type_proba.max())

        action_accepted = (
            tier2_action_conf >= self.action_threshold
            and self._tier2_action_eligible(message, media_result)
        )
        message_type_accepted = (
            tier2_message_type_conf >= self.message_type_threshold
            and tier2_message_type in self.validated_message_type_classes
        )

        if action_accepted and message_type_accepted:
            source = TIER_TIER2_FULL
            raw = {
                "action": tier2_action,
                "message_type": tier2_message_type,
                "reason": (
                    f"Tier-2 cheap classifier: action={tier2_action} (p={tier2_action_conf:.2f}), "
                    f"message_type={tier2_message_type} (p={tier2_message_type_conf:.2f})."
                ),
                "confidence": min(tier2_action_conf, tier2_message_type_conf),
                "evidence_message_ids": tier1_raw["evidence_message_ids"],
            }
        elif action_accepted and tier1_message_type_is_informed:
            source = TIER_MIXED
            raw = {
                "action": tier2_action,
                "message_type": tier1_raw["message_type"],
                "reason": (
                    f"Tier-2 cheap classifier action={tier2_action} (p={tier2_action_conf:.2f}); "
                    f"message_type from tier-1 rules: {tier1_raw['reason']}"
                ),
                "confidence": tier2_action_conf,
                "evidence_message_ids": tier1_raw["evidence_message_ids"],
            }
        else:
            # Tier 3
            llm_raw = self._route_via_llm(message, ctx, media_result) if self.llm_available else None
            if llm_raw is not None:
                source = TIER_LLM
                raw = llm_raw
            else:
                # No API key / LLM path unavailable -- degrade to tier 1's own
                # candidate rather than fail; this is the only case where tier
                # 1 resolves entirely on its own.
                source = TIER_LLM_UNAVAILABLE
                raw = tier1_raw

        final = self._apply_overrides(message, ctx, media_result, raw)
        final["_source"] = source
        final["_tier2_action_confidence"] = tier2_action_conf
        final["_tier2_message_type_confidence"] = tier2_message_type_conf
        self.tier_stats[source] += 1
        return final


# ---------------------------------------------------------------------------
# Benchmark: pure-LLM vs cascade, on sample_messages.csv and synthetic_test.csv
# ---------------------------------------------------------------------------

def _accuracy(df: pd.DataFrame) -> tuple[float, float, float]:
    action_acc = float((df.expected_action == df.predicted_action).mean())
    type_acc = float((df.expected_message_type == df.predicted_message_type).mean())
    full_acc = float(((df.expected_action == df.predicted_action) & (df.expected_message_type == df.predicted_message_type)).mean())
    return action_acc, type_acc, full_acc


def _run_pure_llm(dataset_path: str, use_response_cache: bool = True) -> dict[str, Any]:
    samples = pd.read_csv(dataset_path)
    router = Router(dataset_dir=DATASET_DIR, use_response_cache=use_response_cache)
    rows = []
    t0 = time.time()
    for _, row in samples.iterrows():
        pred = router.route(row[INPUT_COLUMNS])
        rows.append({
            "message_id": row.message_id,
            "expected_action": row.action, "predicted_action": pred["action"],
            "expected_message_type": row.message_type, "predicted_message_type": pred["message_type"],
            "_source": pred["_source"],
        })
    elapsed = time.time() - t0
    df = pd.DataFrame(rows)
    action_acc, type_acc, full_acc = _accuracy(df)
    pricing = (1.00, 5.00) if router.model == "claude-haiku-4-5" else None
    cost = None
    if pricing:
        cost = (router.usage_stats["input_tokens"] / 1e6) * pricing[0] + (router.usage_stats["output_tokens"] / 1e6) * pricing[1]
    return {
        "n": len(df), "action_acc": action_acc, "type_acc": type_acc, "full_acc": full_acc,
        "elapsed_s": elapsed, "api_calls": router.usage_stats["api_calls"],
        "cache_hits": router.usage_stats["cache_hits"], "cache_misses": router.usage_stats["cache_misses"],
        "input_tokens": router.usage_stats["input_tokens"], "output_tokens": router.usage_stats["output_tokens"],
        "cost": cost, "model": router.model, "df": df,
    }


def _run_cascade(
    dataset_path: str,
    classifier: CheapClassifier,
    use_response_cache: bool = True,
    action_threshold: float = DEFAULT_ACTION_THRESHOLD,
    message_type_threshold: float = DEFAULT_MESSAGE_TYPE_THRESHOLD,
    validated_message_type_classes: Optional[frozenset[str]] = None,
    restrict_action_eligibility: bool = True,
) -> dict[str, Any]:
    samples = pd.read_csv(dataset_path)
    router = CascadeRouter(
        dataset_dir=DATASET_DIR,
        classifier=classifier,
        use_response_cache=use_response_cache,
        action_threshold=action_threshold,
        message_type_threshold=message_type_threshold,
        validated_message_type_classes=validated_message_type_classes,
        restrict_action_eligibility=restrict_action_eligibility,
    )
    rows = []
    t0 = time.time()
    for _, row in samples.iterrows():
        pred = router.route(row[INPUT_COLUMNS])
        rows.append({
            "message_id": row.message_id,
            "expected_action": row.action, "predicted_action": pred["action"],
            "expected_message_type": row.message_type, "predicted_message_type": pred["message_type"],
            "_source": pred["_source"],
            "_tier2_action_confidence": pred["_tier2_action_confidence"],
            "_tier2_message_type_confidence": pred["_tier2_message_type_confidence"],
        })
    elapsed = time.time() - t0
    df = pd.DataFrame(rows)
    action_acc, type_acc, full_acc = _accuracy(df)
    pricing = (1.00, 5.00) if router.model == "claude-haiku-4-5" else None
    cost = None
    if pricing:
        cost = (router.usage_stats["input_tokens"] / 1e6) * pricing[0] + (router.usage_stats["output_tokens"] / 1e6) * pricing[1]
    n = len(df)
    tier_stats = router.tier_stats
    return {
        "n": n, "action_acc": action_acc, "type_acc": type_acc, "full_acc": full_acc,
        "elapsed_s": elapsed, "api_calls": router.usage_stats["api_calls"],
        "cache_hits": router.usage_stats["cache_hits"], "cache_misses": router.usage_stats["cache_misses"],
        "input_tokens": router.usage_stats["input_tokens"], "output_tokens": router.usage_stats["output_tokens"],
        "cost": cost, "model": router.model,
        "tier_stats": dict(tier_stats),
        "pct_tier2_full": tier_stats.get(TIER_TIER2_FULL, 0) / n,
        "pct_tier1_type_tier2_action": tier_stats.get(TIER_MIXED, 0) / n,
        "pct_tier3_llm": (tier_stats.get(TIER_LLM, 0) + tier_stats.get(TIER_LLM_UNAVAILABLE, 0)) / n,
        "tier2_resolutions_total": tier_stats.get(TIER_TIER2_FULL, 0) + tier_stats.get(TIER_MIXED, 0),
        "tier2_full_fraction_of_tier2": (
            tier_stats.get(TIER_TIER2_FULL, 0) / (tier_stats.get(TIER_TIER2_FULL, 0) + tier_stats.get(TIER_MIXED, 0))
            if (tier_stats.get(TIER_TIER2_FULL, 0) + tier_stats.get(TIER_MIXED, 0)) > 0 else float("nan")
        ),
        "tier2_mixed_fraction_of_tier2": (
            tier_stats.get(TIER_MIXED, 0) / (tier_stats.get(TIER_TIER2_FULL, 0) + tier_stats.get(TIER_MIXED, 0))
            if (tier_stats.get(TIER_TIER2_FULL, 0) + tier_stats.get(TIER_MIXED, 0)) > 0 else float("nan")
        ),
        "df": df,
    }


def _fmt_cost(cost: Optional[float]) -> str:
    return f"${cost:.4f}" if cost is not None else "n/a"


def _render_dataset_section(label: str, dataset_path: str, llm_result: dict, cascade_result: dict) -> str:
    lines = [f"## {label}\n"]
    lines.append(f"`{os.path.relpath(dataset_path, REPO_ROOT)}`, n={llm_result['n']}\n")
    lines.append("| | action acc | message_type acc | fully correct | wall-clock | LLM calls | cost |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.append(
        f"| Pure LLM | {llm_result['action_acc']:.1%} | {llm_result['type_acc']:.1%} | {llm_result['full_acc']:.1%} "
        f"| {llm_result['elapsed_s']:.1f}s | {llm_result['api_calls']} | {_fmt_cost(llm_result['cost'])} |"
    )
    lines.append(
        f"| Cascade | {cascade_result['action_acc']:.1%} | {cascade_result['type_acc']:.1%} | {cascade_result['full_acc']:.1%} "
        f"| {cascade_result['elapsed_s']:.1f}s | {cascade_result['api_calls']} | {_fmt_cost(cascade_result['cost'])} |"
    )
    lines.append("")
    lines.append("### Cascade resolution breakdown\n")
    lines.append("| Tier | Rows | % of total |")
    lines.append("|---|---|---|")
    n = cascade_result["n"]
    ts = cascade_result["tier_stats"]
    tier2_full = ts.get(TIER_TIER2_FULL, 0)
    mixed = ts.get(TIER_MIXED, 0)
    llm_n = ts.get(TIER_LLM, 0) + ts.get(TIER_LLM_UNAVAILABLE, 0)
    lines.append(f"| Tier 2 -- fully resolved (action + message_type both from classifier) | {tier2_full} | {tier2_full/n:.1%} |")
    lines.append(f"| Tier 1+2 mixed -- tier-2 action + tier-1 message_type | {mixed} | {mixed/n:.1%} |")
    lines.append(f"| Tier 3 -- escalated to LLM | {llm_n} | {llm_n/n:.1%} |")
    lines.append("")
    tier2_total = tier2_full + mixed
    if tier2_total > 0:
        lines.append(
            f"Of the {tier2_total} messages tier 2 resolved (fully or partially): "
            f"**{tier2_full}/{tier2_total} ({tier2_full/tier2_total:.1%}) were fully tier 2**, "
            f"**{mixed}/{tier2_total} ({mixed/tier2_total:.1%}) were the action-only-with-tier-1-type mix**."
        )
    else:
        lines.append("Tier 2 resolved 0 messages on this set.")
    lines.append("")
    return "\n".join(lines)


def diff_action_rows(dataset_path: str, llm_result: dict[str, Any], cascade_result: dict[str, Any]) -> pd.DataFrame:
    """Rows where the cascade's predicted action differs from pure LLM's, enriched
    with message text, which tier resolved the cascade's answer, the cheap
    classifier's own action confidence for that row (regardless of which tier
    ultimately supplied the action), and whether each side was actually correct."""
    raw = pd.read_csv(dataset_path)[["message_id", "message_text"]]
    llm = llm_result["df"][["message_id", "expected_action", "predicted_action"]].rename(
        columns={"predicted_action": "llm_action"}
    )
    cascade = cascade_result["df"][
        ["message_id", "predicted_action", "_source", "_tier2_action_confidence"]
    ].rename(columns={"predicted_action": "cascade_action"})

    merged = llm.merge(cascade, on="message_id").merge(raw, on="message_id")
    diff = merged[merged.llm_action != merged.cascade_action].copy()
    diff["llm_correct"] = diff.llm_action == diff.expected_action
    diff["cascade_correct"] = diff.cascade_action == diff.expected_action
    return diff.reset_index(drop=True)


def format_action_diff(diff: pd.DataFrame) -> str:
    if diff.empty:
        return "No rows -- cascade and pure LLM agreed on action for every message."
    lines = []
    for _, r in diff.iterrows():
        llm_mark = "correct" if r.llm_correct else "WRONG"
        cascade_mark = "correct" if r.cascade_correct else "WRONG"
        lines.append(f"- {r.message_id} (expected={r.expected_action})")
        lines.append(f"    text: {r.message_text!r}")
        lines.append(f"    pure LLM  -> {r.llm_action} ({llm_mark})")
        lines.append(
            f"    cascade   -> {r.cascade_action} ({cascade_mark}), resolved by {r._source}, "
            f"tier-2 action confidence for this row = {r._tier2_action_confidence:.2f}"
        )
    return "\n".join(lines)


def _render_dataset_section(
    label: str, dataset_path: str, llm_result: dict, cascade_result: dict, diff: Optional[pd.DataFrame] = None
) -> str:
    lines = [f"## {label}\n"]
    lines.append(f"`{os.path.relpath(dataset_path, REPO_ROOT)}`, n={llm_result['n']}\n")
    lines.append("| | action acc | message_type acc | fully correct | wall-clock | LLM calls | cost |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.append(
        f"| Pure LLM | {llm_result['action_acc']:.1%} | {llm_result['type_acc']:.1%} | {llm_result['full_acc']:.1%} "
        f"| {llm_result['elapsed_s']:.1f}s | {llm_result['api_calls']} | {_fmt_cost(llm_result['cost'])} |"
    )
    lines.append(
        f"| Cascade | {cascade_result['action_acc']:.1%} | {cascade_result['type_acc']:.1%} | {cascade_result['full_acc']:.1%} "
        f"| {cascade_result['elapsed_s']:.1f}s | {cascade_result['api_calls']} | {_fmt_cost(cascade_result['cost'])} |"
    )
    lines.append("")
    lines.append("### Cascade resolution breakdown\n")
    lines.append("| Tier | Rows | % of total |")
    lines.append("|---|---|---|")
    n = cascade_result["n"]
    ts = cascade_result["tier_stats"]
    tier2_full = ts.get(TIER_TIER2_FULL, 0)
    mixed = ts.get(TIER_MIXED, 0)
    llm_n = ts.get(TIER_LLM, 0) + ts.get(TIER_LLM_UNAVAILABLE, 0)
    lines.append(f"| Tier 2 -- fully resolved (action + message_type both from classifier) | {tier2_full} | {tier2_full/n:.1%} |")
    lines.append(f"| Tier 1+2 mixed -- tier-2 action + tier-1 message_type | {mixed} | {mixed/n:.1%} |")
    lines.append(f"| Tier 3 -- escalated to LLM | {llm_n} | {llm_n/n:.1%} |")
    lines.append("")
    tier2_total = tier2_full + mixed
    if tier2_total > 0:
        lines.append(
            f"Of the {tier2_total} messages tier 2 resolved (fully or partially): "
            f"**{tier2_full}/{tier2_total} ({tier2_full/tier2_total:.1%}) were fully tier 2**, "
            f"**{mixed}/{tier2_total} ({mixed/tier2_total:.1%}) were the action-only-with-tier-1-type mix**."
        )
    else:
        lines.append("Tier 2 resolved 0 messages on this set.")
    lines.append("")
    if diff is not None:
        lines.append("### Rows where cascade action != pure-LLM action\n")
        lines.append("```")
        lines.append(format_action_diff(diff))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def run_benchmark(
    action_threshold: float = DEFAULT_ACTION_THRESHOLD,
    message_type_threshold: float = DEFAULT_MESSAGE_TYPE_THRESHOLD,
    validated_message_type_classes: Optional[frozenset[str]] = None,
    use_response_cache: bool = False,
    restrict_action_eligibility: bool = True,
    note: str = "",
) -> str:
    """use_response_cache defaults to False here (unlike Router's own default)
    because this function's whole purpose is producing trustworthy cost/call
    numbers -- a cache hit from a previous run would silently understate both."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    classifier = CheapClassifier().fit(load_training_data())

    sections = []
    for label, filename in (
        ("sample_messages.csv", "sample_messages.csv"),
        ("synthetic_test.csv (held-out)", "synthetic_test.csv"),
    ):
        path = os.path.join(DATASET_DIR, filename)
        print(f"\n=== {label}: pure LLM (cache {'ON' if use_response_cache else 'OFF'}) ===")
        llm_result = _run_pure_llm(path, use_response_cache=use_response_cache)
        print(f"  action={llm_result['action_acc']:.1%} type={llm_result['type_acc']:.1%} "
              f"time={llm_result['elapsed_s']:.1f}s calls={llm_result['api_calls']} cost={_fmt_cost(llm_result['cost'])}")

        print(f"=== {label}: cascade (cache {'ON' if use_response_cache else 'OFF'}) ===")
        cascade_result = _run_cascade(
            path, classifier, use_response_cache=use_response_cache,
            action_threshold=action_threshold, message_type_threshold=message_type_threshold,
            validated_message_type_classes=validated_message_type_classes,
            restrict_action_eligibility=restrict_action_eligibility,
        )
        print(f"  action={cascade_result['action_acc']:.1%} type={cascade_result['type_acc']:.1%} "
              f"time={cascade_result['elapsed_s']:.1f}s calls={cascade_result['api_calls']} cost={_fmt_cost(cascade_result['cost'])}")
        print(f"  tiers: {cascade_result['tier_stats']}")

        diff = diff_action_rows(path, llm_result, cascade_result)
        if not diff.empty:
            print(f"  action differs from pure LLM on {len(diff)}/{cascade_result['n']} rows:")
            print(format_action_diff(diff))

        sections.append(_render_dataset_section(label, path, llm_result, cascade_result, diff=diff))

    ts_human = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    cache_note = (
        "Response cache was **disabled** for every LLM call in this run (both pure-LLM and cascade "
        "tier-3 escalations) -- every `LLM calls` / `cost` figure below reflects genuine fresh API "
        "calls, not cache hits left over from an earlier run."
        if not use_response_cache else
        "Response cache was left on for this run -- `LLM calls` / `cost` may reflect cache hits, not "
        "fresh calls."
    )
    header = f"""# Cascade Benchmark

Run {ts_human}. Compares the pure-LLM path (`src/router.py`'s `Router`) against
the 3-tier cascade (`src/cascade_router.py`'s `CascadeRouter`) on the same rows,
same model (`claude-haiku-4-5`).

{cache_note}

Cascade gates: `action_threshold={action_threshold}`,
`message_type_threshold={message_type_threshold}`,
`validated_message_type_classes={sorted(validated_message_type_classes or DEFAULT_VALIDATED_MESSAGE_TYPE_CLASSES)}`.
{note}
"""
    body = header + "\n".join(sections)
    with open(BENCHMARK_PATH, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"\nWrote {os.path.relpath(BENCHMARK_PATH, REPO_ROOT)}")
    return body


if __name__ == "__main__":
    run_benchmark()
