# Roadmap: action selection under incomplete information

## Research question

Given the observed dialogue, available tools and remaining budgets, when should
an agent answer, ask for a decisive missing fact, retrieve evidence, or stop and
defer? The goal is to measure decision quality and unnecessary work, not simply
increase the number of agent steps. Medical simulation is the first testbed;
cross-domain generalization is not an established result.

## Why this follows from existing experiments

Historical traces show 11 regressions among 14 initially correct drafts sent
through reflection, missed safe deferral on four missing-information cases,
and severe over-abstention in the external Agent v3 stress test. These studies
use different tasks and denominators and cannot be pooled into a claim that
most agent errors arise from one cause. Schema failures routed to abstention
must also be separated from intentional uncertainty decisions.

## Next steps, in order

1. **Offline trace audit.** Reuse local checkpoints. Define a labeling rubric
   separating knowledge/retrieval gaps, missing patient facts, incorrect action
   selection, harmful revision and tool/schema errors. Allow multiple labels
   and an unknown category; report missing traces and denominators. Mark manual
   versus automated labels and do not treat explanations as causal proof.
2. **Extract minimal contracts.** Define observation/state, provenance, actions,
   tool results and separate dialogue/compute budgets. Keep medical required
   facts, patient simulation and domain safety policy in the adapter. Preserve
   old commands and checkpoint identities during migration.
3. **Offline multi-turn fixtures.** Test incomplete facts, fact completion,
   contradiction, repeated questions, tool failure and budget exhaustion. Check
   state updates and allowed actions after each turn. Synthetic fixtures test
   engineering contracts, not clinical accuracy.
4. **Controlled development pilot.** Compare direct answering, existing fixed
   workflows and a task-aware action policy. Hold model, tools and case inputs
   fixed. Evaluate at matched compute and interaction budgets where feasible;
   otherwise report resource curves instead of claiming equal cost. Freeze the
   protocol before an untouched holdout. Inspect call estimates and remaining
   cumulative API budget before any paid execution.

Candidate outcomes: action correctness, inappropriate-answer and false-deferral
rates, clarification recovery, final task accuracy, unnecessary tool/revision
steps, tokens, latency and estimated cost. Action labels need a defensible task
contract; clinical labels require appropriate independent review. Do not define
success merely as agreeing with the new router's own rules.

The information-gain experiment remains a candidate *question selection*
baseline after the decision to ask. It is not the main research claim. Do not
start its full holdout before the audit establishes the relevant failure mode.

## Scope and release boundaries

The current release is a platform foundation, not a generic agent framework or
a clinically validated assistant. No training or cross-domain experiments are
implied. Keep original GraphRAG work in its original repository; use
`interactive-agent` for this research direction. Do not publish raw dialogue,
external data, secrets or private interview notes.
