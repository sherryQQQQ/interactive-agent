"""Safe public commands; external experiments are lazy-loaded and explicit."""
import argparse
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import sqlite3
import sys

from interactive_agent.registry import EXPERIMENTS


def doctor():
    packages = {}
    for name in ("langgraph", "langchain-core", "langchain-google-genai", "python-dotenv", "PyYAML"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    with sqlite3.connect(":memory:") as conn:
        try:
            conn.execute("CREATE VIRTUAL TABLE probe USING fts5(text)")
            fts5 = True
        except sqlite3.OperationalError:
            fts5 = False
    return {"python": sys.version.split()[0], "packages": packages, "sqlite_fts5": fts5,
            "ready": all(packages.values()) and fts5,
            "network_calls": 0, "note": "Does not test credentials or external data"}


def dispatch(name, arguments, workspace):
    experiment = EXPERIMENTS[name]
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    if not any(flag in arguments for flag in ("--help", "-h", "--dry-run", "--reuse-only", "--execute")):
        raise ValueError("Choose --dry-run, --reuse-only, or --execute explicitly")
    if "--reuse-only" in arguments and not experiment.replay_supported:
        raise ValueError("This adapter has no strict replay support yet")
    if "--execute" in arguments and ("--dry-run" in arguments or "--reuse-only" in arguments):
        raise ValueError("Choose one execution mode")
    workspace = Path(workspace).resolve()
    if not (workspace / "graphrag/eval/specs" / experiment.spec).is_file():
        raise ValueError("External experiments require a repository workspace; use --workspace PATH")
    previous_cwd, previous_argv = Path.cwd(), sys.argv
    try:
        os.chdir(workspace)
        sys.argv = [experiment.module, *arguments]
        importlib.import_module(experiment.module).main()
    finally:
        os.chdir(previous_cwd)
        sys.argv = previous_argv


def main(argv=None):
    parser = argparse.ArgumentParser(description="Interactive Agent research platform")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("catalog", help="List experiments without loading models")
    sub.add_parser("doctor", help="Check dependencies; never contact providers")
    plan = sub.add_parser("plan", help="Show inputs and status without external data")
    plan.add_argument("name", choices=EXPERIMENTS)
    demo = sub.add_parser("demo", help="Run a scripted LangGraph fixture, zero API cost")
    demo.add_argument("--output", type=Path, required=True)
    report = sub.add_parser("report", help="Verify and summarize a demo trace")
    report.add_argument("directory", type=Path)
    comparison = sub.add_parser("compare", help="Score normalized paired records offline")
    comparison.add_argument("records", type=Path)
    comparison.add_argument("--baseline", required=True)
    comparison.add_argument("--candidate", required=True)
    audit = sub.add_parser(
        "audit-boundaries",
        help="Aggregate saved action-boundary traces offline; never call providers",
    )
    audit.add_argument("--workspace", type=Path, default=Path("."))
    audit.add_argument("--revision-v1", type=Path)
    audit.add_argument("--revision-v2", type=Path)
    audit.add_argument("--routing", type=Path)
    audit.add_argument("--output", type=Path)
    experiment = sub.add_parser("experiment", help="Invoke a guarded research adapter")
    experiment.add_argument("--workspace", default=".")
    experiment.add_argument("name", choices=EXPERIMENTS)
    experiment.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.command == "catalog":
            result = [item.as_dict() for item in EXPERIMENTS.values()]
        elif args.command == "plan":
            result = EXPERIMENTS[args.name].as_dict()
            result["note"] = "Metadata only; use experiment NAME -- --dry-run for cost estimates"
        elif args.command == "doctor":
            result = doctor()
        elif args.command == "demo":
            from interactive_agent.artifacts import write_run
            from graphrag.agent.clinical_demo import run_demo
            if args.output.exists():
                raise ValueError("Output already exists; choose a new run directory")
            result = write_run(args.output, run_demo())
        elif args.command == "report":
            from interactive_agent.artifacts import read_report
            result = read_report(args.directory)
        elif args.command == "compare":
            from interactive_agent.scoring import compare
            result = compare(json.loads(args.records.read_text()), args.baseline, args.candidate)
        elif args.command == "audit-boundaries":
            from interactive_agent.boundary_audit import run_boundary_audit
            workspace = args.workspace.resolve()
            external = workspace / "graphrag/eval/external"
            result = run_boundary_audit(
                revision_v1=(args.revision_v1 or external / "mirage/textbooks_scaled_results.json"),
                revision_v2=(args.revision_v2 or external / "mirage/stage5j_agent_v2_scaled.json"),
                routing=(args.routing or external / "refusalbench/stage5l_results.json"),
            )
            if args.output:
                if args.output.exists():
                    raise ValueError("Output already exists; choose a new audit report path")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(
                    json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
        else:
            dispatch(args.name, args.arguments, args.workspace)
            return
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        if args.command == "doctor" and not result["ready"]:
            raise SystemExit(1)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
