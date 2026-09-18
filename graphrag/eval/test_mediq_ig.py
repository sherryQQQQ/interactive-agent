"""Offline regressions for experimental isolation and complete observations."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from graphrag.agent.clinical_handoff import ClinicalHandoff, ConversationTurn
from graphrag.eval import mediq_ig as ig
from graphrag.eval.checkpointed_gemini import ProviderResponse
from graphrag.eval.mediq_handoff_data import ConceptAwareFactPatient
from graphrag.eval.test_mediq_handoff_benchmark import fixture_case, Retriever


def response(payload):
    return ProviderResponse(json.dumps(payload), 10, 10, 20, 0.01, False)


def update(_raw, conversation):
    # Make the consumed observation visible without relying on an LLM.
    return SimpleNamespace(
        handoff=ClinicalHandoff(conversation[-1].content, ()),
        decision=SimpleNamespace(action="ask", question="How long has the fever lasted?"),
    )


class IGFairnessTests(unittest.TestCase):
    def test_replay_miss_or_budget_guard_stops_runner(self):
        with tempfile.TemporaryDirectory() as root, \
             patch.object(ig, "run_ig_case", side_effect=RuntimeError("Reuse-only miss")):
            with self.assertRaisesRegex(RuntimeError, "Reuse-only"):
                ig.run_ig_benchmark([fixture_case()], None, Retriever(),
                    Path(root) / "result.json", Path(root) / "log.jsonl", {}, "dev")
            self.assertFalse((Path(root) / "result.json").exists())

    def test_last_answer_is_consumed_without_a_fourth_question(self):
        answers = []

        def patient(question, conversation):
            answers.append(question)
            return f"observation-{len(answers)}"

        with patch.object(ig, "parse_interview_update", side_effect=update):
            result = ig._run_llm_freeform_arm(
                fixture_case(), lambda *args: response({}), patient,
                Retriever(), lambda *args: None,
            )
        self.assertEqual(len(answers), 3)
        self.assertEqual(result["handoff"].chief_complaint, "observation-3")
        self.assertEqual(len(result["arm_calls"]), 4)

    def test_arms_have_identical_but_independent_patient_states(self):
        patients = []

        def interview(case, provider, patient, retriever, record, **kwargs):
            patients.append(patient)
            self.assertIs(type(patient), ConceptAwareFactPatient)
            self.assertNotIn("test-contamination", patient.revealed)
            patient.revealed["test-contamination"] = "marker"
            return {"handoff": ClinicalHandoff("fixture", ()),
                    "conversation": (), "questions_asked": 0, "errors": []}

        with patch.object(ig, "_run_llm_freeform_arm", side_effect=interview), \
             patch.object(ig, "_run_ig_arm", side_effect=interview), \
             patch.object(ig, "_diagnose", return_value={"correct": True}):
            ig.run_ig_case(fixture_case(), None, Retriever())
        self.assertEqual(len({id(patient) for patient in patients}), 3)

    def test_oracle_probes_do_not_consume_facts_and_commit_once(self):
        class Patient:
            def __init__(self):
                self.questions = []

            def __call__(self, question, conversation):
                self.questions.append(question)
                return f"answer-{len(self.questions)}"

        patient = Patient()

        def provider(call_id, stage, prompt, schema):
            if stage.endswith("candidates"):
                # Empty candidates must not break selection indices.
                return response({"candidates": [{"question": ""},
                    {"question": "first"}, {"question": "second"}]})
            if stage.endswith("baseline"):
                return response({"option_probabilities": {"A": .5, "B": .5}})
            if stage.endswith("score"):
                p = .9 if call_id.endswith(":2") else .5
                return response({"option_probabilities": {"A": p, "B": 1-p}})
            return response({})

        with patch.object(ig, "MAX_QUESTIONS", 1), \
             patch.object(ig, "parse_interview_update", side_effect=update):
            result = ig._run_ig_arm(fixture_case(), provider, patient,
                                   Retriever(), lambda *args: None, "oracle")
        self.assertEqual(patient.questions, ["second"])
        self.assertEqual([c["patient_answer"] for c in result["ig_trace"][0]["candidates"]],
                         ["answer-1", "answer-1"])
        self.assertEqual(result["handoff"].chief_complaint, "answer-1")

    def test_failed_cases_stay_in_the_accuracy_denominator(self):
        metrics = ig.compute_ig_metrics([
            {"status": "answered", "arms": {arm: {"questions_asked": 1,
             "diagnosis": {"correct": True}} for arm in ig.ARMS}},
            {"status": "failed", "arms": {}},
        ])
        self.assertEqual(metrics["failed_cases"], 1)
        self.assertEqual(metrics["accuracy"]["llm-freeform"], .5)


if __name__ == "__main__":
    unittest.main()
