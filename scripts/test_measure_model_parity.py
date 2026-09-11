"""Comparator logic tests, not evidence of real-model parity."""

import copy
import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "measure_model_parity", Path(__file__).with_name("measure_model_parity.py")
)
assert _spec and _spec.loader
_parity = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parity)
check_regression = _parity.check_regression
validate_scores = _parity.validate_scores


class ParityRegressionTest(unittest.TestCase):
    def setUp(self):
        self.report = {
            "identity": {"models": "test-only", "fixtures": ["hash"]},
            "observations": [
                {
                    "id": "fixture-001.png",
                    "same_winner": True,
                    "input_equal": True,
                    "score_delta_max": 0.00001,
                    "same_tensor_score_delta_max": 0.000001,
                    "input_delta_max": 0.0,
                }
            ],
        }
        self.baseline = {
            "status": "accepted",
            "identity": self.report["identity"],
            "score_tolerance": 0.00002,
            "same_tensor_score_tolerance": 0.000002,
            "input_tolerance": 0.0,
        }

    def test_matching_capture_passes(self):
        self.assertEqual(check_regression(self.report, self.baseline), [])

    def test_blocked_baseline_cannot_pass(self):
        self.baseline["status"] = "blocked"
        self.assertTrue(check_regression(self.report, self.baseline))

    def test_winner_mismatch_always_blocks(self):
        self.report["observations"][0]["same_winner"] = False
        self.assertTrue(check_regression(self.report, self.baseline))

    def test_different_production_tensors_block_even_within_baseline(self):
        self.report["observations"][0]["input_equal"] = False
        self.assertTrue(check_regression(self.report, self.baseline))

    def test_exceeded_measured_score_or_pixel_limit_blocks(self):
        for key in [
            "score_delta_max",
            "same_tensor_score_delta_max",
            "input_delta_max",
        ]:
            with self.subTest(key=key):
                report = copy.deepcopy(self.report)
                report["observations"][0][key] = 1.0
                self.assertTrue(check_regression(report, self.baseline))

    def test_changed_fixture_or_artifact_requires_new_review(self):
        self.report["identity"] = {"models": "changed"}
        self.assertTrue(check_regression(self.report, self.baseline))

    def test_empty_capture_cannot_pass(self):
        self.report["observations"] = []
        self.assertTrue(check_regression(self.report, self.baseline))

    def test_invalid_probabilities_are_rejected(self):
        for scores in [
            [0.5, 0.5],
            [float("nan"), 0, 0, 1],
            [1, 1, 1, 1],
            [-1, 1, 1, 0],
        ]:
            with self.subTest(scores=scores), self.assertRaises(ValueError):
                validate_scores(scores)


if __name__ == "__main__":
    unittest.main()
