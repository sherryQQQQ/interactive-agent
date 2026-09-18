"""Metadata only: listing experiments must never import a paid provider."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Experiment:
    name: str
    module: str
    question: str
    status: str
    spec: str
    inputs: tuple[str, ...]
    replay_supported: bool

    def as_dict(self):
        return asdict(self)


EXPERIMENTS = {
    item.name: item for item in (
        Experiment("handoff", "graphrag.eval.mediq_handoff_holdout",
                   "Compare transcript, handoff, and handoff with cited turns",
                   "historical-results", "mediq_handoff_holdout.json",
                   ("MediQ source", "Textbooks BM25 index"), True),
        Experiment("compaction", "graphrag.eval.mediq_compaction_p1",
                   "Compare five diagnostic context representations",
                   "historical-results", "mediq_compaction_p1.json",
                   ("MediQ source", "Textbooks BM25 index"), True),
        Experiment("information-gain", "graphrag.eval.mediq_ig",
                   "Compare freeform, oracle and imagined-answer question selection",
                   "fairness-v2-offline-validation", "mediq_ig_selection.json",
                   ("MediQ source", "Textbooks BM25 index"), True),
        Experiment("distractors", "graphrag.eval.mediq_phase2",
                   "Compare context formats under irrelevant turns",
                   "experimental-not-end-to-end-validated", "mediq_phase2_spec.json",
                   ("MediQ source", "Textbooks BM25 index", "Phase 1 local results"), False),
    )
}
