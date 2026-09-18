import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from interactive_agent.artifacts import write_run, read_report
from interactive_agent.cli import main, dispatch
from interactive_agent.scoring import compare


class PlatformTests(unittest.TestCase):
    def test_catalog_does_not_import_runners(self):
        with patch("interactive_agent.cli.importlib.import_module", side_effect=AssertionError), \
             contextlib.redirect_stdout(io.StringIO()) as stream:
            main(["catalog"])
        self.assertEqual(len(json.loads(stream.getvalue())), 4)

    def test_execution_requires_explicit_mode(self):
        with self.assertRaisesRegex(ValueError, "explicitly"):
            dispatch("information-gain", [], ".")
        with self.assertRaisesRegex(ValueError, "one execution mode"):
            dispatch("information-gain", ["--execute", "--reuse-only"], ".")
        with self.assertRaisesRegex(ValueError, "no strict replay"):
            dispatch("distractors", ["--reuse-only"], ".")

    def test_demo_report_roundtrip_and_overwrite_rejection(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            trace = {"status": "answered", "questions_asked": 2, "trace": []}
            report = write_run(directory, trace)
            self.assertEqual(read_report(directory), report)
            with self.assertRaises(FileExistsError):
                write_run(directory, trace)
            (directory / "trace.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "digest"):
                read_report(directory)

    def test_real_offline_demo_cli(self):
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stdout(io.StringIO()):
            directory = Path(root) / "demo"
            main(["demo", "--output", str(directory)])
            report = read_report(directory)
        self.assertEqual(report["questions_asked"], 2)
        self.assertEqual(report["model_calls"], 0)

    def test_paired_metrics_keep_invalid_correct_distinct(self):
        records = [
            {"case_id": "one", "arm": "a", "correct": False, "valid": True},
            {"case_id": "one", "arm": "b", "correct": True, "valid": False},
        ]
        report = compare(records, "a", "b")
        self.assertEqual(report["candidate_wins"], 1)
        self.assertEqual(report["arms"]["b"]["accuracy"], 1)
        self.assertEqual(report["arms"]["b"]["valid_and_correct_rate"], 0)
        self.assertIsNone(report["arms"]["b"]["selective_accuracy"])
        with self.assertRaisesRegex(ValueError, "identical"):
            compare(records[:1], "a", "b")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            compare(records + records, "a", "b")


if __name__ == "__main__":
    unittest.main()
