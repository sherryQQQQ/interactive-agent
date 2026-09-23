import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("inspect_ai"), "inspect extra not installed")
class InspectIntegrationTests(unittest.TestCase):
    def test_scripted_contract_creates_standard_log_without_model_usage(self):
        from inspect_ai import eval
        from interactive_agent.inspect_eval import clinical_scripted_contract

        with tempfile.TemporaryDirectory() as root:
            with patch.dict(
                "os.environ", {"INSPECT_TRACE_FILE": str(Path(root) / "trace.log")}
            ), patch(
                "inspect_ai._util.appdirs.user_data_path",
                return_value=Path(root) / "inspect-data",
            ), patch(
                "inspect_ai._util.appdirs.user_cache_path",
                return_value=Path(root) / "inspect-cache",
            ):
                logs = eval(
                    clinical_scripted_contract(),
                    display="none",
                    log_dir=str(Path(root) / "logs"),
                )
                self.assertEqual(len(logs), 1)
                log = logs[0]
                self.assertEqual(log.status, "success")
                self.assertEqual(len(log.samples or []), 1)
                sample = log.samples[0]
                self.assertEqual(sample.scores["clinical_contract_scorer"].value, "C")
                self.assertEqual(sample.output.model, "scripted/clinical-fixture")
                self.assertEqual(sample.model_usage, {})
                trajectory = [
                    event.data["event"]
                    for event in sample.events
                    if type(event).__name__ == "InfoEvent"
                    and event.source == "clinical-agent"
                ]
                self.assertEqual(
                    trajectory,
                    [
                        "interview_ask",
                        "patient_tool_success",
                        "interview_ask",
                        "patient_tool_success",
                        "interview_finalize",
                        "retrieval_tool_success",
                        "diagnosed",
                        "safety_approve",
                    ],
                )


if __name__ == "__main__":
    unittest.main()
