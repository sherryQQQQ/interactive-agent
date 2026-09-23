"""Zero-call Inspect replay for paired MIRAGE checkpoint results.

The adapter intentionally logs normalized outcomes and telemetry, not benchmark
questions, retrieved passages, or raw provider responses.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

try:
    from inspect_ai import Task, task
    from inspect_ai.dataset import Sample
    from inspect_ai.log import transcript
    from inspect_ai.model import ModelOutput
    from inspect_ai.scorer import CORRECT, INCORRECT, Score, accuracy, scorer
    from inspect_ai.solver import Generate, Solver, TaskState, solver
except ImportError as exc:  # pragma: no cover - exercised without the extra
    raise ImportError(
        "Inspect AI support is optional; install with pip install -e '.[inspect]'"
    ) from exc


DEFAULT_SYSTEMS = ("closed-book", "textbooks-rag", "textbooks-agent")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_record(record: dict[str, Any]) -> dict[str, Any]:
    """Keep outcome/resource fields only; never copy prompts or raw answers."""
    return {
        "system": record["system"],
        "correct": record["correct"],
        "status": record.get("status"),
        "prediction": record.get("prediction"),
        "gold_choice": record.get("gold_choice"),
        "initial_correct": record.get("initial_correct"),
        "retry_count": record.get("retry_count", 0),
        "reflection_approved": record.get("reflection_approved"),
        "provider_request_count": record.get("provider_request_count"),
        "latency_s": record.get("latency_s"),
        "retrieval_latency_s": record.get("retrieval_latency_s"),
        "input_tokens": record.get("input_tokens"),
        "output_tokens": record.get("output_tokens"),
        "total_tokens": record.get("total_tokens"),
        "tool_error_count": len(record.get("tool_errors") or []),
    }


def load_paired_samples(
    results_path: str | Path,
    systems: Sequence[str] = DEFAULT_SYSTEMS,
) -> tuple[list[Sample], dict[str, Any]]:
    """Validate a complete paired checkpoint and create privacy-minimal samples."""
    path = Path(results_path).expanduser().resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("results")
    if not isinstance(records, list) or not records:
        raise ValueError("Checkpoint must contain a non-empty results array")
    systems = tuple(systems)
    if not systems or len(set(systems)) != len(systems):
        raise ValueError("Systems must be non-empty and unique")

    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    case_sets = {system: set() for system in systems}
    for record in records:
        system = record.get("system")
        if system not in case_sets:
            continue
        case_id = record.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"Missing case_id for system {system}")
        if type(record.get("correct")) is not bool:
            raise ValueError(f"Missing boolean correctness for {case_id}/{system}")
        key = (case_id, system)
        if key in indexed:
            raise ValueError(f"Duplicate result for {case_id}/{system}")
        indexed[key] = record
        case_sets[system].add(case_id)

    reference = case_sets[systems[0]]
    if not reference:
        raise ValueError(f"No records found for {systems[0]}")
    for system in systems[1:]:
        if case_sets[system] != reference:
            missing = sorted(reference - case_sets[system])
            extra = sorted(case_sets[system] - reference)
            raise ValueError(
                f"Unmatched cases for {system}: missing={missing[:5]}, extra={extra[:5]}"
            )

    samples = []
    for case_id in sorted(reference):
        first = indexed[(case_id, systems[0])]
        arms = {
            system: _normalized_record(indexed[(case_id, system)])
            for system in systems
        }
        samples.append(
            Sample(
                id=case_id,
                input=f"Replay normalized paired outcomes for case {case_id}.",
                target="stored-checkpoint",
                metadata={
                    "case_id": case_id,
                    "dataset": first.get("dataset"),
                    "arms": arms,
                },
            )
        )
    source = {
        "path_name": path.name,
        "sha256": _sha256(path),
        "case_count": len(samples),
        "systems": list(systems),
        "provider_calls_expected": 0,
    }
    return samples, source


@solver
def checkpoint_replay_solver() -> Solver:
    async def solve(state: TaskState, _generate: Generate) -> TaskState:
        arms = state.metadata["arms"]
        for system, record in arms.items():
            transcript().info(
                {
                    "event": "checkpoint_replay",
                    "system": system,
                    "status": record["status"],
                    "correct": record["correct"],
                    "retry_count": record["retry_count"],
                    "tool_error_count": record["tool_error_count"],
                },
                source="mirage-checkpoint",
            )
        state.output = ModelOutput.from_content(
            model="scripted/checkpoint-replay",
            content=json.dumps(
                {
                    system: {
                        "correct": record["correct"],
                        "status": record["status"],
                    }
                    for system, record in arms.items()
                },
                sort_keys=True,
            ),
        )
        state.completed = True
        return state

    return solve


def _metric_map(systems: Sequence[str]):
    return {system: [accuracy()] for system in systems}


@scorer(metrics=_metric_map(DEFAULT_SYSTEMS))
def paired_checkpoint_scorer():
    async def score(state: TaskState, _target) -> Score:
        arms = state.metadata["arms"]
        return Score(
            value={
                system: CORRECT if record["correct"] else INCORRECT
                for system, record in arms.items()
            },
            answer="stored-checkpoint",
            explanation="Replayed exact-choice correctness from the saved checkpoint.",
            metadata={
                "initial_correct": {
                    system: record["initial_correct"] for system, record in arms.items()
                },
                "retry_count": {
                    system: record["retry_count"] for system, record in arms.items()
                },
            },
        )

    return score


@task
def mirage_paired_checkpoint(
    results_path: str,
) -> Task:
    samples, source = load_paired_samples(results_path)
    return Task(
        dataset=samples,
        solver=checkpoint_replay_solver(),
        scorer=paired_checkpoint_scorer(),
        model="mockllm/model",
        message_limit=1,
        token_limit=1,
        turn_limit=1,
        metadata={"purpose": "paired-checkpoint-replay", "source": source},
    )
