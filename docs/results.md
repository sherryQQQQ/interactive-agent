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
