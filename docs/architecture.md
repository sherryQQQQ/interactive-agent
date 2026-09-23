# Architecture and extension points

Target direction: a shared multi-turn state/action layer with domain-specific
tools and policies. This separation is planned in [the roadmap](roadmap.md);
the current runtime remains primarily clinical and does not yet implement a
domain-independent action selector.

The public `interactive_agent` package exposes experiment metadata, explicit
execution modes, offline artifacts and paired scoring. Scientific runners remain
in `graphrag.eval`, preserving historical commands and checkpoint identities.
This is a staged migration, not a claim that all runners use one artifact schema.

`interactive_agent.inspect_eval` is the first integration with Inspect AI. The
scripted fixture is represented as a one-sample `Task`; the LangGraph run is an
Inspect solver, each agent action is a transcript event, and a deterministic
custom scorer checks orchestration contracts. The log records zero model usage.
This validates the evaluation seam only. It does not score diagnosis quality,
and the historical Gemini runners continue using their original checkpoints.

`inspect_checkpoint_eval` is the first historical-results migration. It groups
the three MIRAGE arms by case before scoring, rejects incomplete or duplicate
pairs, fingerprints the source and copies only normalized outcome/resource
fields. Benchmark questions, retrieved text and raw responses are deliberately
excluded from the Inspect log. This avoids both data redistribution and the
false independence created by treating three paired arms as unrelated samples.

## Agent layer

`graphrag.agent.clinical_handoff` defines typed facts, source turns, handoffs and
diagnostic packets. `clinical_agent` builds the bounded LangGraph workflow.
`clinical_tools.ClinicalTools` injects patient interaction, evidence retrieval,
diagnosis and safety validation. See `clinical_demo.run_demo` for a complete
dependency-injection example with no network calls.

An interview updates state; it does not train model weights. A question budget
bounds interaction. Source-ID validation does not establish semantic support.
Safety rules are experimental, not clinically validated triage.

## Adding an experiment

1. Implement offline planning and guarded execution in a runner.
2. Register its module, frozen spec, input requirements and replay support in
   `interactive_agent.registry`.
3. Inject deterministic tools for regression tests before paid execution.
4. Record attempted cases, failures, model identity and costs.
5. Reset patient state per arm; freeze selections and version protocol changes.

The Gemini adapter checkpoints calls and enforces per-run budgets. Local model
serving, cluster scheduling and cross-run global billing accounting are not
implemented. Cumulative spending must be checked separately.

## Artifacts

The offline demo writes `manifest.json`, `trace.json` and `report.json` into a
new directory. The manifest identifies the format and hashes the trace. Loading
checks that hash and recomputes the report. This detects accidental modification,
not malicious tampering. External adapters retain their historical JSON schemas.
