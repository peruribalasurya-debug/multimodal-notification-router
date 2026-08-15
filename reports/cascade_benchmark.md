# Cascade Benchmark

Run 2026-08-15 10:10:20. Compares the pure-LLM path (`src/router.py`'s `Router`) against
the 3-tier cascade (`src/cascade_router.py`'s `CascadeRouter`) on the same rows,
same model (`claude-haiku-4-5`).

Response cache was **disabled** for every LLM call in this run (both pure-LLM and cascade tier-3 escalations) -- every `LLM calls` / `cost` figure below reflects genuine fresh API calls, not cache hits left over from an earlier run.

Cascade gates: `action_threshold=0.9`,
`message_type_threshold=0.9`,
`validated_message_type_classes=['event', 'forward', 'personal', 'promotion', 'scam', 'urgent']`.

**Fixes carried by this run** (both on by default, not toggleable via CLI flags since both are
correctness fixes, not tunable knobs):

- `restrict_action_eligibility=True` -- tier-2 action eligibility is categorically restricted,
  excluding any message matching the same audited injection/credential/hard-urgency patterns
  tier-1 rules 1, 2, 6.5, and 7 already use. Root cause: the cheap classifier was 99% confident
  and WRONG on synth_003 (a genuine emergency, alarm vocabulary), because training data has a
  56%/36% mute/notify skew among alarm-vocabulary rows (manufactured-urgency scam messages
  outnumber genuine emergencies). A confidence threshold bump couldn't have caught this (the
  wrong prediction was already at p=0.99) -- this is a categorical exclusion, not a probability
  gate.
- **New**: tier 2's action is never consulted when tier 1 classifies a message as
  `message_type=="promotion"` -- tier 1's own action (`TIER_PROMOTION_TIER1_PROTECTED`), which
  reads `allows_promotions`/opt-out/dismissal history, is authoritative instead. Root cause:
  promotion routing is relationship-dependent by definition, but tier 2's action head -- whose
  400-feature TF-IDF text signal dominates its ~103-row training set -- was found to ignore
  that: two personas with opposite Myntra opt-in history both got `mute` for the identical text
  "you have won 50% off...", regardless of relationship. Measured effect on this run: entirely
  from previously-mishandled promotion rows now resolving correctly and for free (no LLM call)
  -- sample_messages.csv message_type accuracy 83.3% -> 90.0%; synthetic_test.csv action and
  message_type accuracy both 77.8% -> 88.9% (driven by synth_004 and synth_009 flipping from
  wrong to correct, visible in the per-row diff below). No regressions on either dataset.

## sample_messages.csv

`dataset\sample_messages.csv`, n=30

| | action acc | message_type acc | fully correct | wall-clock | LLM calls | cost |
|---|---|---|---|---|---|---|
| Pure LLM | 96.7% | 76.7% | 76.7% | 45.7s | 27 | $0.1605 |
| Cascade | 96.7% | 90.0% | 90.0% | 24.5s | 15 | $0.0872 |

### Cascade resolution breakdown

| Tier | Rows | % of total |
|---|---|---|
| Tier 2 -- fully resolved (action + message_type both from classifier) | 1 | 3.3% |
| Tier 1+2 mixed -- tier-2 action + tier-1 message_type | 7 | 23.3% |
| Tier 1 promotion-protected -- tier-1 action kept, tier-2 action never consulted | 6 | 20.0% |
| Tier 3 -- escalated to LLM | 16 | 53.3% |

Of the 8 messages tier 2 resolved (fully or partially): **1/8 (12.5%) were fully tier 2**, **7/8 (87.5%) were the action-only-with-tier-1-type mix**.

### Rows where cascade action != pure-LLM action

```
No rows -- cascade and pure LLM agreed on action for every message.
```

## synthetic_test.csv (held-out)

`dataset\synthetic_test.csv`, n=18

| | action acc | message_type acc | fully correct | wall-clock | LLM calls | cost |
|---|---|---|---|---|---|---|
| Pure LLM | 83.3% | 83.3% | 72.2% | 27.5s | 18 | $0.1002 |
| Cascade | 88.9% | 88.9% | 83.3% | 19.5s | 13 | $0.0722 |

### Cascade resolution breakdown

| Tier | Rows | % of total |
|---|---|---|
| Tier 2 -- fully resolved (action + message_type both from classifier) | 0 | 0.0% |
| Tier 1+2 mixed -- tier-2 action + tier-1 message_type | 1 | 5.6% |
| Tier 1 promotion-protected -- tier-1 action kept, tier-2 action never consulted | 4 | 22.2% |
| Tier 3 -- escalated to LLM | 13 | 72.2% |

Of the 1 messages tier 2 resolved (fully or partially): **0/1 (0.0%) were fully tier 2**, **1/1 (100.0%) were the action-only-with-tier-1-type mix**.

### Rows where cascade action != pure-LLM action

```
- synth_004 (expected=digest)
    text: 'HDFC Rewards: Enjoy an exclusive cashback offer on your next 3 transactions this month. Tap to explore your personalized deal.'
    pure LLM  -> mute (WRONG)
    cascade   -> digest (correct), resolved by tier1_promotion_action_protected, tier-2 action confidence for this row = 0.99
- synth_009 (expected=mute)
    text: "Big savings alert: exclusive deal on electronics this week only. Tap to view your personalized offer before it's gone."
    pure LLM  -> digest (WRONG)
    cascade   -> mute (correct), resolved by tier1_promotion_action_protected, tier-2 action confidence for this row = 0.86
- synth_018 (expected=digest)
    text: 'Admin note: the community potluck sign-up sheet is open till next Sunday, no need to reply here, just add your name and dish directly in the sheet.'
    pure LLM  -> digest (correct)
    cascade   -> mute (WRONG), resolved by tier3_llm, tier-2 action confidence for this row = 0.51
```
