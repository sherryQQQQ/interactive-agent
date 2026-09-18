"""Offline audit of observable action-boundary failures in saved experiments.

The audit reports events, not inferred root causes. It never calls a model and
never emits case text or raw provider output.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


DEFERRAL_ACTIONS = frozenset({"abstain", "clarify", "escalate"})


def _load_results(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = path.read_bytes()
    document = json.loads(payload)
    results = document.get("results") if isinstance(document, dict) else None
    if not isinstance(results, list):
        raise ValueError(f"Expected a top-level results list: {path}")
    if not all(isinstance(record, dict) for record in results):
        raise ValueError(f"Every result must be an object: {path}")
    return results, hashlib.sha256(payload).hexdigest()


def audit_revisions(path: Path, *, system: str = "textbooks-agent") -> dict[str, Any]:
    """Count observable revision outcomes in an exact-choice experiment."""
    results, digest = _load_results(path)
    records = [record for record in results if record.get("system") == system]
    if not records:
        raise ValueError(f"No records for system {system!r}: {path}")
    known = [r for r in records if type(r.get("initial_correct")) is bool]
    initially_correct = [r for r in known if r["initial_correct"]]
    initially_wrong = [r for r in known if not r["initial_correct"]]
    revised_correct = [r for r in initially_correct if int(r.get("retry_count", 0)) > 0]
    revised_wrong = [r for r in initially_wrong if int(r.get("retry_count", 0)) > 0]
    harmful = sum(not bool(r.get("correct")) for r in revised_correct)
    recovered = sum(bool(r.get("correct")) for r in revised_wrong)
    return {
        "source_sha256": digest,
        "system": system,
        "attempted": len(records),
        "initial_outcome_observed": len(known),
        "initial_outcome_missing": len(records) - len(known),
        "initially_correct": len(initially_correct),
        "initially_wrong": len(initially_wrong),
        "initially_correct_sent_to_retry": len(revised_correct),
        "initially_wrong_sent_to_retry": len(revised_wrong),
        "harmful_revision": harmful,
        "harmful_revision_rate_given_correct_retry": (
            harmful / len(revised_correct) if revised_correct else None
        ),
        "retry_recovery": recovered,
        "retry_recovery_rate_given_wrong_retry": (
            recovered / len(revised_wrong) if revised_wrong else None
        ),
        "final_correct": sum(bool(r.get("correct")) for r in records),
        "cases_with_retry": sum(int(r.get("retry_count", 0)) > 0 for r in records),
        "provider_or_pipeline_errors": sum(r.get("status") == "error" for r in records),
    }


def audit_routes(path: Path) -> dict[str, Any]:
    """Compare emitted and benchmark-expected actions by system."""
    results, digest = _load_results(path)
    required = {"system", "expected_action", "expected_answerable", "action"}
    if any(not required.issubset(record) for record in results):
        raise ValueError(f"Routing records are missing required fields: {path}")
    systems: dict[str, Any] = {}
    for system in sorted({str(record["system"]) for record in results}):
        records = [record for record in results if str(record["system"]) == system]
        actions = Counter(str(r["action"]) for r in records)
        expected = Counter(str(r["expected_action"]) for r in records)
        answerable = [r for r in records if r["expected_answerable"] is True]
        unanswerable = [r for r in records if r["expected_answerable"] is False]
        clarification = [r for r in records if r["expected_action"] == "clarify"]
        systems[system] = {
            "attempted": len(records),
            "expected_actions": dict(sorted(expected.items())),
            "emitted_actions": dict(sorted(actions.items())),
            "exact_action_matches": sum(r["action"] == r["expected_action"] for r in records),
            "false_deferrals_on_answerable": sum(
                r["action"] in DEFERRAL_ACTIONS for r in answerable
            ),
            "answerable_denominator": len(answerable),
            "answers_on_unanswerable": sum(r["action"] == "answer" for r in unanswerable),
            "unanswerable_denominator": len(unanswerable),
            "missed_clarifications": sum(r["action"] != "clarify" for r in clarification),
            "clarification_denominator": len(clarification),
            "invalid_actions": actions.get("invalid", 0),
            "records_with_gate_errors": sum(bool(r.get("gate_errors")) for r in records),
            "records_with_tool_errors": sum(bool(r.get("tool_errors")) for r in records),
        }
    return {"source_sha256": digest, "systems": systems}


def run_boundary_audit(
    *, revision_v1: Path, revision_v2: Path, routing: Path
) -> dict[str, Any]:
    """Build a privacy-preserving aggregate report from local saved traces."""
    sources = {"revision_v1": revision_v1, "revision_v2": revision_v2, "routing": routing}
    missing = [name for name, path in sources.items() if not path.is_file()]
    report: dict[str, Any] = {
        "audit_version": "boundary-observations-v1",
        "model_calls": 0,
        "estimated_cost_usd": 0.0,
        "status": "incomplete" if missing else "complete",
        "missing_sources": missing,
        "limitations": [
            "Different experiments and populations are reported separately and cannot be pooled.",
            "Events are observable associations, not adjudicated causal root causes.",
            "Expected actions come from benchmark contracts, not independent clinical review.",
            "Schema and gate errors are separated from intentional deferral decisions.",
        ],
    }
    if revision_v1.is_file():
        report["revision_v1"] = audit_revisions(revision_v1)
    if revision_v2.is_file():
        report["revision_v2"] = audit_revisions(revision_v2)
    if routing.is_file():
        report["routing"] = audit_routes(routing)
    return report
