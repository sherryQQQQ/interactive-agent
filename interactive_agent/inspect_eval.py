"""Inspect AI task for the deterministic clinical-agent fixture.

This is deliberately a contract test, not a medical-quality benchmark. It
proves that the project's trajectories, budgets, and custom scores can be
represented in a standard evaluation log without making a model call.
"""

from __future__ import annotations

import json
from typing import Any

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

from graphrag.agent.clinical_demo import run_demo


EXPECTED_TRACE = (
    "interview_ask",
    "patient_tool_success",
    "interview_ask",
    "patient_tool_success",
    "interview_finalize",
    "retrieval_tool_success",
    "diagnosed",
    "safety_approve",
)


def contract_checks(result: dict[str, Any]) -> dict[str, bool]:
    """Return explicit, independently reportable fixture-contract checks."""
    max_questions = result.get("max_questions")
    questions_asked = result.get("questions_asked")
    return {
        "answered": result.get("status") == "answered",
        "within_question_budget": (
            isinstance(questions_asked, int)
            and isinstance(max_questions, int)
            and questions_asked <= max_questions
        ),
        "expected_trajectory": tuple(result.get("trace", ())) == EXPECTED_TRACE,
        "patient_tool_success": (
            result.get("patient_tool_calls") == result.get("patient_tool_successes") == 2
        ),
        "retrieval_tool_success": (
            result.get("retrieval_tool_calls")
            == result.get("retrieval_tool_successes")
            == 1
        ),
        "grounded_handoff": bool(
            result.get("diagnostic_packet", {}).get("handoff", {}).get("facts")
            and result.get("diagnostic_packet", {}).get("evidence")
        ),
    }


@solver
def scripted_clinical_agent() -> Solver:
    async def solve(state: TaskState, _generate: Generate) -> TaskState:
        result = run_demo()
        checks = contract_checks(result)
        for index, event in enumerate(result["trace"]):
            transcript().info(
                {"sequence": index, "event": event}, source="clinical-agent"
            )
        state.store.set("clinical_result", result)
        state.store.set("contract_checks", checks)
        state.output = ModelOutput.from_content(
            model="scripted/clinical-fixture",
            content=json.dumps(
                {
                    "status": result["status"],
                    "action": result["action"],
                    "questions_asked": result["questions_asked"],
                    "checks": checks,
                },
                sort_keys=True,
            ),
        )
        state.completed = True
        return state

    return solve


@scorer(metrics=[accuracy()])
def clinical_contract_scorer():
    async def score(state: TaskState, _target) -> Score:
        checks = state.store.get("contract_checks")
        passed = bool(checks) and all(checks.values())
        failed = sorted(name for name, value in (checks or {}).items() if not value)
        return Score(
            value=CORRECT if passed else INCORRECT,
            answer="pass" if passed else "fail",
            explanation=(
                "All scripted orchestration contracts passed."
                if passed
                else f"Failed contracts: {', '.join(failed)}"
            ),
            metadata={"checks": checks or {}},
        )

    return score


@task
def clinical_scripted_contract() -> Task:
    return Task(
        dataset=[
            Sample(
                id="acute-chest-discomfort-fixture",
                input="Run the deterministic clinical handoff fixture.",
                target="pass",
                metadata={"fixture": True, "medical_quality_benchmark": False},
            )
        ],
        solver=scripted_clinical_agent(),
        scorer=clinical_contract_scorer(),
        model="mockllm/model",
        message_limit=1,
        token_limit=1,
        turn_limit=1,
        metadata={
            "purpose": "orchestration-contract-test",
            "provider_calls_expected": 0,
        },
    )
