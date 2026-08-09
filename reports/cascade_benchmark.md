# Cascade Benchmark

Run 2026-08-08 18:13:38. Compares the pure-LLM path (`src/router.py`'s `Router`) against
the 3-tier cascade (`src/cascade_router.py`'s `CascadeRouter`) on the same rows,
same model (`claude-haiku-4-5`).

Response cache was **disabled** for every LLM call in this run (both pure-LLM and cascade tier-3 escalations) -- every `LLM calls` / `cost` figure below reflects genuine fresh API calls, not cache hits left over from an earlier run.

Cascade gates: `action_threshold=0.9`,
`message_type_threshold=0.9`,
`validated_message_type_classes=['event', 'forward', 'personal', 'promotion', 'scam', 'urgent']`.

**Final corrected run** -- fix applied: tier-2 action eligibility is now categorically
restricted (`restrict_action_eligibility=True`, the new default), excluding any message
matching the same audited injection/credential/hard-urgency patterns tier-1 rules 1, 2,
6.5, and 7 already use. This targets the root cause found in the diagnostic run: the
cheap classifier was 99% confident and WRONG on synth_003 (a genuine emergency, alarm
vocabulary), because training data has a 56%/36% mute/notify skew among alarm-vocabulary
rows (manufactured-urgency scam messages outnumber genuine emergencies). A confidence
threshold bump could not have caught this (the wrong prediction was already at p=0.99);
this is a categorical exclusion, not a probability gate.

## sample_messages.csv

`dataset\sample_messages.csv`, n=30

| | action acc | message_type acc | fully correct | wall-clock | LLM calls | cost |
|---|---|---|---|---|---|---|
| Pure LLM | 96.7% | 76.7% | 76.7% | 50.8s | 27 | $0.1604 |
| Cascade | 96.7% | 83.3% | 83.3% | 30.8s | 18 | $0.1055 |

### Cascade resolution breakdown

| Tier | Rows | % of total |
|---|---|---|
| Tier 2 -- fully resolved (action + message_type both from classifier) | 2 | 6.7% |
| Tier 1+2 mixed -- tier-2 action + tier-1 message_type | 9 | 30.0% |
| Tier 3 -- escalated to LLM | 19 | 63.3% |

Of the 11 messages tier 2 resolved (fully or partially): **2/11 (18.2%) were fully tier 2**, **9/11 (81.8%) were the action-only-with-tier-1-type mix**.

### Rows where cascade action != pure-LLM action

```
No rows -- cascade and pure LLM agreed on action for every message.
```

## synthetic_test.csv (held-out)

`dataset\synthetic_test.csv`, n=18

| | action acc | message_type acc | fully correct | wall-clock | LLM calls | cost |
|---|---|---|---|---|---|---|
| Pure LLM | 88.9% | 77.8% | 66.7% | 28.3s | 18 | $0.1003 |
| Cascade | 77.8% | 77.8% | 61.1% | 28.5s | 15 | $0.0829 |

### Cascade resolution breakdown

| Tier | Rows | % of total |
|---|---|---|
| Tier 2 -- fully resolved (action + message_type both from classifier) | 1 | 5.6% |
| Tier 1+2 mixed -- tier-2 action + tier-1 message_type | 2 | 11.1% |
| Tier 3 -- escalated to LLM | 15 | 83.3% |

Of the 3 messages tier 2 resolved (fully or partially): **1/3 (33.3%) were fully tier 2**, **2/3 (66.7%) were the action-only-with-tier-1-type mix**.

### Rows where cascade action != pure-LLM action

```
- synth_004 (expected=digest)
    text: 'HDFC Rewards: Enjoy an exclusive cashback offer on your next 3 transactions this month. Tap to explore your personalized deal.'
    pure LLM  -> mute (WRONG)
    cascade   -> notify (WRONG), resolved by tier1_type_tier2_action, tier-2 action confidence for this row = 0.99
- synth_009 (expected=mute)
    text: "Big savings alert: exclusive deal on electronics this week only. Tap to view your personalized offer before it's gone."
    pure LLM  -> notify (WRONG)
    cascade   -> digest (WRONG), resolved by tier3_llm, tier-2 action confidence for this row = 0.86
- synth_013 (expected=digest)
    text: 'Hi, are you the one coordinating the community garden clean-up this month?'
    pure LLM  -> digest (correct)
    cascade   -> notify (WRONG), resolved by tier3_llm, tier-2 action confidence for this row = 0.56
- synth_018 (expected=digest)
    text: 'Admin note: the community potluck sign-up sheet is open till next Sunday, no need to reply here, just add your name and dish directly in the sheet.'
    pure LLM  -> digest (correct)
    cascade   -> mute (WRONG), resolved by tier3_llm, tier-2 action confidence for this row = 0.51
```

### Note on the 4 remaining synthetic action diffs

`synth_003` -- the row that motivated this fix -- no longer appears in this diff at all: tier-2
action confidence for it is still ~0.99 mute, but `_tier2_action_eligible` now categorically
rejects it (hard-urgency pattern match), so it escalates to tier 3 and matches pure-LLM.
The fix works as intended.

Of the 4 rows that *do* still differ, only **1** (`synth_004`) is actually caused by the
cascade's own tier-2 mechanism -- and even there, pure LLM's independent answer was also
wrong (just a different wrong answer). The other **3** (`synth_009`, `synth_013`, `synth_018`)
were resolved by `tier3_llm` -- i.e. the cascade rejected tier 2 and made its own fresh LLM
call, same prompt as pure-LLM's call for the same row. With the response cache disabled,
these are two independent samples from the model for the same input, and they disagree.
This is LLM output non-determinism between separate API calls, not a cascade design flaw --
confirmed separately by pure-LLM's own synthetic action accuracy moving between runs on the
exact same 18 rows and prompts (83.3% in the diagnostic run vs 88.9% in this run) purely from
re-querying the API with cache off. Any single benchmark run's accuracy gap between pure-LLM
and cascade on an 18-row set has meaningful noise from this source alone.

Separately: 1 row in `sample_messages.csv` (`sample_msg_046`) hit an LLM call failure
(`_route_via_llm` returned `None`) and fell back to tier 1's rule-based answer
(`tier3_unavailable_fallback_tier1`). This is expected, intermittent behavior already seen
in the original 110-row full-dataset labeling run (7/110 rows fell back the same way) --
not something introduced by this fix.
