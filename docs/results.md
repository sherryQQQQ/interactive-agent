# Results and limits

These are historical observations, not new experiments from this refactor.
Raw checkpoints are local, not included in a fresh checkout. The stage archive
and compression analysis retain the original analysis; the protocol audit
governs its interpretation.

| Study | Comparison | Finding |
|---|---|---|
| MIRAGE matched corpus, 100 | RAG / Agent v2 | 78% / 76%; no demonstrated Agent gain |
| MediQ pilot, 30 | Handoff / transcript | 25/30 / 22/30; exact McNemar p=0.25 |
| MediQ compaction, 91 evaluable of 100 | Handoff / transcript | 54/91 / 52/91; p=0.73 |

Nine cases were excluded from the historical compaction diagnosis comparison.
Counting these as unsuccessful attempts gives 54/100 and 52/100, a different
estimand. Future reports should present both denominators. Structured handoff
used about 20% more diagnostic input tokens than the transcript; this was not a
demonstrated compression benefit.

Reference validity is not semantic faithfulness. These results do not establish
that handoff improves accuracy or that information acquisition is the dominant
bottleneck. IG fairness-v2 has offline tests only; earlier calls cannot be
relabelled as revised-protocol results. Distractor studies remain experimental.
No GPU-training results or clinical validation are available.

## Standard checkpoint replay

The local Agent v2 MIRAGE checkpoint was replayed through Inspect AI as 100
paired samples (source SHA-256 prefix `5599405a677b`). The replay reproduced
closed-book 84%, textbooks RAG 78% and textbooks Agent 76%, with no non-empty
model-usage records. This is a schema/pairing migration check, not a new model
experiment and not additional evidence for or against the Agent.

## Offline action-boundary audit

`interactive-agent audit-boundaries` recomputes the following aggregates from
ignored local result files with zero model calls. It fingerprints each source;
no case text or raw output is written to the report.

| Revision experiment | Correct drafts retried → harmed | Wrong drafts retried → recovered |
|---|---:|---:|
| Agent v1, MIRAGE n=100 | 11/14 | 0/7 |
| Agent v2, MIRAGE n=100 | 0/0 (no correct draft retried) | 1/3 |

The external 36-case routing stress test produced these observable actions:

| System | Exact action | False deferral on 18 answerable | Answer on 18 unanswerable | Invalid | Gate-error records |
|---|---:|---:|---:|---:|---:|
| Direct RAG | 13/36 | 8/18 | 10/18 | 4 | 0 |
| Agent v2 | 11/36 | 7/18 | 9/18 | 8 | 0 |
| Agent v3 | 12/36 | 14/18 | 6/18 | 0 | 7 |

All systems missed the three expected clarification actions. Agent v3 removed
invalid action formats and reduced answers on unanswerable cases, but shifted
strongly toward deferral. Seven of its records contained gate errors. These
figures describe benchmark-contract mismatches, not clinically adjudicated
errors, and the MIRAGE and routing populations must not be pooled.
