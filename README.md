# Interactive Agent

**A research platform for action selection in information-incomplete,
multi-turn tasks, with simulated medical tasks as the first testbed.**

The research direction is to study when an agent should answer, clarify,
retrieve evidence, or stop/defer. Current implementations include a bounded
clinical LangGraph workflow, handoff and question-selection experiments,
offline fixtures, and checkpointed Gemini adapters. A domain-independent
decision policy and cross-domain evaluation are **planned, not implemented
or validated**.

Research software for simulated cases, not a clinical service. The
[original GraphRAG project](https://github.com/sherryQQQQ/RAG_Medical_Diagnosis)
contains the retrieval comparison that motivated this work.

## From retrieval to action selection

| Stage | Main question | Status |
|---|---|---|
| Vector RAG / GraphRAG | Can the system retrieve useful evidence? | Legacy retrieval study, separate original repository |
| Medical QA Agent | Does reflection or structured handoff improve answers? | Implemented; mixed/negative historical findings |
| Interactive decision research | Given the current observations, should the agent answer, ask, retrieve, or stop? | New research direction; offline audit first |

A conversation turn with a user is different from an internal reflection or
tool-call iteration. Both budgets must be tracked. Medical rules and patient
tools belong in the domain adapter; general state, provenance, budgets and
action evaluation are candidates for a shared core. Current clinical modules
have not yet been fully separated into that architecture.

Historical traces show harmful reflection, missed clarification and excessive
deferral. They motivate an action-boundary audit; they do **not** establish that
most errors are boundary errors or that a new router will improve performance.
See [the research roadmap](docs/roadmap.md) for the next controlled steps.

`interactive-agent audit-boundaries` reads ignored local results and prints
aggregate counts and source hashes only. It makes zero model calls. Missing
sources are reported rather than downloaded. Add
`--output runs/boundary-audit.json` to save a report; existing files are never
overwritten.

## Start in five minutes

Python 3.11–3.13. No GPU, API key, or downloaded medical data is needed for
the fixture demo. Run from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
interactive-agent catalog
interactive-agent doctor
interactive-agent demo --output runs/demo
interactive-agent report runs/demo
interactive-agent audit-boundaries
python -m pytest tests graphrag/agent/test_clinical_agent.py graphrag/eval/test_mediq_ig.py
```

The demo uses **scripted models and a synthetic patient**, not an actual LLM.
It writes a manifest, a complete workflow trace, and a report. It demonstrates
execution and provenance validation, not diagnostic accuracy. Existing run
directories are never overwritten.

For the full legacy-and-platform test suite, install the optional retrieval
dependencies with `pip install -e '.[dev,retrieval]'`, then run `python -m pytest`.

## Standard evaluation logs

The first [Inspect AI](https://inspect.aisi.org.uk/) adapter maps the scripted
clinical workflow to a standard task, solver, event trajectory and custom
scorer. It checks six orchestration contracts: termination, question budget,
expected action sequence, patient-tool success, retrieval-tool success and a
grounded handoff. It makes no provider/model calls and is **not** evidence of
medical answer quality.

```bash
python -m pip install -e '.[dev,inspect]'
inspect eval interactive_agent/inspect_eval.py@clinical_scripted_contract \
  --display none --log-dir runs/inspect-contract
inspect view --log-dir runs/inspect-contract
```

Inspect is optional so the core package remains small. Legacy paid experiment
adapters have not yet been migrated; their checkpoint identities and historical
outputs remain unchanged.

An offline MIRAGE replay adapter validates strict three-arm pairing and writes
one Inspect sample per case. It excludes questions, passages and raw model
answers from the new log:

```bash
inspect eval interactive_agent/inspect_checkpoint_eval.py@mirage_paired_checkpoint \
  -T results_path=graphrag/eval/external/mirage/stage5j_agent_v2_scaled.json \
  --display none --log-dir runs/inspect-stage5j-v2-replay
```

The source file remains ignored and local. Replaying it creates zero provider
calls; missing, duplicate or unmatched system records fail before evaluation.

## Research workflows

| Question | Experiment | Status |
|---|---|---|
| Does reflection help fixed-context QA? | MIRAGE matched RAG/Agent | Historical results |
| Does handoff format affect answers? | MediQ handoff and five-arm compaction | Historical results |
| Does question selection help? | MediQ information gain | Offline fairness fixes; no validated result |
| Does irrelevant context affect handoff? | MediQ distractors | Implemented; not validated end to end |

```text
Case → interview policy → patient tool → updated patient state
                            ↑                  │
                            └── question budget┘
         → evidence retrieval → diagnostic context → answer / safety gate
         → traces + checkpoint + paired evaluation
```

Model calls, patient responses, evidence retrieval, and safety validation are
injected dependencies. See [extension points](docs/architecture.md).

## Run an experiment

```bash
# Offline metadata: no credentials or downloaded data needed
interactive-agent plan information-gain

# Full plan: requires local benchmark source
interactive-agent experiment information-gain -- --set dev --dry-run

# Replay a local checkpoint without creating provider calls
interactive-agent experiment handoff -- --reuse-only

# Explicit provider execution; inspect the plan first (incurs charges)
interactive-agent experiment information-gain -- --set dev --execute
```

External experiments run from an **editable checkout** with separately
prepared data. See the [experiment guide](docs/experiments.md) for inputs,
frozen selections, budgets, and replay limitations. Checkpoints are local,
not distributed. A fresh clone cannot reconstruct published results without
the corresponding data and checkpoints.

## Evidence

| Experiment | Observed result | Interpretation |
|---|---|---|
| MIRAGE, 100 cases | Direct RAG 78%, Agent v2 76% | No demonstrated Agent advantage |
| MediQ, 30 cases | Handoff 25/30, transcript 22/30; p=0.25 | Pilot signal, not confirmation |
| MediQ compaction, 91/100 evaluable | Handoff 59.3%, transcript 57.1%; p=0.73 | No significant difference; 9 failures excluded from historical diagnosis analysis |

Structured handoff used **20% more diagnostic input tokens** in the compaction
study. Valid source IDs do not establish semantic faithfulness. See
[results and limitations](docs/results.md) for denominators and interpretation.

## Project map

| Location | Responsibility |
|---|---|
| `interactive_agent/` | Public CLI, registry, run artifacts, paired scoring, Inspect task |
| `graphrag/agent/clinical_*` | Typed state, injected tools, LangGraph workflow |
| `graphrag/eval/mediq_*` | Research adapters and frozen selections |
| `graphrag/eval/checkpointed_gemini.py` | Checkpoints and budget controls |
| `tests/`, `graphrag/**/test_*.py` | Offline scientific and platform tests |
| `docs/history/` | Archived development stages |
| `final/`, `graphrag/kg/`, `graphrag/retrieval/` | Legacy retrieval implementation |

The `graphrag` namespace preserves historical commands. Start new workflows
with `interactive-agent`.

- [Experiments](docs/experiments.md) · [Architecture](docs/architecture.md)
- [Protocol and audit](docs/research-protocol.md) · [Results](docs/results.md)
- [Docker](docs/docker.md) · [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md) · [Data provenance](THIRD_PARTY.md)

The paid adapter supports Gemini. Local open-weight serving and H100 training
are future extensions, not implemented capabilities.
