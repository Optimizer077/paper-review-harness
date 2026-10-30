import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("scoring", Path(__file__).resolve().parents[1] / "paper-writing/scripts/score_evaluation.py")
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class ScoringTests(unittest.TestCase):
    def test_weighted_score_is_reproducible(self):
        result = s.score({"criteria": [{"id": "a", "weight": 80, "rating": 3, "evidence": ["Observed passage"]}, {"id": "b", "weight": 20, "rating": 4, "evidence": ["Verified artifact"]}]})
        self.assertEqual(result["score_out_of_100"], 80)

    def test_unassessed_criteria_do_not_inflate_score(self):
        result = s.score({"criteria": [{"id": "a", "weight": 80, "rating": 4, "evidence": ["Observed passage"]}, {"id": "b", "weight": 20, "rating": None}]})
        self.assertIsNone(result["score_out_of_100"])
        self.assertEqual(result["assessed_weight_percent"], 80)
        self.assertEqual(result["earned_subtotal"], 80)

    def test_invalid_rating_and_missing_evidence_rejected(self):
        for row in [{"id": "a", "weight": 100, "rating": 5, "evidence": ["x"]}, {"id": "a", "weight": 100, "rating": 3, "evidence": []}, {"id": "a", "weight": 100, "rating": True, "evidence": ["x"]}]:
            with self.assertRaises(ValueError):
                s.score({"criteria": [row]})


if __name__ == "__main__":
    unittest.main()
