"""Evaluation harness for the message notification router.

Runs the full pipeline (src/context.py + src/media.py + src/router.py) against
dataset/sample_messages.csv -- the 30 labeled examples -- and reports how well
predictions match the expected labels:

  1. overall accuracy for action and message_type
  2. confusion matrices for each, printed as a table and saved as PNG heatmaps
  3. per-class precision / recall / F1
  4. confidence calibration: accuracy per confidence bucket + expected
     calibration error (ECE), saved as a reliability diagram PNG
  5. evidence quality: % of rows citing evidence, % of cited IDs that are
     valid (exist in message_history.csv), and overlap with the sample's own
     expected evidence where the sample provides one
  6. API usage: cache hits/misses on router.py's response cache, tokens spent,
     and an estimated cost for the run

If dataset/synthetic_test.csv exists, its rows (hand-crafted held-out cases the
rules were never tuned against) are also run and reported as a separate
"SYNTHETIC (HELD-OUT)" section -- never mixed into the sample_messages.csv numbers
above, so sample-set accuracy and held-out generalization stay distinguishable.

Every run appends a timestamped section to reports/eval_summary.md (a running
log, so results are comparable across runs over time) and writes both a
timestamped and a "latest" copy of each PNG to reports/.

CLI:
    python -m src.eval
    python -m src.eval --limit 5      # only the first 5 sample messages -- fast
                                       # iteration on rubric changes
    ROUTER_MODEL=claude-opus-5 python -m src.eval   # bigger model for final validation
    make eval
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import Any, Optional

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)  # so router.py's own sibling imports (context, media) resolve

# Windows consoles default to a legacy codepage (cp1252) that can't encode characters
# like "∩" used below -- force UTF-8 stdout/stderr so terminal output never crashes on
# them, regardless of the host console's configured codepage.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

import matplotlib  # noqa: E402

matplotlib.use("Agg")  # headless -- no display needed/available
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support  # noqa: E402

from router import ACTIONS, INPUT_COLUMNS, MESSAGE_TYPES, Router  # noqa: E402

DATASET_DIR = os.path.join(REPO_ROOT, "dataset")
SAMPLES_PATH = os.path.join(DATASET_DIR, "sample_messages.csv")
# Hand-crafted held-out cases the rules were never tuned against (see
# dataset/synthetic_test.csv's own generation notes) -- run as a separate report
# section so sample-set accuracy and held-out accuracy are never conflated.
SYNTHETIC_PATH = os.path.join(DATASET_DIR, "synthetic_test.csv")
MESSAGE_HISTORY_PATH = os.path.join(DATASET_DIR, "message_history.csv")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")
SUMMARY_PATH = os.path.join(REPORTS_DIR, "eval_summary.md")

ACTION_LABELS = sorted(ACTIONS)
TYPE_LABELS = sorted(MESSAGE_TYPES)

# Confidence buckets for calibration. The upper bound of the last bucket is 1.01 (not
# 1.0) so a confidence of exactly 1.0 falls inside it under a half-open [lo, hi) test.
CONFIDENCE_BUCKETS = [
    (0.0, 0.5),
    (0.5, 0.6),
    (0.6, 0.7),
    (0.7, 0.8),
    (0.8, 0.9),
    (0.9, 1.01),
]

# $ per million tokens, (input, output). Used only to print an estimated cost for the
# run; a model not listed here still gets its token counts printed, just no $ figure.
MODEL_PRICING_PER_MTOK = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-opus-4-7": (5.00, 25.00),
    "claude-opus-4-6": (5.00, 25.00),
    "claude-fable-5": (10.00, 50.00),
    "claude-mythos-5": (10.00, 50.00),
}


def _positive_int(value: str) -> int:
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError(f"--limit must be a positive integer, got {value!r}")
    return n


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the router against sample_messages.csv")
    parser.add_argument(
        "--limit",
        type=_positive_int,
        default=None,
        help="Only evaluate the first N rows of sample_messages.csv, for fast iteration "
        "on rubric changes instead of the full 30-message set.",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# 0. Run the pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    limit: Optional[int] = None, path: str = SAMPLES_PATH
) -> tuple[pd.DataFrame, bool, dict[str, Any], str]:
    """Runs Router.route() over rows from `path` (sample_messages.csv by default, or
    just the first `limit` of them). Returns a DataFrame with expected + predicted
    columns, whether the LLM path was available, the router's cumulative API usage
    stats, and the model used."""
    router = Router(dataset_dir=DATASET_DIR)
    samples = pd.read_csv(path)
    if limit is not None:
        samples = samples.head(limit)

    rows = []
    for _, row in samples.iterrows():
        input_row = row[INPUT_COLUMNS]
        predicted = router.route(input_row)
        rows.append(
            {
                "message_id": row.message_id,
                "expected_action": row.action,
                "predicted_action": predicted["action"],
                "expected_message_type": row.message_type,
                "predicted_message_type": predicted["message_type"],
                "expected_evidence": row.evidence_message_ids,
                "predicted_evidence": predicted["evidence_message_ids"],
                "confidence": float(predicted["confidence"]),
                "source": predicted.get("_source", "?"),
            }
        )
    return pd.DataFrame(rows), router.llm_available, router.usage_stats, router.model


# ---------------------------------------------------------------------------
# 1. Accuracy
# ---------------------------------------------------------------------------

def accuracy(df: pd.DataFrame, expected_col: str, predicted_col: str) -> float:
    return float((df[expected_col] == df[predicted_col]).mean())


# ---------------------------------------------------------------------------
# 2. Confusion matrices
# ---------------------------------------------------------------------------

def confusion(df: pd.DataFrame, expected_col: str, predicted_col: str, labels: list[str]) -> np.ndarray:
    return confusion_matrix(df[expected_col], df[predicted_col], labels=labels)


def format_confusion_table(cm: np.ndarray, labels: list[str]) -> str:
    col_width = max(6, max(len(l) for l in labels) + 1)
    header = "expected \\ predicted".ljust(20) + "".join(l[: col_width - 1].rjust(col_width) for l in labels)
    lines = [header]
    for i, label in enumerate(labels):
        row = label.ljust(20) + "".join(str(cm[i, j]).rjust(col_width) for j in range(len(labels)))
        lines.append(row)
    return "\n".join(lines)


def save_confusion_heatmap(cm: np.ndarray, labels: list[str], title: str, path: str) -> None:
    n = len(labels)
    fig, ax = plt.subplots(figsize=(max(6.0, n * 0.9), max(5.0, n * 0.8)))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Expected")
    ax.set_title(title)
    vmax = cm.max() if cm.max() > 0 else 1
    for i in range(n):
        for j in range(n):
            value = cm[i, j]
            color = "white" if value > vmax / 2 else "black"
            ax.text(j, i, str(value), ha="center", va="center", color=color, fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Per-class precision / recall / F1
# ---------------------------------------------------------------------------

def per_class_metrics(df: pd.DataFrame, expected_col: str, predicted_col: str, labels: list[str]) -> pd.DataFrame:
    precision, recall, f1, support = precision_recall_fscore_support(
        df[expected_col], df[predicted_col], labels=labels, zero_division=0
    )
    return pd.DataFrame(
        {"label": labels, "precision": precision, "recall": recall, "f1": f1, "support": support}
    )


def format_metrics_table(metrics_df: pd.DataFrame) -> str:
    lines = [f"{'label':<18}{'precision':>10}{'recall':>10}{'f1':>10}{'support':>9}"]
    for _, r in metrics_df.iterrows():
        lines.append(
            f"{r.label:<18}{r.precision:>10.2f}{r.recall:>10.2f}{r.f1:>10.2f}{int(r.support):>9d}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Confidence calibration
# ---------------------------------------------------------------------------

def calibration_table(df: pd.DataFrame, correct_mask: pd.Series) -> tuple[pd.DataFrame, float]:
    """Buckets rows by confidence and reports empirical accuracy per bucket, plus the
    Expected Calibration Error (ECE): the support-weighted average gap between mean
    predicted confidence and empirical accuracy across buckets."""
    working = df.assign(_correct=correct_mask.astype(float))
    rows = []
    for lo, hi in CONFIDENCE_BUCKETS:
        bucket = working[(working.confidence >= lo) & (working.confidence < hi)]
        n = len(bucket)
        if n == 0:
            continue
        acc = bucket["_correct"].mean()
        mean_conf = bucket.confidence.mean()
        label = f"[{lo:.1f}-{min(hi, 1.0):.1f})"
        rows.append({"bucket": label, "n": n, "mean_confidence": mean_conf, "accuracy": acc, "gap": abs(mean_conf - acc)})
    table = pd.DataFrame(rows)
    n_total = len(df)
    ece = float((table["n"] * table["gap"]).sum() / n_total) if len(table) and n_total else float("nan")
    return table, ece


def format_calibration_table(table: pd.DataFrame, ece: float) -> str:
    if table.empty:
        return "(no predictions to bucket)"
    lines = [f"{'bucket':<12}{'n':>5}{'mean_confidence':>18}{'accuracy':>10}{'gap':>8}"]
    for _, r in table.iterrows():
        lines.append(f"{r.bucket:<12}{int(r.n):>5}{r.mean_confidence:>18.3f}{r.accuracy:>10.3f}{r.gap:>8.3f}")
    lines.append(f"\nExpected Calibration Error (ECE): {ece:.4f}")
    return "\n".join(lines)


def save_reliability_diagram(table: pd.DataFrame, ece: float, title: str, path: str) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 6))
    if table.empty:
        ax.text(0.5, 0.5, "no predictions to bucket", ha="center", va="center")
    else:
        x = np.arange(len(table))
        width = 0.35
        ax.bar(x - width / 2, table["mean_confidence"], width, label="mean confidence", color="#4C72B0")
        ax.bar(x + width / 2, table["accuracy"], width, label="empirical accuracy", color="#DD8452")
        ax.set_xticks(x)
        ax.set_xticklabels(table["bucket"], rotation=20, ha="right")
        ax.legend()
    ax.set_ylim(0, 1)
    ax.set_ylabel("value")
    ax.set_title(f"{title}\nExpected Calibration Error = {ece:.3f}")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5. Evidence quality
# ---------------------------------------------------------------------------

def evidence_quality(df: pd.DataFrame, history_ids: set[str]) -> dict[str, Any]:
    n = len(df)
    cites_evidence = df["predicted_evidence"] != "none"
    pct_citing = float(cites_evidence.mean())

    total_ids = 0
    total_valid = 0
    for value in df["predicted_evidence"]:
        if value == "none" or pd.isna(value):
            continue
        ids = value.split(";")
        total_ids += len(ids)
        total_valid += sum(1 for eid in ids if eid in history_ids)
    pct_valid = (total_valid / total_ids) if total_ids else float("nan")

    has_expected = df["expected_evidence"] != "none"
    overlap_rows = df[has_expected]
    overlaps = []
    exact_matches = 0
    for _, row in overlap_rows.iterrows():
        expected_set = set(row["expected_evidence"].split(";"))
        predicted_set = (
            set(row["predicted_evidence"].split(";")) if row["predicted_evidence"] != "none" else set()
        )
        if expected_set:
            overlaps.append(len(expected_set & predicted_set) / len(expected_set))
        if expected_set == predicted_set:
            exact_matches += 1

    return {
        "n_total": n,
        "pct_citing_evidence": pct_citing,
        "total_cited_ids": total_ids,
        "pct_cited_ids_valid": pct_valid,
        "n_rows_with_expected_evidence": len(overlap_rows),
        "mean_overlap_with_expected": float(np.mean(overlaps)) if overlaps else float("nan"),
        "exact_match_rate_with_expected": (exact_matches / len(overlap_rows)) if len(overlap_rows) else float("nan"),
    }


def format_evidence_stats(stats: dict[str, Any]) -> str:
    return (
        f"  Rows citing at least one evidence ID: {stats['pct_citing_evidence']:.1%} ({stats['n_total']} total rows)\n"
        f"  Cited IDs that exist in message_history.csv: {stats['pct_cited_ids_valid']:.1%} "
        f"({stats['total_cited_ids']} IDs cited total)\n"
        f"  Rows where the sample provides its own expected evidence: {stats['n_rows_with_expected_evidence']}\n"
        f"  Mean overlap with that expected evidence (|predicted ∩ expected| / |expected|): "
        f"{stats['mean_overlap_with_expected']:.1%}\n"
        f"  Exact-match rate with that expected evidence set: {stats['exact_match_rate_with_expected']:.1%}"
    )


# ---------------------------------------------------------------------------
# 5b. Synthetic (held-out) set
# ---------------------------------------------------------------------------

def format_synthetic_report(df: pd.DataFrame) -> str:
    """Text report for the held-out synthetic set: overall accuracy, confusion
    tables, and a full per-row pass/fail list (the most useful view at n=18 --
    calibration buckets and heatmap PNGs aren't meaningful at this sample size)."""
    n = len(df)
    action_acc = accuracy(df, "expected_action", "predicted_action")
    type_acc = accuracy(df, "expected_message_type", "predicted_message_type")
    full_correct = (df.expected_action == df.predicted_action) & (
        df.expected_message_type == df.predicted_message_type
    )

    lines = [
        f"n = {n} hand-crafted, held-out cases (never used to tune the rules)",
        f"action accuracy:       {action_acc:.1%}  ({int(round(action_acc * n))}/{n})",
        f"message_type accuracy: {type_acc:.1%}  ({int(round(type_acc * n))}/{n})",
        f"fully correct (both):  {full_correct.mean():.1%}  ({int(full_correct.sum())}/{n})",
        "",
        "--- confusion matrix: action ---",
        format_confusion_table(confusion(df, "expected_action", "predicted_action", ACTION_LABELS), ACTION_LABELS),
        "",
        "--- confusion matrix: message_type ---",
        format_confusion_table(
            confusion(df, "expected_message_type", "predicted_message_type", TYPE_LABELS), TYPE_LABELS
        ),
        "",
        "--- per-row results ---",
    ]
    for _, r in df.iterrows():
        a_mark = "OK  " if r.expected_action == r.predicted_action else "MISS"
        t_mark = "OK  " if r.expected_message_type == r.predicted_message_type else "MISS"
        lines.append(
            f"{r.message_id:12s}  action[{a_mark}] pred={r.predicted_action:7s} exp={r.expected_action:7s}"
            f"  type[{t_mark}] pred={r.predicted_message_type:16s} exp={r.expected_message_type:16s}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6. API usage / cost
# ---------------------------------------------------------------------------

def format_usage_stats(usage_stats: dict[str, Any], model: str) -> str:
    calls = usage_stats.get("api_calls", 0)
    hits = usage_stats.get("cache_hits", 0)
    misses = usage_stats.get("cache_misses", 0)
    input_tok = usage_stats.get("input_tokens", 0)
    output_tok = usage_stats.get("output_tokens", 0)
    cache_read = usage_stats.get("cache_read_input_tokens", 0)
    cache_creation = usage_stats.get("cache_creation_input_tokens", 0)

    lines = [
        f"  Model: {model}",
        f"  Response cache: {hits} hit(s), {misses} miss(es) -- keyed on (message_id, hash "
        "of prompt content), so unchanged messages don't re-call the API on rerun",
        f"  API calls made this run: {calls}",
        f"  Input tokens:  {input_tok:,}  (+{cache_creation:,} prompt-cache-write, "
        f"{cache_read:,} prompt-cache-read)",
        f"  Output tokens: {output_tok:,}",
    ]
    pricing = MODEL_PRICING_PER_MTOK.get(model)
    if calls == 0:
        lines.append("  Estimated cost this run: $0.00 (no API calls -- all cached or rule-based)")
    elif pricing:
        in_price, out_price = pricing
        cost = (input_tok / 1_000_000) * in_price + (output_tok / 1_000_000) * out_price
        lines.append(
            f"  Estimated cost this run: ${cost:.4f}  (at ${in_price:.2f}/${out_price:.2f} per MTok in/out)"
        )
    else:
        lines.append(f"  Estimated cost: unknown -- no pricing on file for model {model!r}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    os.makedirs(REPORTS_DIR, exist_ok=True)
    run_started = datetime.now()
    ts = run_started.strftime("%Y%m%d_%H%M%S")
    ts_human = run_started.strftime("%Y-%m-%d %H:%M:%S")

    limit_note = ""
    if args.limit is not None:
        total_samples = len(pd.read_csv(SAMPLES_PATH, usecols=["message_id"]))
        limit_note = f" (limited to first {min(args.limit, total_samples)} of {total_samples})"

    print(f"Running evaluation against {os.path.relpath(SAMPLES_PATH, REPO_ROOT)}{limit_note} ...")
    df, llm_available, usage_stats, model = run_pipeline(limit=args.limit)
    print(f"LLM available (ANTHROPIC_API_KEY set): {llm_available}")
    if not llm_available:
        print("-> every prediction comes from the deterministic rule-based fallback.")

    history_ids = set(pd.read_csv(MESSAGE_HISTORY_PATH, dtype=str).message_id)

    # 1. accuracy
    action_acc = accuracy(df, "expected_action", "predicted_action")
    type_acc = accuracy(df, "expected_message_type", "predicted_message_type")

    # 2. confusion matrices
    action_cm = confusion(df, "expected_action", "predicted_action", ACTION_LABELS)
    type_cm = confusion(df, "expected_message_type", "predicted_message_type", TYPE_LABELS)
    action_cm_text = format_confusion_table(action_cm, ACTION_LABELS)
    type_cm_text = format_confusion_table(type_cm, TYPE_LABELS)

    action_png_ts = os.path.join(REPORTS_DIR, f"confusion_action_{ts}.png")
    action_png_latest = os.path.join(REPORTS_DIR, "confusion_action_latest.png")
    type_png_ts = os.path.join(REPORTS_DIR, f"confusion_message_type_{ts}.png")
    type_png_latest = os.path.join(REPORTS_DIR, "confusion_message_type_latest.png")
    save_confusion_heatmap(action_cm, ACTION_LABELS, "action: expected vs predicted", action_png_ts)
    save_confusion_heatmap(action_cm, ACTION_LABELS, "action: expected vs predicted", action_png_latest)
    save_confusion_heatmap(type_cm, TYPE_LABELS, "message_type: expected vs predicted", type_png_ts)
    save_confusion_heatmap(type_cm, TYPE_LABELS, "message_type: expected vs predicted", type_png_latest)

    # 3. per-class precision/recall/F1
    action_metrics = per_class_metrics(df, "expected_action", "predicted_action", ACTION_LABELS)
    type_metrics = per_class_metrics(df, "expected_message_type", "predicted_message_type", TYPE_LABELS)

    # 4. confidence calibration -- computed against action-correctness (the field the
    # confidence most directly governs -- it decides whether the user gets interrupted)
    # and reported a second time against full-row correctness (action AND message_type
    # both right) for a stricter view.
    action_correct = df["expected_action"] == df["predicted_action"]
    full_correct = action_correct & (df["expected_message_type"] == df["predicted_message_type"])

    action_calib_table, action_ece = calibration_table(df, action_correct)
    full_calib_table, full_ece = calibration_table(df, full_correct)

    reliability_png_ts = os.path.join(REPORTS_DIR, f"reliability_diagram_{ts}.png")
    reliability_png_latest = os.path.join(REPORTS_DIR, "reliability_diagram_latest.png")
    save_reliability_diagram(action_calib_table, action_ece, "Calibration vs action correctness", reliability_png_ts)
    save_reliability_diagram(action_calib_table, action_ece, "Calibration vs action correctness", reliability_png_latest)

    # 5. evidence quality
    ev_stats = evidence_quality(df, history_ids)

    # ---- print to terminal ----
    print(f"\n{'='*70}\nEVALUATION RESULTS  ({ts_human})\n{'='*70}")
    print(f"\naction accuracy:       {action_acc:.1%}  ({int(action_acc*len(df))}/{len(df)})")
    print(f"message_type accuracy: {type_acc:.1%}  ({int(type_acc*len(df))}/{len(df)})")

    print("\n--- confusion matrix: action ---")
    print(action_cm_text)
    print("\n--- confusion matrix: message_type ---")
    print(type_cm_text)

    print("\n--- per-class metrics: action ---")
    print(format_metrics_table(action_metrics))
    print("\n--- per-class metrics: message_type ---")
    print(format_metrics_table(type_metrics))

    print("\n--- confidence calibration (vs action correctness) ---")
    print(format_calibration_table(action_calib_table, action_ece))
    print("\n--- confidence calibration (vs full-row correctness: action AND message_type) ---")
    print(format_calibration_table(full_calib_table, full_ece))

    print("\n--- evidence quality ---")
    print(format_evidence_stats(ev_stats))

    print("\n--- API usage & estimated cost (this run) ---")
    print(format_usage_stats(usage_stats, model))

    # ---- synthetic (held-out) set: a separate report section, never mixed into the
    # sample_messages.csv numbers above ----
    synthetic_report = None
    if os.path.exists(SYNTHETIC_PATH):
        print(f"\n{'='*70}\nSYNTHETIC (HELD-OUT)\n{'='*70}")
        synth_df, _, _, _ = run_pipeline(path=SYNTHETIC_PATH)
        synthetic_report = format_synthetic_report(synth_df)
        print(synthetic_report)

    print(f"\nSaved PNGs to {os.path.relpath(REPORTS_DIR, REPO_ROOT)}/:")
    for p in [action_png_ts, type_png_ts, reliability_png_ts]:
        print(f"  {os.path.relpath(p, REPO_ROOT)}")
    print("(plus '_latest' copies of each)")

    # ---- append to reports/eval_summary.md ----
    summary = _render_markdown_summary(
        ts_human=ts_human,
        llm_available=llm_available,
        n=len(df),
        action_acc=action_acc,
        type_acc=type_acc,
        action_cm_text=action_cm_text,
        type_cm_text=type_cm_text,
        action_metrics=action_metrics,
        type_metrics=type_metrics,
        action_calib_table=action_calib_table,
        action_ece=action_ece,
        full_calib_table=full_calib_table,
        full_ece=full_ece,
        ev_stats=ev_stats,
        png_paths={
            "action": os.path.relpath(action_png_ts, REPO_ROOT).replace(os.sep, "/"),
            "type": os.path.relpath(type_png_ts, REPO_ROOT).replace(os.sep, "/"),
            "reliability": os.path.relpath(reliability_png_ts, REPO_ROOT).replace(os.sep, "/"),
        },
        synthetic_report=synthetic_report,
    )
    is_new = not os.path.exists(SUMMARY_PATH)
    with open(SUMMARY_PATH, "a", encoding="utf-8") as f:
        if is_new:
            f.write("# Evaluation Summary\n\nRunning log of `python -m src.eval` runs against "
                     "`dataset/sample_messages.csv`, newest last.\n\n")
        f.write(summary)
    print(f"\nAppended run summary to {os.path.relpath(SUMMARY_PATH, REPO_ROOT)}")


def _render_markdown_summary(
    *,
    ts_human: str,
    llm_available: bool,
    n: int,
    action_acc: float,
    type_acc: float,
    action_cm_text: str,
    type_cm_text: str,
    action_metrics: pd.DataFrame,
    type_metrics: pd.DataFrame,
    action_calib_table: pd.DataFrame,
    action_ece: float,
    full_calib_table: pd.DataFrame,
    full_ece: float,
    ev_stats: dict[str, Any],
    png_paths: dict[str, str],
    synthetic_report: Optional[str] = None,
) -> str:
    def metrics_md(df: pd.DataFrame) -> str:
        lines = ["| label | precision | recall | f1 | support |", "|---|---|---|---|---|"]
        for _, r in df.iterrows():
            lines.append(f"| {r.label} | {r.precision:.2f} | {r.recall:.2f} | {r.f1:.2f} | {int(r.support)} |")
        return "\n".join(lines)

    def calib_md(df: pd.DataFrame, ece: float) -> str:
        if df.empty:
            return "(no predictions to bucket)"
        lines = ["| bucket | n | mean confidence | accuracy | gap |", "|---|---|---|---|---|"]
        for _, r in df.iterrows():
            lines.append(f"| {r.bucket} | {int(r.n)} | {r.mean_confidence:.3f} | {r.accuracy:.3f} | {r.gap:.3f} |")
        lines.append(f"\n**Expected Calibration Error (ECE): {ece:.4f}**")
        return "\n".join(lines)

    source_note = (
        "LLM path (ANTHROPIC_API_KEY set)" if llm_available else "rule-based fallback only (no ANTHROPIC_API_KEY)"
    )

    synthetic_md = (
        f"\n### Synthetic (held-out)\n\n```\n{synthetic_report}\n```\n" if synthetic_report else ""
    )

    return f"""
## Run {ts_human}

Source: {source_note} — {n} messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **{action_acc:.1%}**
- message_type: **{type_acc:.1%}**

### Confusion matrix: action

```
{action_cm_text}
```

![action confusion matrix]({png_paths['action']})

### Confusion matrix: message_type

```
{type_cm_text}
```

![message_type confusion matrix]({png_paths['type']})

### Per-class metrics: action

{metrics_md(action_metrics)}

### Per-class metrics: message_type

{metrics_md(type_metrics)}

### Confidence calibration (vs action correctness)

{calib_md(action_calib_table, action_ece)}

![reliability diagram]({png_paths['reliability']})

### Confidence calibration (vs full-row correctness: action AND message_type)

{calib_md(full_calib_table, full_ece)}

### Evidence quality

- Rows citing at least one evidence ID: {ev_stats['pct_citing_evidence']:.1%} ({ev_stats['n_total']} total rows)
- Cited IDs that exist in `message_history.csv`: {ev_stats['pct_cited_ids_valid']:.1%} ({ev_stats['total_cited_ids']} IDs cited total)
- Rows where the sample provides its own expected evidence: {ev_stats['n_rows_with_expected_evidence']}
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): {ev_stats['mean_overlap_with_expected']:.1%}
- Exact-match rate with that expected evidence set: {ev_stats['exact_match_rate_with_expected']:.1%}
{synthetic_md}
---
"""


if __name__ == "__main__":
    main()
