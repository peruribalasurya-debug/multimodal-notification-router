# Multimodal Notification Router

A WhatsApp inbox mixes family chats, school circulars, business promotions, scams, and
voice notes into a single stream, and treating every message the same produces two bad
outcomes at once: important messages get buried, and low-value or unsafe ones interrupt
the user anyway. This project routes every incoming message — text, image poster, or
voice note — to `notify` (interrupt now), `digest` (surface later), or `mute` (suppress),
using each recipient's own relationship history, group/business context, and prior
reactions, not a one-size-fits-all label per message type. It combines a small audited
rule layer, a cheap local classifier, and an LLM (`claude-haiku-4-5` by default) in a
3-tier cascade so most messages resolve without an API call at all, with an LLM escalation
path and a non-negotiable safety-override layer for the rest.

---

## How it works

```mermaid
flowchart TD
    A["Incoming message\ndataset/messages.csv row"] --> B["Stage 1: Context assembly\nsrc/context.py\nuser/group/business joins +\nTF-IDF history retrieval"]
    B --> C["Stage 2: Media extraction\nsrc/media.py\nvision OCR / faster-whisper ASR"]
    C --> D["Tier 1: Deterministic rules\nsrc/router.py _route_via_rules\nalways runs first -- free, instant"]

    D --> E["Tier 2: Cheap classifier\nsrc/cheap_classifier.py\nTF-IDF + logistic regression"]

    E --> F{"action confidence >= 0.9\nAND not alarm/credential/\ninjection pattern?"}
    E --> G{"message_type confidence >= 0.9\nAND class in validated allow-list?\n(scam, forward, promotion,\nurgent, event, personal)"}

    F -- yes --> F1["tier-2 action accepted"]
    F -- no --> F2["action rejected"]
    G -- yes --> G1["tier-2 message_type accepted"]
    G -- no --> G2["message_type rejected"]

    F1 --> H{Both accepted?}
    G1 --> H
    H -- "action + type" --> I["Resolved fully at tier 2\nno LLM call"]
    H -- "action only, tier 1 had\nits own message_type" --> J["Mixed: tier-2 action +\ntier-1 message_type\nno LLM call"]
    F2 --> K["Tier 3: LLM escalation\nsrc/router.py _route_via_llm\nclaude-haiku-4-5, JSON-schema output"]
    G2 --> K

    I --> L["Safety override layer\nsrc/router.py _apply_overrides\nscam/spam -> forced mute;\nevidence validated against\nmessage_history.csv; confidence\ncalibrated -- runs on every\npath, no exceptions"]
    J --> L
    K --> L

    L --> M["output.csv row\nmessage_id, action, message_type,\nreason, confidence,\nevidence_message_ids"]
```

Tier 2's two fields are gated **independently and asymmetrically** because they aren't
equally reliable: cross-validated against 103 genuine LLM labels, the action classifier
hits 92.3% accuracy at its 0.9-confidence threshold, but message_type only reaches 76.0%
at the same threshold — and 5 of 11 message_type classes (`business_update`, `greeting`,
`payment`, `unknown`, `spam`) had too few training examples for any valid cross-validation
score at all. So message_type from tier 2 is only ever accepted for the 6 classes that
*did* validate, and if action clears its bar but message_type doesn't, the whole message
escalates to tier 3 rather than mixing a trusted tier-2 action with an untrusted tier-2
type. The one exception: if tier 1's own rules already produced a non-`unknown`
message_type independently, that pairs with tier 2's action instead of escalating —
see the middle branch above.

Whichever tier resolves the fields, every message still passes through the same safety
override layer before it's written out: known scam/spam signals are forced to `mute`
regardless of what upstream predicted, cited evidence IDs are validated against
`message_history.csv` so a hallucinated citation never reaches the output, and confidence
is calibrated — the one part of the pipeline with zero exceptions, on every path.

---

## Personalization in action

The clearest proof the system isn't just classifying message *type* is two byte-identical
messages, same sender, same group, same day — routed oppositely because the two
recipients have opposite histories with similar messages:

