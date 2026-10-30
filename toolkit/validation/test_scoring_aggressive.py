"""Aggressive policy invariants, distinct from rubric rating arithmetic."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_scoring_v2 import s, SCRIPT, rubric_fixture, evaluation_fixture, criterion, unassess, blocker


class AggressiveScoringTests(unittest.TestCase):
    def setUp(self):
        self.rubric = rubric_fixture()
        self.data = evaluation_fixture(self.rubric)

    def score(self):
        return s.score(self.data, self.rubric, strictness="aggressive")

    def test_core_two_cannot_hide_in_high_average(self):
        criterion(self.data, "research-question")["rating"] = 2
        result = self.score()
        self.assertEqual(result["score_out_of_100"], 97.5)
        self.assertEqual(result["effective_score_out_of_100"], 69)
        self.assertEqual(result["readiness"], "needs_revision_or_evidence")
        self.assertEqual(result["score_caps"][0]["rule"], "core_below_target")
        self.assertTrue(result["score_caps"][0]["evidence"])
        self.assertEqual(s.score(self.data, self.rubric)["readiness"], "reviewed")

    def test_severe_core_and_noncore_caps(self):
        for cid, expected in (("research-question", 49), ("motivation-gap", 69)):
            with self.subTest(cid=cid):
                self.data = evaluation_fixture(self.rubric)
                criterion(self.data, cid)["rating"] = 1
                result = self.score()
                self.assertGreater(result["score_out_of_100"], 95)
                self.assertEqual(result["effective_score_out_of_100"], expected)

    def test_domain_caps_use_complete_domain_and_exact_boundary(self):
        # Communication has no core criteria; all ratings >=2 avoid other caps.
        for rating, expected, rule in ((2, 59, "domain_severe"), (3, 100, None)):
            self.data = evaluation_fixture(self.rubric)
            for cid in s.MANUSCRIPT_DOMAINS["communication"]:
                criterion(self.data, cid)["rating"] = rating
            result = self.score()
            self.assertEqual(result["score_cap_out_of_100"], expected)
            if rule:
                self.assertIn(rule, [x["rule"] for x in result["score_caps"]])
        # 70% through weighted combinations, below75 but at least60.
        criterion(self.data, "title-abstract")["rating"] = 2
        result = self.score()
        self.assertEqual(result["score_cap_out_of_100"], 74)
        self.assertIn("domain_below_target", [x["rule"] for x in result["score_caps"]])
        for cid in s.MANUSCRIPT_DOMAINS["communication"]:
            criterion(self.data, cid)["rating"] = 2
        criterion(self.data, "title-abstract")["rating"] = 4
        # (3*4 + 12*2) / (15*4) =60%; severe-domain cutoff is strictly below60.
        self.assertEqual(self.score()["score_cap_out_of_100"], 74)

    def test_confidence_caps_do_not_multiply_rating(self):
        for confidence, cap in (("low", 59), ("medium", 79)):
            criterion(self.data, "design-validity")["confidence"] = confidence
            result = self.score()
            self.assertEqual(result["score_out_of_100"], 100)
            self.assertEqual(result["effective_score_out_of_100"], cap)
            self.assertEqual(result["readiness"], "needs_revision_or_evidence")
            self.assertIn("core_confidence_" + confidence, [x["rule"] for x in result["score_caps"]])

    def test_blocker_minimum_not_additive_and_missing_not_zero(self):
        self.data["critical_blockers"] = [blocker()]
        criterion(self.data, "research-question")["rating"] = 1
        result = self.score()
        self.assertEqual(result["effective_score_out_of_100"], 39)
        self.assertEqual(result["readiness"], "blocked")
        unassess(criterion(self.data, "motivation-gap"))
        result = self.score()
        self.assertIsNone(result["score_out_of_100"])
        self.assertIsNone(result["effective_score_out_of_100"])
        self.assertEqual(result["readiness"], "blocked")
        self.assertNotIn("effective_score_bounds", result)
        self.assertEqual(result["score_cap_out_of_100"], 39)
        self.data["critical_blockers"] = []
        self.assertEqual(self.score()["readiness"], "incomplete")

    def test_selected_mode_policy_hash_and_recomputed_fields(self):
        result = self.score()
        policy, digest = s.scoring_policy("aggressive")
        self.assertEqual(result["scoring_policy_id"], policy["id"])
        self.assertEqual(result["scoring_policy_sha256"], digest)
        self.assertNotEqual(digest, s.scoring_policy("standard")[1])
        result.update(effective_score_out_of_100=0, score_caps=[{"forged": True}], score_cap_out_of_100=0)
        recomputed = s.score(result, self.rubric)
        self.assertEqual(recomputed["effective_score_out_of_100"], 100)
        self.assertEqual(recomputed["score_caps"], [])
        result["scoring_policy_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "scoring_policy_sha256"):
            s.score(result, self.rubric)

    def test_comparison_rejects_modes_and_withholds_incomplete_effective_delta(self):
        prior = self.score()
        with self.assertRaisesRegex(ValueError, "strictness"):
            s.compare_evaluations(prior, self.data, self.rubric)
        self.data["strictness"] = "aggressive"
        criterion(self.data, "research-question")["rating"] = 2
        comparison = s.compare_evaluations(prior, self.data, self.rubric)
        self.assertEqual(comparison["total_score_delta"], -2.5)
        self.assertEqual(comparison["effective_score_delta"], -31)
        unassess(criterion(self.data, "research-question"))
        comparison = s.compare_evaluations(prior, self.data, self.rubric)
        self.assertIsNone(comparison["effective_score_delta"])
        self.assertIn("complete", comparison["effective_score_delta_reason"])

    def test_v1_rejects_aggressive_and_bad_mode_rejected(self):
        legacy = {"criteria": [{"id": "a", "weight": 100, "rating": 4, "evidence": ["inspected"]}]}
        self.assertEqual(s.score(legacy)["score_out_of_100"], 100)
        with self.assertRaisesRegex(ValueError, "Version 1"):
            s.score(legacy, strictness="aggressive")
        with self.assertRaisesRegex(ValueError, "strictness"):
            s.score(self.data, self.rubric, strictness="unknown")

    def test_cli_markdown_exposes_raw_effective_and_cap_evidence(self):
        criterion(self.data, "research-question")["rating"] = 2
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rubric, output, report = [root / name for name in ("input.json", "rubric.json", "score.json", "report.md")]
            source.write_text(json.dumps(self.data), encoding="utf-8")
            rubric.write_text(json.dumps(self.rubric), encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(source), "--rubric", str(rubric), "--strictness", "aggressive", "--out", str(output), "--markdown", str(report)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["effective_score_out_of_100"], 69)
            text = report.read_text(encoding="utf-8")
            for fragment in ("Effective score: 69/100", "raw anchored score: 97.5/100", "core_below_target", "manuscript §1", "Policy SHA-256", "not additive penalties", "no effective total"):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
