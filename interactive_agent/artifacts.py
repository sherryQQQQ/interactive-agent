"""Versioned, inspectable offline run artifacts; no model calls."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from interactive_agent import __version__


def summarize_trace(trace):
    return {
        "kind": "scripted-fixture-not-a-quality-benchmark",
        "status": trace.get("status"),
        "questions_asked": trace.get("questions_asked", 0),
        "trace": trace.get("trace", []),
        "model_calls": 0,
        "estimated_cost_usd": 0.0,
    }


def write_run(directory, trace):
    directory = Path(directory)
    payload = json.dumps(trace, indent=2, ensure_ascii=False) + "\n"
    report = summarize_trace(trace)
    manifest = {
        "format_version": 1,
        "platform_version": __version__,
        "experiment": "offline-clinical-demo",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trace_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "provider": "scripted",
    }
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "trace.json").write_text(payload, encoding="utf-8")
    for filename, data in (("manifest.json", manifest), ("report.json", report)):
        (directory / filename).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return report


def read_report(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1:
        raise ValueError("Unsupported run artifact version")
    payload = (directory / "trace.json").read_bytes()
    if hashlib.sha256(payload).hexdigest() != manifest["trace_sha256"]:
        raise ValueError("Trace digest mismatch: artifact was modified")
    return summarize_trace(json.loads(payload))