| | [`sample_msg_044`](./dataset/sample_messages.csv) | [`sample_msg_045`](./dataset/sample_messages.csv) |
|---|---|---|
| Message | *"Photos for the kurta set are attached. Pickup is near Gate 2 this weekend."* (+ image) | *(identical text and image)* |
| Sender → recipient | `u_048` → `u_032`, in `group_005` | `u_048` → `u_033`, in `group_005` |
| Recipient's history with similar listings | Opened a near-identical peer marketplace post (`message_0049`), even if slowly (120 min) | **Dismissed** the notification for a near-identical post and **muted** the sender afterward (`message_0050`) |
| Routed action | **`digest`** — worth seeing, not urgent | **`mute`** — this recipient has already shown they don't want these |

Both decisions came from the same retrieval step in `src/context.py` (TF-IDF similarity
against each recipient's *own* message history, joined to their *own* actual reactions in
`message_events.csv`) feeding the same rules/classifier/LLM cascade — the system never
special-cased these two users, it just used what it retrieved.

---

## Results

### Sample eval — 30 labeled messages ([`reports/eval_summary.md`](./reports/eval_summary.md))

| | action accuracy | message_type accuracy |
|---|---|---|
| Pure LLM (`claude-haiku-4-5`) | 96.7% (29/30) | 76.7% (23/30) |

### Synthetic held-out eval — 18 hand-crafted cases never used to tune the rules

| | action accuracy | message_type accuracy | fully correct |
|---|---|---|---|
| Pure LLM | 83.3–88.9%* (15–16/18) | 77.8–83.3%* (14–15/18) | 66.7–72.2%* |

\* *Ranges, not a typo — see the callout below. `temperature` isn't set on the API call,
so identical prompts against `claude-haiku-4-5` don't always return identical answers,
and this 18-row set is small enough for that variance to move the headline number by a
row or two between runs.*

**Confusion matrices and confidence calibration** (from the most recent full 30-row run):

| Action | Message type |
|---|---|
| ![Action confusion matrix](./reports/confusion_action_latest.png) | ![Message type confusion matrix](./reports/confusion_message_type_latest.png) |

![Reliability diagram](./reports/reliability_diagram_latest.png)

---

## The 3-tier cascade: trading LLM calls for cost, not accuracy

Benchmark below ([`reports/cascade_benchmark.md`](./reports/cascade_benchmark.md)) compares
the pure-LLM path against the cascade on the same rows, same model, with the response
cache **disabled** for every LLM call so the numbers are genuine fresh API calls, not
cache-hit artifacts:

| Dataset | | action acc | type acc | LLM calls | cost |
|---|---|---|---|---|---|
| Samples (n=30) | Pure LLM | 96.7% | 76.7% | 27 | $0.1604 |
| Samples (n=30) | Cascade | 96.7% | 83.3% | 18 | $0.1055 |
| Synthetic (n=18) | Pure LLM | 88.9% | 77.8% | 18 | $0.1003 |
| Synthetic (n=18) | Cascade | 77.8%† | 77.8% | 15 | $0.0829 |

Combined: **$0.2607 → $0.1884, a ~28% cost reduction** — specific to this 48-message eval
set (45 → 33 LLM calls, ~27% fewer, resolving 17–37% of messages locally for free
depending on the set), not a claim about the full 110-message run or any other traffic
mix; the tier-2 classifier was trained on only 103 labeled examples, and its
coverage/accuracy on a materially different message distribution would need
re-validating before trusting this exact number elsewhere.

† See the callout below — most of this dataset's action-accuracy gap is LLM call
non-determinism between the pure-LLM and cascade's *own* independent tier-3 calls, not the
cascade design.

---

## What we learned: an emergency that looked like a scam

