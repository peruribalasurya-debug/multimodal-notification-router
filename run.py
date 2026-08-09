#!/usr/bin/env python
"""run.py -- single terminal entry point for the Message Notification Router.

Usage:
    python run.py                 # process every message, resuming from checkpoint
    python run.py --force         # ignore the checkpoint, reprocess everything
    python run.py --limit 10      # debugging: only process the first 10 messages

Runs dataset/messages.csv through the full pipeline (src/context.py stage 1,
src/media.py stage 2, src/router.py stage 3/4), writes dataset/output.csv, then
validates the result against the output contract and prints an action /
message_type distribution so a degenerate run (e.g. everything "notify") is
obvious immediately rather than discovered later, after the output has already been relied on.

Resumable: each completed message is appended to a checkpoint file as soon as
it's done, so an interrupted run (crash, Ctrl-C, hitting a time limit) picks up
exactly where it left off on the next invocation instead of reprocessing
already-done messages or re-spending API budget on them.

Reads ANTHROPIC_API_KEY from the environment only (never hardcoded) -- see
src/router.py. If it's unset, every message routes through the deterministic
rule-based fallback instead of the LLM; the run still completes and produces a
valid output.csv.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)

import pandas as pd  # noqa: E402

from router import ACTIONS, MESSAGE_TYPES, Router  # noqa: E402

DATASET_DIR = os.path.join(REPO_ROOT, "dataset")
MESSAGES_PATH = os.path.join(DATASET_DIR, "messages.csv")
MESSAGE_HISTORY_PATH = os.path.join(DATASET_DIR, "message_history.csv")
OUTPUT_PATH = os.path.join(DATASET_DIR, "output.csv")
CHECKPOINT_PATH = os.path.join(SRC_DIR, ".cache", "run_checkpoint.jsonl")

OUTPUT_COLUMNS = ["message_id", "action", "message_type", "reason", "confidence", "evidence_message_ids"]


def _log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


# ---------------------------------------------------------------------------
# Checkpointing (resumability)
# ---------------------------------------------------------------------------

def _load_checkpoint() -> dict[str, dict]:
    done: dict[str, dict] = {}
    if not os.path.exists(CHECKPOINT_PATH):
        return done
    with open(CHECKPOINT_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # a partially-flushed last line from a crash mid-write -- skip it
            done[row["message_id"]] = row
    return done


def _append_checkpoint(row: dict) -> None:
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    with open(CHECKPOINT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())  # survive a crash immediately after this message completes


# ---------------------------------------------------------------------------
# Processing loop
# ---------------------------------------------------------------------------

_SAFE_DEFAULT_REASON = "Routing failed unexpectedly; defaulted to a safe low-risk action."


def process_all(force: bool = False, limit: int | None = None) -> list[dict]:
    messages = pd.read_csv(MESSAGES_PATH)
    if limit:
        messages = messages.head(limit)
    total = len(messages)

    done = {} if force else _load_checkpoint()
    if done:
        already = sum(1 for mid in messages.message_id if mid in done)
        _log(f"Resuming: {already} of {total} messages already checkpointed, skipping those.")

    router = Router(dataset_dir=DATASET_DIR)
    _log(f"LLM available (ANTHROPIC_API_KEY set): {router.llm_available}")
    if not router.llm_available:
        _log("-> routing every message through the deterministic rule-based fallback.")

    results: list[dict] = []
    for i, (_, row) in enumerate(messages.iterrows(), start=1):
        message_id = row.message_id

        if message_id in done:
            results.append(done[message_id])
            continue

        started = time.monotonic()
        try:
            predicted = router.route(row)
        except Exception as exc:
            # A failure anywhere in the pipeline (not just the LLM call, which
            # router.route already isolates and falls back from internally) must
            # still yield one valid row -- never let a single bad message drop the
            # "one row per message_id" contract for the whole run.
            _log(f"[{i}/{total}] {message_id}: unhandled error ({exc!r}) -- using safe default")
            predicted = {
                "action": "digest",
                "message_type": "unknown",
                "reason": _SAFE_DEFAULT_REASON,
                "confidence": 0.5,
                "evidence_message_ids": "none",
                "_source": "error_default",
            }
        elapsed = time.monotonic() - started

        record = {
            "message_id": message_id,
            "action": predicted["action"],
            "message_type": predicted["message_type"],
            "reason": predicted["reason"],
            "confidence": predicted["confidence"],
            "evidence_message_ids": predicted["evidence_message_ids"],
        }
        _append_checkpoint(record)
        results.append(record)

        source = predicted.get("_source", "?")
        _log(
            f"[{i}/{total}] {message_id} -> {record['action']}/{record['message_type']}"
            f" (conf={record['confidence']:.2f}, source={source}, {elapsed:.1f}s)"
        )

    return results


def write_output_csv(results: list[dict]) -> None:
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in results:
            writer.writerow({k: row[k] for k in OUTPUT_COLUMNS})
    _log(f"Wrote {len(results)} rows to {OUTPUT_PATH}")


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate_output() -> list[str]:
    """Checks output.csv against the hard contract. Returns a list of error strings
    (empty means valid)."""
    errors: list[str] = []

    if not os.path.exists(OUTPUT_PATH):
        return [f"{OUTPUT_PATH} does not exist"]

    with open(OUTPUT_PATH, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f), None)
    if header != OUTPUT_COLUMNS:
        errors.append(f"column mismatch: expected {OUTPUT_COLUMNS}, got {header}")

    output_df = pd.read_csv(OUTPUT_PATH, dtype=str)
    messages_df = pd.read_csv(MESSAGES_PATH, dtype=str)
    history_ids = set(pd.read_csv(MESSAGE_HISTORY_PATH, dtype=str).message_id)

    expected_ids = set(messages_df.message_id)
    actual_ids = list(output_df.message_id)
    actual_id_set = set(actual_ids)

    if len(actual_ids) != len(actual_id_set):
        dupes = sorted({mid for mid, count in Counter(actual_ids).items() if count > 1})
        errors.append(f"{len(dupes)} duplicate message_id(s): {dupes[:10]}")

    missing = expected_ids - actual_id_set
    if missing:
        errors.append(
            f"{len(missing)} message_id(s) from messages.csv missing in output.csv: {sorted(missing)[:10]}"
        )

    extra = actual_id_set - expected_ids
    if extra:
        errors.append(f"{len(extra)} message_id(s) in output.csv not present in messages.csv: {sorted(extra)[:10]}")

    if len(output_df) != len(messages_df):
        errors.append(f"row count mismatch: output.csv has {len(output_df)}, messages.csv has {len(messages_df)}")

    bad_actions = output_df[~output_df.action.isin(ACTIONS)]
    if len(bad_actions):
        errors.append(
            f"{len(bad_actions)} row(s) with invalid action value: {sorted(bad_actions.action.unique().tolist())}"
        )

    bad_types = output_df[~output_df.message_type.isin(MESSAGE_TYPES)]
    if len(bad_types):
        errors.append(
            f"{len(bad_types)} row(s) with invalid message_type value: {sorted(bad_types.message_type.unique().tolist())}"
        )

    def _confidence_invalid(value: str) -> bool:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return True
        return not (0.0 <= parsed <= 1.0)

    bad_confidence = output_df[output_df.confidence.apply(_confidence_invalid)]
    if len(bad_confidence):
        errors.append(
            f"{len(bad_confidence)} row(s) with confidence outside [0,1] or non-numeric: "
            f"{bad_confidence.message_id.tolist()[:10]}"
        )

    def _invalid_evidence_ids(value: str) -> list[str]:
        if pd.isna(value) or value == "none":
            return []
        return [eid for eid in value.split(";") if eid not in history_ids]

    output_df = output_df.assign(_bad_evidence=output_df.evidence_message_ids.apply(_invalid_evidence_ids))
    bad_evidence_rows = output_df[output_df["_bad_evidence"].apply(len) > 0]
    if len(bad_evidence_rows):
        examples = [
            (r.message_id, r["_bad_evidence"]) for _, r in bad_evidence_rows.head(10).iterrows()
        ]
        errors.append(
            f"{len(bad_evidence_rows)} row(s) reference evidence_message_ids not found in "
            f"message_history.csv: {examples}"
        )

    return errors


def print_distribution() -> None:
    output_df = pd.read_csv(OUTPUT_PATH, dtype=str)
    n = len(output_df)

    print("\n=== action distribution ===")
    for value, count in output_df.action.value_counts().items():
        print(f"  {value:10s} {count:4d}  ({count / n:.1%})")

    print("\n=== message_type distribution ===")
    for value, count in output_df.message_type.value_counts().items():
        print(f"  {value:16s} {count:4d}  ({count / n:.1%})")

    n_actions = output_df.action.nunique()
    n_types = output_df.message_type.nunique()
    if n_actions <= 1:
        print(f"\n  WARNING: only {n_actions} distinct action value used across {n} messages -- looks degenerate.")
    if n_types <= 1:
        print(f"  WARNING: only {n_types} distinct message_type value used across {n} messages -- looks degenerate.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the message notification router over dataset/messages.csv")
    parser.add_argument("--limit", type=int, default=None, help="only process the first N messages (debugging)")
    parser.add_argument("--force", action="store_true", help="ignore the checkpoint and reprocess every message")
    args = parser.parse_args()

    _log("Starting run.")
    results = process_all(force=args.force, limit=args.limit)
    write_output_csv(results)

    _log("Validating output.csv against the output contract ...")
    errors = validate_output()
    if errors:
        print("\n=== VALIDATION FAILED ===")
        for e in errors:
            print(f"  - {e}")
    else:
        print("\n=== VALIDATION PASSED ===")
        print(f"  {os.path.relpath(OUTPUT_PATH, REPO_ROOT)} has the exact contract columns in order,")
        print("  one row per message_id with no duplicates or missing IDs, action/message_type only use")
        print("  allowed values, confidence is numeric in [0,1], and every evidence_message_ids value is")
        print("  'none' or IDs that exist in message_history.csv.")

    print_distribution()

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
