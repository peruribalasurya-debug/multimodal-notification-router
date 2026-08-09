"""Tier 2 of the classification cascade: a lightweight, free, local classifier
trained to approximate the LLM's routing decisions (action, message_type) from
the same message text, extracted media text, and structured context signals
the LLM sees.

Training labels come entirely from dataset/messages_llm_labeled_full.csv
(produced once by actually running the LLM path over dataset/messages.csv --
see that file's `label_source` column). This module makes no API calls of its
own: it trains offline from that CSV, and only rows with label_source=="llm"
are used -- the 7 rows that fell back to the deterministic rule-based fallback
are excluded, so tier 2 is distilling genuine LLM judgment, not re-deriving
tier 1's own rules.

With ~103 usable rows across 11 message_type classes, several classes have too
few examples for a trustworthy 5-fold stratified CV estimate (sklearn's
StratifiedKFold requires >= n_splits members per class to run at all). Rather
than silently drop them or let the CV crash, classes below MIN_CLASS_SIZE_FOR_CV
are excluded from the CV *evaluation* (reported separately, flagged low-
confidence) but still included when fitting the final production model, so the
classifier can still predict them -- just without a trustworthy accuracy number
attached.

CLI:
    python -m src.cheap_classifier
"""

from __future__ import annotations

import os
import sys
import warnings
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SRC_DIR)
DATASET_DIR = os.path.join(REPO_ROOT, "dataset")
LABELED_PATH = os.path.join(DATASET_DIR, "messages_llm_labeled_full.csv")

MIN_CLASS_SIZE_FOR_CV = 5
N_SPLITS = 5
RANDOM_STATE = 42

# -- feature schema, matching messages_llm_labeled_full.csv's raw feature columns --

TEXT_SOURCE_COLUMNS = [
    "message_text", "media_ocr_text", "media_visual_description", "media_transcript",
]
NUMERIC_COLUMNS = [
    "forwarded_count", "sender_verified", "sender_domain_match", "business_account_age_days",
    "business_user_reports_30d", "is_admin_sender", "group_muted_by_recipient",
    "group_recipient_dismissed_30d", "relationship_activity_count_180d",
    "relationship_allows_promotions", "relationship_opted_out_promotions",
    "relationship_messages_opened_30d", "relationship_messages_dismissed_30d",
    "relationship_messages_replied_30d", "recipient_messages_opened_30d",
    "recipient_messages_replied_30d", "recipient_notifications_dismissed_30d",
    "recipient_messages_reported_30d", "evidence_count", "evidence_negative_count",
    "evidence_positive_count",
]
CATEGORICAL_COLUMNS = ["conversation_type", "media_type"]