> **The cheap classifier was 99% confident, and wrong, about a genuine emergency.**
>
> [`synth_003`](./dataset/synthetic_test.csv): *"Emergency: the water tank valve on 3rd
> floor has burst and flooding has started. Please shut the main supply valve immediately
> and call the plumber helpline now."* Expected action: `notify` — a direct safety
> emergency that should override even a muted group. The tier-2 classifier called it
> `mute` — at **p = 0.99**.
>
> Raising the confidence threshold couldn't have caught this; 0.99 already clears any
> threshold worth setting. So we went and quantified *why* it was so confident instead of
> just patching around it: of the 25 training rows containing alarm vocabulary
> (*immediately / emergency / urgent / now*), 14 are labeled `mute` — 11 of those are
> scam messages that manufacture false urgency to pressure a click — versus only 9
> labeled `notify`. Manufactured urgency outnumbers genuine urgency in the training data,
> so the classifier learned "alarm language → probably mute" as a shortcut. That shortcut
> is right most of the time and catastrophically wrong on the messages that matter most.
>
> The fix isn't a bigger number, it's a different *kind* of check: messages matching the
> same audited safety/urgency/credential regex patterns tier-1's own rules already use are
> now excluded from tier-2 action resolution categorically, regardless of confidence, and
> fall through to the LLM instead (`src/cascade_router.py`, `ACTION_INELIGIBILITY_PATTERNS`
> / `_tier2_action_eligible`). A probability threshold answers "how sure is the model?" —
> it can't answer "is the model sure about the right thing?" That second question needed a
> structural answer, not a numeric one. After the fix, `synth_003` no longer even reaches
> that decision: it's categorically excluded from tier 2 and escalates straight to the LLM,
> which gets it right.

---

## Getting started (fresh clone)

The dataset ships with the repo under `dataset/` — there's no separate data-download or
setup step. Clone, install, run:

```bash
git clone <this-repo-url>
cd multimodal-notification-router
python tasks.py install
python tasks.py run
```

`python tasks.py <command>` is plain Python (`argparse` + `subprocess`) — it works
anywhere Python runs, with no dependency on GNU Make (which isn't on `PATH` by default on
Windows, in either Git Bash or PowerShell — verified in this environment). A `Makefile` is
also included as a convenience for Unix users who prefer `make <target>`; both call the
exact same underlying commands.

| Python (primary) | make (alternative, Unix) | What it does |
|---|---|---|
| `python tasks.py install` | `make install` | `pip install -r requirements.txt` |
| `python tasks.py run` | `make run` | Full pipeline: every row in `dataset/messages.csv` → `dataset/output.csv` |
| `python tasks.py eval` | `make eval` | Evaluation harness against `dataset/sample_messages.csv` + the synthetic held-out set → `reports/` |
| `python tasks.py test` | `make test` | Quick smoke test across all three pipeline stages |

Extra flags forward straight through, e.g. `python tasks.py run --limit 10` or
`python tasks.py eval --limit 5`.

**Configure secrets** — copy `.env.example` to `.env` (or export directly):

```bash
cp .env.example .env
# then set ANTHROPIC_API_KEY in .env
```

- `ANTHROPIC_API_KEY` — optional but recommended. Without it, the pipeline still produces
  a valid `output.csv` end-to-end via the deterministic rule-based classifier and local
  Tesseract OCR fallback instead.
- `ROUTER_MODEL` — defaults to `claude-haiku-4-5`. Override for a bigger model on a final
  validation run, e.g. `ROUTER_MODEL=claude-opus-5 python -m src.eval`.
- `ROUTER_WHISPER_MODEL`, `TESSERACT_CMD` — optional, see `.env.example`.

Secrets are read from the environment only — never hardcoded.

**Run it:**

```bash
python tasks.py run     # writes dataset/output.csv, validates the output contract,
                         # resumable via a checkpoint if interrupted
python tasks.py eval    # accuracy, confusion matrices, calibration, cost -- see reports/
python tasks.py test    # fast smoke test, not a full accuracy check
```

---

## Further reading

- [`docs/architecture.md`](./docs/architecture.md) — full pipeline design and the case for
  the hybrid (rules + local models + LLM) approach.
- [`docs/routing_rubric.md`](./docs/routing_rubric.md) — `message_type` definitions and the
  `notify`/`digest`/`mute` decision rules the classifier follows.
- [`src/cascade_router.py`](./src/cascade_router.py) — the 3-tier cascade implementation,
  with the full gating logic documented in its module docstring.
- [`reports/eval_summary.md`](./reports/eval_summary.md) — running log of every eval run.
- [`reports/cascade_benchmark.md`](./reports/cascade_benchmark.md) — full cascade vs.
  pure-LLM benchmark, including the per-row synthetic diff behind the callout above.
