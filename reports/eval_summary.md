# Evaluation Summary

Running log of `python -m src.eval` runs against `dataset/sample_messages.csv`, newest last.


## Run 2026-08-02 21:32:17

Source: rule-based fallback only (no ANTHROPIC_API_KEY) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260802_213217.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               0               1               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260802_213217.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 1.00 | 1.00 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 1.00 | 1.00 | 1.00 | 4 |
| spam | 1.00 | 1.00 | 1.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

![reliability diagram](reports/reliability_diagram_20260802_213217.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

### Evidence quality

- Rows citing at least one evidence ID: 96.7% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (50 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 58.9%
- Exact-match rate with that expected evidence set: 14.3%

---

## Run 2026-08-02 21:33:41

Source: rule-based fallback only (no ANTHROPIC_API_KEY) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260802_213341.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               0               1               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260802_213341.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 1.00 | 1.00 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 1.00 | 1.00 | 1.00 | 4 |
| spam | 1.00 | 1.00 | 1.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

![reliability diagram](reports/reliability_diagram_20260802_213341.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

### Evidence quality

- Rows citing at least one evidence ID: 96.7% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (50 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 58.9%
- Exact-match rate with that expected evidence set: 14.3%

---

## Run 2026-08-02 21:43:16

Source: rule-based fallback only (no ANTHROPIC_API_KEY) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260802_214316.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               0               1               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260802_214316.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 1.00 | 1.00 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 1.00 | 1.00 | 1.00 | 4 |
| spam | 1.00 | 1.00 | 1.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

![reliability diagram](reports/reliability_diagram_20260802_214316.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

### Evidence quality

- Rows citing at least one evidence ID: 96.7% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (50 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 58.9%
- Exact-match rate with that expected evidence set: 14.3%

---

## Run 2026-08-02 22:19:55

Source: rule-based fallback only (no ANTHROPIC_API_KEY) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260802_221955.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               0               1               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260802_221955.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 1.00 | 1.00 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 1.00 | 1.00 | 1.00 | 4 |
| spam | 1.00 | 1.00 | 1.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

![reliability diagram](reports/reliability_diagram_20260802_221955.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

### Evidence quality

- Rows citing at least one evidence ID: 96.7% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (50 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 58.9%
- Exact-match rate with that expected evidence set: 14.3%

---

## Run 2026-08-02 23:46:43

Source: LLM path (ANTHROPIC_API_KEY set) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **93.3%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260802_234643.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              1               3               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               1               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260802_234643.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 0.75 | 1.00 | 0.86 | 3 |
| event | 1.00 | 0.75 | 0.86 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 0.80 | 1.00 | 0.89 | 4 |
| spam | 0.00 | 0.00 | 0.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 1 | 0.660 | 1.000 | 0.340 |
| [0.7-0.8) | 11 | 0.721 | 1.000 | 0.279 |
| [0.8-0.9) | 6 | 0.833 | 1.000 | 0.167 |
| [0.9-1.0) | 12 | 0.943 | 1.000 | 0.057 |

**Expected Calibration Error (ECE): 0.1697**

![reliability diagram](reports/reliability_diagram_20260802_234643.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 1 | 0.660 | 1.000 | 0.340 |
| [0.7-0.8) | 11 | 0.721 | 0.909 | 0.188 |
| [0.8-0.9) | 6 | 0.833 | 1.000 | 0.167 |
| [0.9-1.0) | 12 | 0.943 | 0.917 | 0.027 |

**Expected Calibration Error (ECE): 0.1243**

### Evidence quality

- Rows citing at least one evidence ID: 93.3% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (64 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 75.0%
- Exact-match rate with that expected evidence set: 17.9%

---

## Run 2026-08-03 10:20:54

Source: LLM path (ANTHROPIC_API_KEY set) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **96.7%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260803_102054.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              1               3               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               0               1               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260803_102054.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 0.75 | 1.00 | 0.86 | 3 |
| event | 1.00 | 0.75 | 0.86 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 1.00 | 1.00 | 1.00 | 4 |
| spam | 1.00 | 1.00 | 1.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 1 | 0.660 | 1.000 | 0.340 |
| [0.7-0.8) | 12 | 0.725 | 1.000 | 0.275 |
| [0.8-0.9) | 6 | 0.862 | 1.000 | 0.138 |
| [0.9-1.0) | 11 | 0.945 | 1.000 | 0.055 |

**Expected Calibration Error (ECE): 0.1693**

![reliability diagram](reports/reliability_diagram_20260803_102054.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 1 | 0.660 | 1.000 | 0.340 |
| [0.7-0.8) | 12 | 0.725 | 0.917 | 0.192 |
| [0.8-0.9) | 6 | 0.862 | 1.000 | 0.138 |
| [0.9-1.0) | 11 | 0.945 | 1.000 | 0.055 |

**Expected Calibration Error (ECE): 0.1360**

### Evidence quality

- Rows citing at least one evidence ID: 93.3% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (63 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 75.0%
- Exact-match rate with that expected evidence set: 21.4%

---

## Run 2026-08-03 11:40:37

Source: LLM path (ANTHROPIC_API_KEY set) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **96.7%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260803_114037.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               1               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260803_114037.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 1.00 | 1.00 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 0.80 | 1.00 | 0.89 | 4 |
| spam | 0.00 | 0.00 | 0.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 1 | 0.660 | 1.000 | 0.340 |
| [0.7-0.8) | 11 | 0.721 | 1.000 | 0.279 |
| [0.8-0.9) | 6 | 0.842 | 1.000 | 0.158 |
| [0.9-1.0) | 12 | 0.945 | 1.000 | 0.055 |

**Expected Calibration Error (ECE): 0.1673**

![reliability diagram](reports/reliability_diagram_20260803_114037.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 1 | 0.660 | 1.000 | 0.340 |
| [0.7-0.8) | 11 | 0.721 | 1.000 | 0.279 |
| [0.8-0.9) | 6 | 0.842 | 1.000 | 0.158 |
| [0.9-1.0) | 12 | 0.945 | 0.917 | 0.028 |

**Expected Calibration Error (ECE): 0.1567**

### Evidence quality

- Rows citing at least one evidence ID: 93.3% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (63 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 75.0%
- Exact-match rate with that expected evidence set: 21.4%

---

## Run 2026-08-04 11:35:51

Source: LLM path (ANTHROPIC_API_KEY set) — 3 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                    0      0      0
mute                      0      0      0
notify                    0      0      3
```

![action confusion matrix](reports/confusion_action_20260804_113551.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               1               0               0               0               0               0               0               0               0               0
forward                            0               0               0               0               0               0               0               0               0               0               0
greeting                           0               0               0               0               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               0               0               0               0               0               0
promotion                          0               0               0               0               0               0               0               0               0               0               0
scam                               0               0               0               0               0               0               0               0               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               2
```

![message_type confusion matrix](reports/confusion_message_type_20260804_113551.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 0.00 | 0.00 | 0.00 | 0 |
| mute | 0.00 | 0.00 | 0.00 | 0 |
| notify | 1.00 | 1.00 | 1.00 | 3 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 0.00 | 0.00 | 0.00 | 0 |
| event | 1.00 | 1.00 | 1.00 | 1 |
| forward | 0.00 | 0.00 | 0.00 | 0 |
| greeting | 0.00 | 0.00 | 0.00 | 0 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 0.00 | 0.00 | 0.00 | 0 |
| promotion | 0.00 | 0.00 | 0.00 | 0 |
| scam | 0.00 | 0.00 | 0.00 | 0 |
| spam | 0.00 | 0.00 | 0.00 | 0 |
| unknown | 0.00 | 0.00 | 0.00 | 0 |
| urgent | 1.00 | 1.00 | 1.00 | 2 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.7-0.8) | 1 | 0.700 | 1.000 | 0.300 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |

**Expected Calibration Error (ECE): 0.2267**

![reliability diagram](reports/reliability_diagram_20260804_113551.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.7-0.8) | 1 | 0.700 | 1.000 | 0.300 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |

**Expected Calibration Error (ECE): 0.2267**

### Evidence quality

- Rows citing at least one evidence ID: 100.0% (3 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (6 IDs cited total)
- Rows where the sample provides its own expected evidence: 3
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 33.3%
- Exact-match rate with that expected evidence set: 0.0%

---

## Run 2026-08-04 11:36:14

Source: LLM path (ANTHROPIC_API_KEY set) — 3 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                    0      0      0
mute                      0      0      0
notify                    0      0      3
```

![action confusion matrix](reports/confusion_action_20260804_113614.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               1               0               0               0               0               0               0               0               0               0
forward                            0               0               0               0               0               0               0               0               0               0               0
greeting                           0               0               0               0               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               0               0               0               0               0               0
promotion                          0               0               0               0               0               0               0               0               0               0               0
scam                               0               0               0               0               0               0               0               0               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               2
```

![message_type confusion matrix](reports/confusion_message_type_20260804_113614.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 0.00 | 0.00 | 0.00 | 0 |
| mute | 0.00 | 0.00 | 0.00 | 0 |
| notify | 1.00 | 1.00 | 1.00 | 3 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 0.00 | 0.00 | 0.00 | 0 |
| event | 1.00 | 1.00 | 1.00 | 1 |
| forward | 0.00 | 0.00 | 0.00 | 0 |
| greeting | 0.00 | 0.00 | 0.00 | 0 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 0.00 | 0.00 | 0.00 | 0 |
| promotion | 0.00 | 0.00 | 0.00 | 0 |
| scam | 0.00 | 0.00 | 0.00 | 0 |
| spam | 0.00 | 0.00 | 0.00 | 0 |
| unknown | 0.00 | 0.00 | 0.00 | 0 |
| urgent | 1.00 | 1.00 | 1.00 | 2 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.7-0.8) | 1 | 0.700 | 1.000 | 0.300 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |

**Expected Calibration Error (ECE): 0.2267**

![reliability diagram](reports/reliability_diagram_20260804_113614.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.7-0.8) | 1 | 0.700 | 1.000 | 0.300 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |

**Expected Calibration Error (ECE): 0.2267**

### Evidence quality

- Rows citing at least one evidence ID: 100.0% (3 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (6 IDs cited total)
- Rows where the sample provides its own expected evidence: 3
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 33.3%
- Exact-match rate with that expected evidence set: 0.0%

---

## Run 2026-08-04 11:40:57

Source: LLM path (ANTHROPIC_API_KEY set) — 2 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                    0      0      0
mute                      0      0      0
notify                    0      0      2
```

![action confusion matrix](reports/confusion_action_20260804_114057.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               1               0               0               0               0               0               0               0               0               0
forward                            0               0               0               0               0               0               0               0               0               0               0
greeting                           0               0               0               0               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               0               0               0               0               0               0
promotion                          0               0               0               0               0               0               0               0               0               0               0
scam                               0               0               0               0               0               0               0               0               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               1
```

![message_type confusion matrix](reports/confusion_message_type_20260804_114057.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 0.00 | 0.00 | 0.00 | 0 |
| mute | 0.00 | 0.00 | 0.00 | 0 |
| notify | 1.00 | 1.00 | 1.00 | 2 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 0.00 | 0.00 | 0.00 | 0 |
| event | 1.00 | 1.00 | 1.00 | 1 |
| forward | 0.00 | 0.00 | 0.00 | 0 |
| greeting | 0.00 | 0.00 | 0.00 | 0 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 0.00 | 0.00 | 0.00 | 0 |
| promotion | 0.00 | 0.00 | 0.00 | 0 |
| scam | 0.00 | 0.00 | 0.00 | 0 |
| spam | 0.00 | 0.00 | 0.00 | 0 |
| unknown | 0.00 | 0.00 | 0.00 | 0 |
| urgent | 1.00 | 1.00 | 1.00 | 1 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.7-0.8) | 1 | 0.700 | 1.000 | 0.300 |
| [0.8-0.9) | 1 | 0.810 | 1.000 | 0.190 |

**Expected Calibration Error (ECE): 0.2450**

![reliability diagram](reports/reliability_diagram_20260804_114057.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.7-0.8) | 1 | 0.700 | 1.000 | 0.300 |
| [0.8-0.9) | 1 | 0.810 | 1.000 | 0.190 |

**Expected Calibration Error (ECE): 0.2450**

### Evidence quality

- Rows citing at least one evidence ID: 100.0% (2 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (4 IDs cited total)
- Rows where the sample provides its own expected evidence: 2
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 50.0%
- Exact-match rate with that expected evidence set: 0.0%

---

## Run 2026-08-05 09:59:14

Source: rule-based fallback only (no ANTHROPIC_API_KEY) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260805_095914.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               0               1               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260805_095914.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 1.00 | 1.00 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 1.00 | 1.00 | 1.00 | 4 |
| spam | 1.00 | 1.00 | 1.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

![reliability diagram](reports/reliability_diagram_20260805_095914.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

### Evidence quality

- Rows citing at least one evidence ID: 96.7% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (45 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 58.9%
- Exact-match rate with that expected evidence set: 25.0%

---

## Run 2026-08-08 11:13:36

Source: rule-based fallback only (no ANTHROPIC_API_KEY) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260808_111336.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               0               1               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260808_111336.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 1.00 | 1.00 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 1.00 | 1.00 | 1.00 | 4 |
| spam | 1.00 | 1.00 | 1.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

![reliability diagram](reports/reliability_diagram_20260808_111336.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

### Evidence quality

- Rows citing at least one evidence ID: 96.7% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (45 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 58.9%
- Exact-match rate with that expected evidence set: 25.0%

---

## Run 2026-08-08 11:26:34

Source: rule-based fallback only (no ANTHROPIC_API_KEY) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260808_112634.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               0               1               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260808_112634.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 1.00 | 1.00 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 1.00 | 1.00 | 1.00 | 4 |
| spam | 1.00 | 1.00 | 1.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

![reliability diagram](reports/reliability_diagram_20260808_112634.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

### Evidence quality

- Rows citing at least one evidence ID: 96.7% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (45 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 58.9%
- Exact-match rate with that expected evidence set: 25.0%

---

## Run 2026-08-08 11:40:23

Source: rule-based fallback only (no ANTHROPIC_API_KEY) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **100.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   11      0      0
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260808_114023.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               0               6               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               0               1               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260808_114023.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 1.00 | 1.00 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 1.00 | 1.00 | 1.00 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 1.00 | 1.00 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 1.00 | 1.00 | 1.00 | 4 |
| promotion | 1.00 | 1.00 | 1.00 | 6 |
| scam | 1.00 | 1.00 | 1.00 | 4 |
| spam | 1.00 | 1.00 | 1.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 1.00 | 1.00 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

![reliability diagram](reports/reliability_diagram_20260808_114023.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.5-0.6) | 4 | 0.583 | 1.000 | 0.417 |
| [0.6-0.7) | 9 | 0.656 | 1.000 | 0.344 |
| [0.7-0.8) | 10 | 0.718 | 1.000 | 0.282 |
| [0.8-0.9) | 2 | 0.810 | 1.000 | 0.190 |
| [0.9-1.0) | 5 | 0.932 | 1.000 | 0.068 |

**Expected Calibration Error (ECE): 0.2770**

### Evidence quality

- Rows citing at least one evidence ID: 96.7% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (45 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 58.9%
- Exact-match rate with that expected evidence set: 25.0%

### Synthetic (held-out)

```
n = 18 hand-crafted, held-out cases (never used to tune the rules)
action accuracy:       100.0%  (18/18)
message_type accuracy: 100.0%  (18/18)
fully correct (both):  100.0%  (18/18)

--- confusion matrix: action ---
expected \ predicted digest   mute notify
digest                    6      0      0
mute                      0      7      0
notify                    0      0      5

--- confusion matrix: message_type ---
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               3               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               1               0               0               0               0               0               0               0
payment                            0               0               0               0               1               0               0               0               0               0               0
personal                           0               0               0               0               0               2               0               0               0               0               0
promotion                          0               0               0               0               0               0               4               0               0               0               0
scam                               0               0               0               0               0               0               0               3               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               0               0               0               0               0               0               0               0               0               2

--- per-row results ---
synth_001     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=payment          exp=payment         
synth_002     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_003     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_004     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=promotion        exp=promotion       
synth_005     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_006     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_007     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=greeting         exp=greeting        
synth_008     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_009     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_010     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=personal         exp=personal        
synth_011     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_012     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=forward          exp=forward         
synth_013     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=unknown          exp=unknown         
synth_014     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
synth_015     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=event            exp=event           
synth_016     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=promotion        exp=promotion       
synth_017     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=personal         exp=personal        
synth_018     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
```

---

## Run 2026-08-08 12:45:13

Source: LLM path (ANTHROPIC_API_KEY set) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **96.7%**
- message_type: **76.7%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   10      0      1
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260808_124513.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               3               0               0               0               0               0               0               0               0               1
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               3               0               0               0               0               1
promotion                          0               0               0               0               0               2               3               0               0               1               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               1               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               0               1
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260808_124513.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 0.91 | 0.95 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 0.90 | 1.00 | 0.95 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 0.75 | 0.86 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 0.60 | 0.75 | 0.67 | 4 |
| promotion | 1.00 | 0.50 | 0.67 | 6 |
| scam | 0.80 | 1.00 | 0.89 | 4 |
| spam | 0.00 | 0.00 | 0.00 | 1 |
| unknown | 0.00 | 0.00 | 0.00 | 1 |
| urgent | 0.57 | 1.00 | 0.73 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 1 | 0.660 | 1.000 | 0.340 |
| [0.7-0.8) | 9 | 0.729 | 1.000 | 0.271 |
| [0.8-0.9) | 2 | 0.800 | 0.500 | 0.300 |
| [0.9-1.0) | 18 | 0.936 | 1.000 | 0.064 |

**Expected Calibration Error (ECE): 0.1510**

![reliability diagram](reports/reliability_diagram_20260808_124513.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 1 | 0.660 | 1.000 | 0.340 |
| [0.7-0.8) | 9 | 0.729 | 0.778 | 0.049 |
| [0.8-0.9) | 2 | 0.800 | 0.500 | 0.300 |
| [0.9-1.0) | 18 | 0.936 | 0.778 | 0.158 |

**Expected Calibration Error (ECE): 0.1410**

### Evidence quality

- Rows citing at least one evidence ID: 93.3% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (31 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 46.4%
- Exact-match rate with that expected evidence set: 39.3%

### Synthetic (held-out)

```
n = 18 hand-crafted, held-out cases (never used to tune the rules)
action accuracy:       83.3%  (15/18)
message_type accuracy: 83.3%  (15/18)
fully correct (both):  72.2%  (13/18)

--- confusion matrix: action ---
expected \ predicted digest   mute notify
digest                    4      1      1
mute                      1      6      0
notify                    0      0      5

--- confusion matrix: message_type ---
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               3               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               1               0               0               0               0               0               0               0
payment                            0               0               0               0               1               0               0               0               0               0               0
personal                           0               0               0               0               0               1               0               0               0               0               1
promotion                          0               0               0               0               0               1               3               0               0               0               0
scam                               0               0               0               0               0               0               0               3               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               1               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               2

--- per-row results ---
synth_001     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=payment          exp=payment         
synth_002     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_003     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_004     action[MISS] pred=mute    exp=digest   type[OK  ] pred=promotion        exp=promotion       
synth_005     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_006     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_007     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=greeting         exp=greeting        
synth_008     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_009     action[MISS] pred=digest  exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_010     action[OK  ] pred=notify  exp=notify   type[MISS] pred=urgent           exp=personal        
synth_011     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_012     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=forward          exp=forward         
synth_013     action[MISS] pred=notify  exp=digest   type[MISS] pred=personal         exp=unknown         
synth_014     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
synth_015     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=event            exp=event           
synth_016     action[OK  ] pred=digest  exp=digest   type[MISS] pred=personal         exp=promotion       
synth_017     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=personal         exp=personal        
synth_018     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
```

---


## Analysis: LLM vs rules, samples vs synthetic (2026-08-08)

Comparing the LLM path (`claude-haiku-4-5`, run 2026-08-08 12:45:13 above) against the deterministic rule-based fallback: on `sample_messages.csv` the LLM scores 96.7% action / 76.7% message_type accuracy versus 100%/100% for rules; on the synthetic held-out set (18 hand-crafted cases the rules were never tuned against) the LLM scores 83.3% action / 83.3% message_type (72.2% fully correct) versus 100%/100% for rules. The rules outperform the LLM path on *both* the tuned sample set and the genuinely held-out synthetic set, which is evidence against "the rules are overfit" — an overfit rule set would have degraded sharply on synthetic data, and instead it matched its sample-set performance exactly. The LLM gap is better explained by the cost-driven default model (`claude-haiku-4-5`) than by any deficiency in the rules; the event/business_update disambiguation fix from earlier in this session holds on this run (zero cross-confusion between those two types in either direction), and evidence-citation exact-match improved sharply (21.4% → 39.3%) at the cost of some overlap/recall (75.0% → 46.4%), consistent with the tightened single-citation prompt instruction added since the last LLM-path run. The natural next step is re-running with a bigger model (`ROUTER_MODEL=claude-opus-5`) before concluding Haiku's accuracy ceiling here is final.

---

## Run 2026-08-08 13:33:53

Source: LLM path (ANTHROPIC_API_KEY set) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **96.7%**
- message_type: **86.7%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   10      0      1
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260808_133353.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               4               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               4               0               0               0               0               0
promotion                          0               0               0               0               0               2               4               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               1               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               1               0               0               0               0               0               0               0               0               3
```

![message_type confusion matrix](reports/confusion_message_type_20260808_133353.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 0.91 | 0.95 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 0.90 | 1.00 | 0.95 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 0.80 | 1.00 | 0.89 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 0.67 | 1.00 | 0.80 | 4 |
| promotion | 1.00 | 0.67 | 0.80 | 6 |
| scam | 0.80 | 1.00 | 0.89 | 4 |
| spam | 0.00 | 0.00 | 0.00 | 1 |
| unknown | 1.00 | 1.00 | 1.00 | 1 |
| urgent | 1.00 | 0.75 | 0.86 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 5 | 0.672 | 0.800 | 0.128 |
| [0.7-0.8) | 10 | 0.717 | 1.000 | 0.283 |
| [0.8-0.9) | 4 | 0.847 | 1.000 | 0.153 |
| [0.9-1.0) | 11 | 0.938 | 1.000 | 0.062 |

**Expected Calibration Error (ECE): 0.1587**

![reliability diagram](reports/reliability_diagram_20260808_133353.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 5 | 0.672 | 0.600 | 0.072 |
| [0.7-0.8) | 10 | 0.717 | 0.900 | 0.183 |
| [0.8-0.9) | 4 | 0.847 | 0.750 | 0.097 |
| [0.9-1.0) | 11 | 0.938 | 0.909 | 0.029 |

**Expected Calibration Error (ECE): 0.0967**

### Evidence quality

- Rows citing at least one evidence ID: 93.3% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (35 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 55.4%
- Exact-match rate with that expected evidence set: 35.7%

### Synthetic (held-out)

```
n = 18 hand-crafted, held-out cases (never used to tune the rules)
action accuracy:       94.4%  (17/18)
message_type accuracy: 83.3%  (15/18)
fully correct (both):  77.8%  (14/18)

--- confusion matrix: action ---
expected \ predicted digest   mute notify
digest                    5      0      1
mute                      0      7      0
notify                    0      0      5

--- confusion matrix: message_type ---
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               3               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               1               0               0               0               0               0               0               0               0
payment                            0               0               0               0               1               0               0               0               0               0               0
personal                           0               0               0               0               0               2               0               0               0               0               0
promotion                          0               0               0               0               0               1               3               0               0               0               0
scam                               0               0               0               0               0               0               0               3               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               1               0
urgent                             0               1               0               0               0               0               0               0               0               0               1

--- per-row results ---
synth_001     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=payment          exp=payment         
synth_002     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_003     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_004     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=promotion        exp=promotion       
synth_005     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_006     action[OK  ] pred=notify  exp=notify   type[MISS] pred=event            exp=urgent          
synth_007     action[OK  ] pred=mute    exp=mute     type[MISS] pred=forward          exp=greeting        
synth_008     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_009     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_010     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=personal         exp=personal        
synth_011     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_012     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=forward          exp=forward         
synth_013     action[MISS] pred=notify  exp=digest   type[OK  ] pred=unknown          exp=unknown         
synth_014     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
synth_015     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=event            exp=event           
synth_016     action[OK  ] pred=digest  exp=digest   type[MISS] pred=personal         exp=promotion       
synth_017     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=personal         exp=personal        
synth_018     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
```

---

## Run 2026-08-08 18:53:44

Source: LLM path (ANTHROPIC_API_KEY set) — 2 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **50.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                    0      0      0
mute                      0      0      0
notify                    0      0      2
```

![action confusion matrix](reports/confusion_action_20260808_185344.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               0               0               0               0               0               0               0               0               0               1
forward                            0               0               0               0               0               0               0               0               0               0               0
greeting                           0               0               0               0               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               0               0               0               0               0               0
promotion                          0               0               0               0               0               0               0               0               0               0               0
scam                               0               0               0               0               0               0               0               0               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               1
```

![message_type confusion matrix](reports/confusion_message_type_20260808_185344.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 0.00 | 0.00 | 0.00 | 0 |
| mute | 0.00 | 0.00 | 0.00 | 0 |
| notify | 1.00 | 1.00 | 1.00 | 2 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 0.00 | 0.00 | 0.00 | 0 |
| event | 0.00 | 0.00 | 0.00 | 1 |
| forward | 0.00 | 0.00 | 0.00 | 0 |
| greeting | 0.00 | 0.00 | 0.00 | 0 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 0.00 | 0.00 | 0.00 | 0 |
| promotion | 0.00 | 0.00 | 0.00 | 0 |
| scam | 0.00 | 0.00 | 0.00 | 0 |
| spam | 0.00 | 0.00 | 0.00 | 0 |
| unknown | 0.00 | 0.00 | 0.00 | 0 |
| urgent | 0.50 | 1.00 | 0.67 | 1 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.9-1.0) | 2 | 0.935 | 1.000 | 0.065 |

**Expected Calibration Error (ECE): 0.0650**

![reliability diagram](reports/reliability_diagram_20260808_185344.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.9-1.0) | 2 | 0.935 | 0.500 | 0.435 |

**Expected Calibration Error (ECE): 0.4350**

### Evidence quality

- Rows citing at least one evidence ID: 100.0% (2 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (4 IDs cited total)
- Rows where the sample provides its own expected evidence: 2
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 50.0%
- Exact-match rate with that expected evidence set: 0.0%

### Synthetic (held-out)

```
n = 18 hand-crafted, held-out cases (never used to tune the rules)
action accuracy:       83.3%  (15/18)
message_type accuracy: 83.3%  (15/18)
fully correct (both):  72.2%  (13/18)

--- confusion matrix: action ---
expected \ predicted digest   mute notify
digest                    4      1      1
mute                      1      6      0
notify                    0      0      5

--- confusion matrix: message_type ---
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               3               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               1               0               0               0               0               0               0               0               0
payment                            0               0               0               0               1               0               0               0               0               0               0
personal                           0               0               0               0               0               2               0               0               0               0               0
promotion                          0               0               0               0               0               1               3               0               0               0               0
scam                               0               0               0               0               0               0               0               3               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               1               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               2

--- per-row results ---
synth_001     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=payment          exp=payment         
synth_002     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_003     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_004     action[MISS] pred=mute    exp=digest   type[OK  ] pred=promotion        exp=promotion       
synth_005     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_006     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_007     action[OK  ] pred=mute    exp=mute     type[MISS] pred=forward          exp=greeting        
synth_008     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_009     action[MISS] pred=digest  exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_010     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=personal         exp=personal        
synth_011     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_012     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=forward          exp=forward         
synth_013     action[MISS] pred=notify  exp=digest   type[MISS] pred=personal         exp=unknown         
synth_014     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
synth_015     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=event            exp=event           
synth_016     action[OK  ] pred=digest  exp=digest   type[MISS] pred=personal         exp=promotion       
synth_017     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=personal         exp=personal        
synth_018     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
```

---

## Run 2026-08-08 18:54:48

Source: LLM path (ANTHROPIC_API_KEY set) — 2 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **50.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                    0      0      0
mute                      0      0      0
notify                    0      0      2
```

![action confusion matrix](reports/confusion_action_20260808_185448.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               0               0               0               0               0               0               0               0               0               1
forward                            0               0               0               0               0               0               0               0               0               0               0
greeting                           0               0               0               0               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               0               0               0               0               0               0
promotion                          0               0               0               0               0               0               0               0               0               0               0
scam                               0               0               0               0               0               0               0               0               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               1
```

![message_type confusion matrix](reports/confusion_message_type_20260808_185448.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 0.00 | 0.00 | 0.00 | 0 |
| mute | 0.00 | 0.00 | 0.00 | 0 |
| notify | 1.00 | 1.00 | 1.00 | 2 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 0.00 | 0.00 | 0.00 | 0 |
| event | 0.00 | 0.00 | 0.00 | 1 |
| forward | 0.00 | 0.00 | 0.00 | 0 |
| greeting | 0.00 | 0.00 | 0.00 | 0 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 0.00 | 0.00 | 0.00 | 0 |
| promotion | 0.00 | 0.00 | 0.00 | 0 |
| scam | 0.00 | 0.00 | 0.00 | 0 |
| spam | 0.00 | 0.00 | 0.00 | 0 |
| unknown | 0.00 | 0.00 | 0.00 | 0 |
| urgent | 0.50 | 1.00 | 0.67 | 1 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.9-1.0) | 2 | 0.935 | 1.000 | 0.065 |

**Expected Calibration Error (ECE): 0.0650**

![reliability diagram](reports/reliability_diagram_20260808_185448.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.9-1.0) | 2 | 0.935 | 0.500 | 0.435 |

**Expected Calibration Error (ECE): 0.4350**

### Evidence quality

- Rows citing at least one evidence ID: 100.0% (2 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (4 IDs cited total)
- Rows where the sample provides its own expected evidence: 2
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 50.0%
- Exact-match rate with that expected evidence set: 0.0%

### Synthetic (held-out)

```
n = 18 hand-crafted, held-out cases (never used to tune the rules)
action accuracy:       83.3%  (15/18)
message_type accuracy: 83.3%  (15/18)
fully correct (both):  72.2%  (13/18)

--- confusion matrix: action ---
expected \ predicted digest   mute notify
digest                    4      1      1
mute                      1      6      0
notify                    0      0      5

--- confusion matrix: message_type ---
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               3               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               1               0               0               0               0               0               0               0               0
payment                            0               0               0               0               1               0               0               0               0               0               0
personal                           0               0               0               0               0               2               0               0               0               0               0
promotion                          0               0               0               0               0               1               3               0               0               0               0
scam                               0               0               0               0               0               0               0               3               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               1               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               2

--- per-row results ---
synth_001     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=payment          exp=payment         
synth_002     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_003     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_004     action[MISS] pred=mute    exp=digest   type[OK  ] pred=promotion        exp=promotion       
synth_005     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_006     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_007     action[OK  ] pred=mute    exp=mute     type[MISS] pred=forward          exp=greeting        
synth_008     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_009     action[MISS] pred=digest  exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_010     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=personal         exp=personal        
synth_011     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_012     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=forward          exp=forward         
synth_013     action[MISS] pred=notify  exp=digest   type[MISS] pred=personal         exp=unknown         
synth_014     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
synth_015     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=event            exp=event           
synth_016     action[OK  ] pred=digest  exp=digest   type[MISS] pred=personal         exp=promotion       
synth_017     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=personal         exp=personal        
synth_018     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
```

---

## Run 2026-08-08 18:58:38

Source: LLM path (ANTHROPIC_API_KEY set) — 2 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **100.0%**
- message_type: **50.0%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                    0      0      0
mute                      0      0      0
notify                    0      0      2
```

![action confusion matrix](reports/confusion_action_20260808_185838.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               0               0               0               0               0               0               0               0               0               1
forward                            0               0               0               0               0               0               0               0               0               0               0
greeting                           0               0               0               0               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               0               0               0               0               0               0
promotion                          0               0               0               0               0               0               0               0               0               0               0
scam                               0               0               0               0               0               0               0               0               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               1
```

![message_type confusion matrix](reports/confusion_message_type_20260808_185838.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 0.00 | 0.00 | 0.00 | 0 |
| mute | 0.00 | 0.00 | 0.00 | 0 |
| notify | 1.00 | 1.00 | 1.00 | 2 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 0.00 | 0.00 | 0.00 | 0 |
| event | 0.00 | 0.00 | 0.00 | 1 |
| forward | 0.00 | 0.00 | 0.00 | 0 |
| greeting | 0.00 | 0.00 | 0.00 | 0 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 0.00 | 0.00 | 0.00 | 0 |
| promotion | 0.00 | 0.00 | 0.00 | 0 |
| scam | 0.00 | 0.00 | 0.00 | 0 |
| spam | 0.00 | 0.00 | 0.00 | 0 |
| unknown | 0.00 | 0.00 | 0.00 | 0 |
| urgent | 0.50 | 1.00 | 0.67 | 1 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.9-1.0) | 2 | 0.935 | 1.000 | 0.065 |

**Expected Calibration Error (ECE): 0.0650**

![reliability diagram](reports/reliability_diagram_20260808_185838.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.9-1.0) | 2 | 0.935 | 0.500 | 0.435 |

**Expected Calibration Error (ECE): 0.4350**

### Evidence quality

- Rows citing at least one evidence ID: 100.0% (2 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (4 IDs cited total)
- Rows where the sample provides its own expected evidence: 2
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 50.0%
- Exact-match rate with that expected evidence set: 0.0%

### Synthetic (held-out)

```
n = 18 hand-crafted, held-out cases (never used to tune the rules)
action accuracy:       83.3%  (15/18)
message_type accuracy: 83.3%  (15/18)
fully correct (both):  72.2%  (13/18)

--- confusion matrix: action ---
expected \ predicted digest   mute notify
digest                    4      1      1
mute                      1      6      0
notify                    0      0      5

--- confusion matrix: message_type ---
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               3               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               1               0               0               0               0               0               0               0               0
payment                            0               0               0               0               1               0               0               0               0               0               0
personal                           0               0               0               0               0               2               0               0               0               0               0
promotion                          0               0               0               0               0               1               3               0               0               0               0
scam                               0               0               0               0               0               0               0               3               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               1               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               2

--- per-row results ---
synth_001     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=payment          exp=payment         
synth_002     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_003     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_004     action[MISS] pred=mute    exp=digest   type[OK  ] pred=promotion        exp=promotion       
synth_005     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_006     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_007     action[OK  ] pred=mute    exp=mute     type[MISS] pred=forward          exp=greeting        
synth_008     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_009     action[MISS] pred=digest  exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_010     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=personal         exp=personal        
synth_011     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_012     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=forward          exp=forward         
synth_013     action[MISS] pred=notify  exp=digest   type[MISS] pred=personal         exp=unknown         
synth_014     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
synth_015     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=event            exp=event           
synth_016     action[OK  ] pred=digest  exp=digest   type[MISS] pred=personal         exp=promotion       
synth_017     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=personal         exp=personal        
synth_018     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
```

---

## Run 2026-08-08 19:28:45

Source: LLM path (ANTHROPIC_API_KEY set) — 30 messages from `dataset/sample_messages.csv`.

### Accuracy

- action: **96.7%**
- message_type: **76.7%**

### Confusion matrix: action

```
expected \ predicted digest   mute notify
digest                   10      0      1
mute                      0     10      0
notify                    0      0      9
```

![action confusion matrix](reports/confusion_action_20260808_192845.png)

### Confusion matrix: message_type

```
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    3               0               0               0               0               0               0               0               0               0               0
event                              0               3               0               0               0               0               0               0               0               0               1
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               0               2               0               0               0               0               0               0               0
payment                            0               0               0               0               0               0               0               0               0               0               0
personal                           0               0               0               0               0               3               0               0               0               0               1
promotion                          0               0               0               0               0               3               3               0               0               0               0
scam                               0               0               0               0               0               0               0               4               0               0               0
spam                               0               0               0               0               0               0               0               1               0               0               0
unknown                            0               0               0               0               0               0               0               0               0               0               1
urgent                             0               0               0               0               0               0               0               0               0               0               4
```

![message_type confusion matrix](reports/confusion_message_type_20260808_192845.png)

### Per-class metrics: action

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| digest | 1.00 | 0.91 | 0.95 | 11 |
| mute | 1.00 | 1.00 | 1.00 | 10 |
| notify | 0.90 | 1.00 | 0.95 | 9 |

### Per-class metrics: message_type

| label | precision | recall | f1 | support |
|---|---|---|---|---|
| business_update | 1.00 | 1.00 | 1.00 | 3 |
| event | 1.00 | 0.75 | 0.86 | 4 |
| forward | 1.00 | 1.00 | 1.00 | 1 |
| greeting | 1.00 | 1.00 | 1.00 | 2 |
| payment | 0.00 | 0.00 | 0.00 | 0 |
| personal | 0.50 | 0.75 | 0.60 | 4 |
| promotion | 1.00 | 0.50 | 0.67 | 6 |
| scam | 0.80 | 1.00 | 0.89 | 4 |
| spam | 0.00 | 0.00 | 0.00 | 1 |
| unknown | 0.00 | 0.00 | 0.00 | 1 |
| urgent | 0.57 | 1.00 | 0.73 | 4 |

### Confidence calibration (vs action correctness)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 2 | 0.675 | 1.000 | 0.325 |
| [0.7-0.8) | 8 | 0.731 | 1.000 | 0.269 |
| [0.8-0.9) | 2 | 0.805 | 0.500 | 0.305 |
| [0.9-1.0) | 18 | 0.941 | 1.000 | 0.059 |

**Expected Calibration Error (ECE): 0.1493**

![reliability diagram](reports/reliability_diagram_20260808_192845.png)

### Confidence calibration (vs full-row correctness: action AND message_type)

| bucket | n | mean confidence | accuracy | gap |
|---|---|---|---|---|
| [0.6-0.7) | 2 | 0.675 | 1.000 | 0.325 |
| [0.7-0.8) | 8 | 0.731 | 0.875 | 0.144 |
| [0.8-0.9) | 2 | 0.805 | 0.000 | 0.805 |
| [0.9-1.0) | 18 | 0.941 | 0.778 | 0.163 |

**Expected Calibration Error (ECE): 0.2113**

### Evidence quality

- Rows citing at least one evidence ID: 93.3% (30 total rows)
- Cited IDs that exist in `message_history.csv`: 100.0% (47 IDs cited total)
- Rows where the sample provides its own expected evidence: 28
- Mean overlap with that expected evidence (`|predicted ∩ expected| / |expected|`): 64.3%
- Exact-match rate with that expected evidence set: 25.0%

### Synthetic (held-out)

```
n = 18 hand-crafted, held-out cases (never used to tune the rules)
action accuracy:       83.3%  (15/18)
message_type accuracy: 83.3%  (15/18)
fully correct (both):  72.2%  (13/18)

--- confusion matrix: action ---
expected \ predicted digest   mute notify
digest                    4      1      1
mute                      1      6      0
notify                    0      0      5

--- confusion matrix: message_type ---
expected \ predicted business_update           event         forward        greeting         payment        personal       promotion            scam            spam         unknown          urgent
business_update                    0               0               0               0               0               0               0               0               0               0               0
event                              0               3               0               0               0               0               0               0               0               0               0
forward                            0               0               1               0               0               0               0               0               0               0               0
greeting                           0               0               1               0               0               0               0               0               0               0               0
payment                            0               0               0               0               1               0               0               0               0               0               0
personal                           0               0               0               0               0               2               0               0               0               0               0
promotion                          0               0               0               0               0               1               3               0               0               0               0
scam                               0               0               0               0               0               0               0               3               0               0               0
spam                               0               0               0               0               0               0               0               0               0               0               0
unknown                            0               0               0               0               0               1               0               0               0               0               0
urgent                             0               0               0               0               0               0               0               0               0               0               2

--- per-row results ---
synth_001     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=payment          exp=payment         
synth_002     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_003     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_004     action[MISS] pred=mute    exp=digest   type[OK  ] pred=promotion        exp=promotion       
synth_005     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_006     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=urgent           exp=urgent          
synth_007     action[OK  ] pred=mute    exp=mute     type[MISS] pred=forward          exp=greeting        
synth_008     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_009     action[MISS] pred=digest  exp=mute     type[OK  ] pred=promotion        exp=promotion       
synth_010     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=personal         exp=personal        
synth_011     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=scam             exp=scam            
synth_012     action[OK  ] pred=mute    exp=mute     type[OK  ] pred=forward          exp=forward         
synth_013     action[MISS] pred=notify  exp=digest   type[MISS] pred=personal         exp=unknown         
synth_014     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
synth_015     action[OK  ] pred=notify  exp=notify   type[OK  ] pred=event            exp=event           
synth_016     action[OK  ] pred=digest  exp=digest   type[MISS] pred=personal         exp=promotion       
synth_017     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=personal         exp=personal        
synth_018     action[OK  ] pred=digest  exp=digest   type[OK  ] pred=event            exp=event           
```

---
