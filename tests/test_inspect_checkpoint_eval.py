import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("inspect_ai"), "inspect extra not installed")
class InspectCheckpointTests(unittest.TestCase):
    def _write_results(self, path: Path, *, omit=None, duplicate=False):
        rows = []
        correctness = {
            "case-1": (True, False, True),
            "case-2": (False, True, False),
        }
        systems = ("closed-book", "textbooks-rag", "textbooks-agent")
        for case_id, outcomes in correctness.items():
            for system, correct in zip(systems, outcomes):
                if omit == (case_id, system):
                    continue
                rows.append(
                    {
                        "case_id": case_id,
                        "dataset": "fixture",
                        "system": system,
                        "correct": correct,
                        "status": "completed",
                        "raw_answer": "must-not-enter-inspect-log",
                        "retry_count": 1 if system == "textbooks-agent" else 0,
                        "tool_errors": [],
                    }
                )
        if duplicate:
            rows.append(dict(rows[0]))
        path.write_text(json.dumps({"results": rows}), encoding="utf-8")

    def test_loader_rejects_unpaired_and_duplicate_records(self):
        from interactive_agent.inspect_checkpoint_eval import load_paired_samples

        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "results.json"
            self._write_results(path, omit=("case-2", "textbooks-agent"))
            with self.assertRaisesRegex(ValueError, "Unmatched"):
                load_paired_samples(path)
            self._write_results(path, duplicate=True)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_paired_samples(path)

    def test_replay_preserves_pairing_and_excludes_raw_answers(self):
        from inspect_ai import eval
        from interactive_agent.inspect_checkpoint_eval import (
            load_paired_samples,
            mirage_paired_checkpoint,
        )

        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            path = root / "results.json"
            self._write_results(path)
            samples, source = load_paired_samples(path)
            self.assertEqual(len(samples), 2)
            self.assertEqual(source["provider_calls_expected"], 0)
            self.assertNotIn("raw_answer", json.dumps(samples[0].metadata))
            with patch.dict(
                "os.environ", {"INSPECT_TRACE_FILE": str(root / "trace.log")}
            ), patch(
                "inspect_ai._util.appdirs.user_data_path",
                return_value=root / "inspect-data",
            ), patch(
                "inspect_ai._util.appdirs.user_cache_path",
                return_value=root / "inspect-cache",
            ):
                logs = eval(
                    mirage_paired_checkpoint(str(path)),
                    display="none",
                    log_dir=str(root / "logs"),
                )
                log = logs[0]
                self.assertEqual(log.status, "success")
                self.assertEqual(len(log.samples or []), 2)
                self.assertEqual(log.samples[0].model_usage, {})
                score = log.samples[0].scores["paired_checkpoint_scorer"].value
                self.assertEqual(set(score), set(source["systems"]))
                serialized = json.dumps(log.samples[0].model_dump(), default=str)
                self.assertNotIn("must-not-enter-inspect-log", serialized)


if __name__ == "__main__":
    unittest.main()