def extract_context_features(row: Any, ctx: dict[str, Any], media_result: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Builds the same raw feature dict for a single message that was used to
    generate dataset/messages_llm_labeled_full.csv (see
    scripts/label_full_dataset.py at generation time) -- the single source of
    truth for the feature schema, reused at both training-data-generation time
    and live cascade-inference time so the two can never silently drift apart.

    `row` is a message row (message_id, message_text, media_type, ... -- the
    INPUT_COLUMNS shape from router.py). `ctx` is
    ContextAssembler.build_context_for_row(row)'s output. `media_result` is
    MediaExtractor.extract_for_message(row)'s output.
    """
    business_ctx = ctx.get("business_context") or {}
    business = business_ctx.get("business") or {}
    relationship = business_ctx.get("relationship")
    group_ctx = ctx.get("group_context") or {}
    membership = group_ctx.get("membership") or {}
    sender_membership = group_ctx.get("sender_membership") or {}
    recipient_profile = (ctx.get("recipient") or {}).get("profile") or {}
    extraction = (media_result or {}).get("extraction") or {}
    evidence = ctx.get("evidence") or []

    evidence_negative = sum(
        1 for e in evidence
        if (e.get("reaction") or {}).get("notification_dismissed") == 1
        or (e.get("reaction") or {}).get("muted_after_message") == 1
        or (e.get("reaction") or {}).get("message_reported") == 1
    )
    evidence_positive = sum(1 for e in evidence if (e.get("reaction") or {}).get("message_opened") == 1)

    is_business = business_ctx.get("business") is not None
    is_group = group_ctx.get("group") is not None

    return {
        "message_text": row.get("message_text"),
        "media_type": row.get("media_type"),
        "media_ocr_text": extraction.get("ocr_text"),
        "media_visual_description": extraction.get("visual_description"),
        "media_transcript": extraction.get("transcript"),
        "conversation_type": row.get("conversation_type"),
        "forwarded_count": row.get("forwarded_count"),
        "sender_verified": business.get("verified") if is_business else None,
        "sender_domain_match": (
            int(business.get("official_domain") == business.get("domain_used_by_sender")) if is_business else None
        ),
        "business_account_age_days": business.get("account_age_days") if is_business else None,
        "business_user_reports_30d": business.get("user_reports_30d") if is_business else None,
        "is_admin_sender": (
            int(sender_membership.get("role") == "admin") if is_group and sender_membership else None
        ),
        "group_muted_by_recipient": membership.get("group_muted_by_user") if is_group else None,
        "group_recipient_dismissed_30d": membership.get("notifications_dismissed_30d") if is_group else None,
        "relationship_why_known": relationship.get("why_user_knows_account") if relationship else None,
        "relationship_activity_count_180d": relationship.get("activity_count_180d") if relationship else None,
        "relationship_allows_promotions": relationship.get("allows_promotions") if relationship else None,
        "relationship_opted_out_promotions": (
            int(bool(relationship.get("promotions_opted_out_at"))) if relationship else None
        ),
        "relationship_messages_opened_30d": relationship.get("messages_opened_30d") if relationship else None,
        "relationship_messages_dismissed_30d": relationship.get("messages_dismissed_30d") if relationship else None,
        "relationship_messages_replied_30d": relationship.get("messages_replied_30d") if relationship else None,
        "recipient_messages_opened_30d": recipient_profile.get("messages_opened_30d"),
        "recipient_messages_replied_30d": recipient_profile.get("messages_replied_30d"),
        "recipient_notifications_dismissed_30d": recipient_profile.get("notifications_dismissed_30d"),
        "recipient_messages_reported_30d": recipient_profile.get("messages_reported_30d"),
        "evidence_count": len(evidence),
        "evidence_negative_count": evidence_negative,
        "evidence_positive_count": evidence_positive,
    }


def feature_row_to_dataframe(features: dict[str, Any]) -> pd.DataFrame:
    """Wraps a single extract_context_features() dict as the 1-row DataFrame
    CheapClassifier.predict/predict_proba expect. Coerces dtypes to match what
    a CSV round-trip (pd.read_csv) would produce at training time -- a raw
    feature dict from extract_context_features() has Python `None` for
    missing values, which pandas/sklearn's missing-value machinery doesn't
    always treat the same as the np.nan a CSV-loaded DataFrame would have."""
    df = pd.DataFrame([features])
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].where(df[col].notna(), np.nan)
    return df.assign(combined_text=_combined_text(df))


def _combined_text(df: pd.DataFrame) -> pd.Series:
    """message_text + every extracted-media text field, joined -- mirrors
    router.py's own _combined_text so tier 2 sees the same textual signal
    tier 1/the LLM did."""
    parts = df[TEXT_SOURCE_COLUMNS].fillna("")
    return parts.apply(lambda r: " ".join(v for v in r if v), axis=1)


def load_training_data(path: str = LABELED_PATH) -> pd.DataFrame:
    """Loads messages_llm_labeled_full.csv and keeps only genuine LLM-labeled
    rows (label_source == "llm"), printing how many were dropped."""
    df = pd.read_csv(path)
    n_total = len(df)
    df = df[df.label_source == "llm"].reset_index(drop=True)
    n_dropped = n_total - len(df)
    if n_dropped:
        print(
            f"Dropped {n_dropped} rule-fallback row(s) (label_source != 'llm') -- "
            f"training only on the {len(df)} genuine LLM labels."
        )
    return df.assign(combined_text=_combined_text(df))


def _build_feature_transformer() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(max_features=400, ngram_range=(1, 2), min_df=1, stop_words="english"),
                "combined_text",
            ),
            ("numeric", SimpleImputer(strategy="constant", fill_value=-1), NUMERIC_COLUMNS),
            (
                "categorical",
                Pipeline([
                    ("impute", SimpleImputer(strategy="constant", fill_value="missing")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore")),
                ]),
                CATEGORICAL_COLUMNS,
            ),
        ],
    )


def _build_model_pipeline() -> Pipeline:
    return Pipeline([
        ("features", _build_feature_transformer()),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0)),
    ])


class CheapClassifier:
    """Tier-2 classifier: predicts `action` and `message_type` from the same
    raw feature schema as dataset/messages_llm_labeled_full.csv (message text,
    extracted media text, structured context). Two independent pipelines
    (separate TF-IDF + logistic regression each), since the two targets don't
    need to share a decision boundary.
    """

    def __init__(self) -> None:
        self.action_model: Optional[Pipeline] = None
        self.message_type_model: Optional[Pipeline] = None
        self.action_classes_: Optional[list[str]] = None
        self.message_type_classes_: Optional[list[str]] = None

    def fit(self, df: pd.DataFrame) -> "CheapClassifier":
        if "combined_text" not in df.columns:
            df = df.assign(combined_text=_combined_text(df))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ConvergenceWarning)
            self.action_model = _build_model_pipeline().fit(df, df["action"])
            self.message_type_model = _build_model_pipeline().fit(df, df["message_type"])
        self.action_classes_ = list(self.action_model.named_steps["clf"].classes_)
        self.message_type_classes_ = list(self.message_type_model.named_steps["clf"].classes_)
        return self

    def _prep(self, df: pd.DataFrame) -> pd.DataFrame:
        if "combined_text" not in df.columns:
            df = df.assign(combined_text=_combined_text(df))
        return df

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._prep(df)
        return pd.DataFrame({
            "action": self.action_model.predict(df),
            "message_type": self.message_type_model.predict(df),
        })

    def predict_proba(self, df: pd.DataFrame) -> dict[str, dict[str, Any]]:
        """Returns {"action": {"classes": [...], "proba": ndarray[n, n_classes]},
        "message_type": {...}} -- the caller thresholds on whichever target and
        confidence level the cascade needs."""
        df = self._prep(df)
        return {
            "action": {"classes": self.action_classes_, "proba": self.action_model.predict_proba(df)},
            "message_type": {
                "classes": self.message_type_classes_, "proba": self.message_type_model.predict_proba(df),
            },
        }


# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------

def cross_validate_target(
    df: pd.DataFrame, target_col: str, min_class_size: int = MIN_CLASS_SIZE_FOR_CV, n_splits: int = N_SPLITS
) -> dict[str, Any]:
    """Stratified k-fold CV for one target column. Classes with fewer than
    `min_class_size` examples can't support a valid n_splits-fold stratified
    split (sklearn requires >= n_splits members per class) -- they're excluded
    from the CV subset and reported separately as `rare_classes`, rather than
    silently dropped or left to crash the whole run."""
    counts = df[target_col].value_counts()
    rare_classes = counts[counts < min_class_size]
    eligible_classes = counts[counts >= min_class_size].index.tolist()

    df_eligible = df[df[target_col].isin(eligible_classes)].reset_index(drop=True)
    y = df_eligible[target_col]
    classes_sorted = sorted(y.unique())

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    pipeline = _build_model_pipeline()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ConvergenceWarning)
        oof_pred = cross_val_predict(pipeline, df_eligible, y, cv=skf)
        oof_proba = cross_val_predict(pipeline, df_eligible, y, cv=skf, method="predict_proba")

    accuracy = float((y.values == oof_pred).mean())
    precision, recall, f1, support = precision_recall_fscore_support(
        y, oof_pred, labels=classes_sorted, zero_division=0
    )
    per_class = pd.DataFrame(
        {"label": classes_sorted, "precision": precision, "recall": recall, "f1": f1, "support": support}
    )

    return {
        "target": target_col,
        "n_used": len(df_eligible),
        "n_excluded_rare": len(df) - len(df_eligible),
        "rare_classes": rare_classes.to_dict(),
        "accuracy": accuracy,
        "per_class": per_class,
        "oof_true": y.values,
        "oof_pred": oof_pred,
        "oof_proba": oof_proba,
        "proba_classes": classes_sorted,
    }


def format_cv_report(result: dict[str, Any]) -> str:
    lines = [
        f"Target: {result['target']}",
        f"  CV accuracy (stratified {N_SPLITS}-fold, out-of-fold): {result['accuracy']:.1%}  "
        f"(n={result['n_used']} rows across {len(result['per_class'])} classes with >= {MIN_CLASS_SIZE_FOR_CV} examples)",
    ]
    if result["rare_classes"]:
        excluded = ", ".join(f"{k} (n={v})" for k, v in sorted(result["rare_classes"].items(), key=lambda kv: -kv[1]))
        lines.append(
            f"  EXCLUDED from CV -- too few examples for a valid {N_SPLITS}-fold stratified split "
            f"(need >= {MIN_CLASS_SIZE_FOR_CV}): {excluded}"
        )
        lines.append(
            f"  ({result['n_excluded_rare']} row(s) excluded; these classes are still in the final fitted "
            "model, just without a trustworthy CV number)"
        )
    lines.append("")
    lines.append(f"  {'label':<18}{'precision':>10}{'recall':>9}{'f1':>8}{'support':>9}")
    for _, r in result["per_class"].iterrows():
        lines.append(f"  {r.label:<18}{r.precision:>10.2f}{r.recall:>9.2f}{r.f1:>8.2f}{int(r.support):>9d}")
    return "\n".join(lines)


def format_probability_distribution(result: dict[str, Any]) -> str:
    """Distribution of the out-of-fold predicted probability for whichever
    class the model actually predicted (its own confidence in its own guess) --
    the honest way to look at this: in-sample probabilities on a model that's
    already seen the row are almost always overconfident."""
    max_proba = result["oof_proba"].max(axis=1)
    correct = result["oof_true"] == result["oof_pred"]

    percentiles = np.percentile(max_proba, [0, 25, 50, 75, 100])
    lines = [
        f"Target: {result['target']}  (n={len(max_proba)} out-of-fold predictions)",
        f"  min/25%/median/75%/max: {percentiles[0]:.2f} / {percentiles[1]:.2f} / {percentiles[2]:.2f} "
        f"/ {percentiles[3]:.2f} / {percentiles[4]:.2f}",
        f"  mean: {max_proba.mean():.2f}",
        "",
        f"  {'threshold':<12}{'rows >= thresh':>16}{'accuracy among them':>22}",
    ]
    for thresh in (0.5, 0.6, 0.7, 0.8, 0.9):
        mask = max_proba >= thresh
        n = int(mask.sum())
        acc = float(correct[mask].mean()) if n else float("nan")
        acc_str = f"{acc:.1%}" if n else "n/a"
        lines.append(f"  >= {thresh:.1f}      {n:>10d}/{len(max_proba)}{acc_str:>22}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pd.set_option("display.width", 160)

    df = load_training_data()
    print(f"\nLoaded {len(df)} genuine LLM-labeled rows from "
          f"{os.path.relpath(LABELED_PATH, REPO_ROOT)}\n")

    for target in ("action", "message_type"):
        print("=" * 72)
        result = cross_validate_target(df, target)
        print(format_cv_report(result))
        print()
        print(format_probability_distribution(result))
        print()

    print("=" * 72)
    print("Fitting final production model on all", len(df), "rows (including rare classes)...")
    clf = CheapClassifier().fit(df)
    print(f"  action classes learned:       {clf.action_classes_}")
    print(f"  message_type classes learned: {clf.message_type_classes_}")

    proba = clf.predict_proba(df.head(3))
    print("\nSanity check -- predict_proba() on the first 3 training rows:")
    for i in range(3):
        a_classes, a_proba = proba["action"]["classes"], proba["action"]["proba"][i]
        t_classes, t_proba = proba["message_type"]["classes"], proba["message_type"]["proba"][i]
        a_top = a_classes[int(np.argmax(a_proba))]
        t_top = t_classes[int(np.argmax(t_proba))]
        print(f"  {df.iloc[i].message_id}: action={a_top} (p={a_proba.max():.2f})  "
              f"message_type={t_top} (p={t_proba.max():.2f})")
