# Research protocol and audit

For context-format experiments hold case, observations, retriever, corpus,
generation instruction and model fixed. For interview-policy experiments hold
patient simulator and question limit fixed and report compute differences:
equal question count is not equal token or call budget.

Freeze development/holdout IDs, prompts, routing rules and primary outcomes.
Do not tune on holdout failures and describe the rerun as untouched. Changes
require a new protocol version; preserve previous results as historical.

Report attempted, valid and excluded cases; accuracy and Wilson 95% intervals;
paired wins/losses and exact McNemar. Predefine multiple-comparison handling.
Report failure reasons, latency percentiles, tokens, cost and provider errors.
Non-significant differences do not demonstrate equivalence.

## Interpretation limits

- Existing source IDs do not prove semantic faithfulness.
- Shared errors across formats do not identify missing information as the cause.
- One imagined answer is not expected information gain over an answer distribution.
- Lower model-reported entropy may reflect confident errors.
- Oracle probing is privileged access, not a guaranteed accuracy ceiling.
- Simulated patients cannot establish clinical safety or patient benefit.
- Historical complete-case accuracy is not all-attempted success rate.

The old frozen IG spec remains for audit. The fairness-v2 amendment in
`experiments.md` supersedes its call estimates and patient-state implementation.
Partial-budget diagnosis analysis is deferred; it needs the corresponding
diagnosis calls, not just truncated interview traces.

Before publication: data/license review, leakage audit, untouched holdout,
sensitivity analysis and manual error review. Clinical claims require appropriate
clinical expertise. A platform refactor alone is not a research contribution.
