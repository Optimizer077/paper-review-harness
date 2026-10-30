"""Independent adversarial checks for aggressive score caps and readiness."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from test_scoring_v2 import s, SCRIPT, rubric_fixture, evaluation_fixture, criterion, unassess, blocker


class AggressiveIndependentTests(unittest.TestCase):
    def setUp(self):
        self.rubric = rubric_fixture()
        self.data = evaluation_fixture(self.rubric)

    def score(self):
        return s.score(self.data, self.rubric, strictness="aggressive")

    def test_fractional_weights_do_not_round_past_domain_thresholds(self):
        # This is a valid alternate profile: redistribute its communication
        # weight from 12 to 20, taking the additional 8 from research-question.
        self.data["profile"] = "theory"
        weights = self.rubric["profiles"]["theory"]["weights"]
        weights["research-question"] = 0
        for cid in s.MANUSCRIPT_DOMAINS["communication"]:
            weights[cid] = 0
        criterion(self.data, "title-abstract")["rating"] = 2
        for low_weight, expected_cap, displayed in (
            (16.0004, 59, 60), (16, 74, 60), (15.9996, 74, 60),
            (10.0004, 74, 75), (10, 100, 75), (9.9996, 100, 75),
        ):
            with self.subTest(low_weight=low_weight):
                weights["title-abstract"] = low_weight
                weights["introduction-logic"] = 20 - low_weight
                result = self.score()
                domain = next(d for d in result["domain_scores"] if d["id"] == "communication")
                self.assertEqual(domain["score_out_of_100"], displayed)
                self.assertEqual(result["score_cap_out_of_100"], expected_cap)
                self.assertEqual(result["readiness"], "reviewed" if expected_cap == 100 else "needs_revision_or_evidence")

    def test_zero_weight_missing_assessment_still_withholds_both_totals(self):
        self.data["profile"] = "theory"  # jargon-acronyms has zero weight.
        unassess(criterion(self.data, "jargon-acronyms"))
        result = self.score()
        self.assertEqual(result["assessment_coverage_percent"], 100)
        self.assertEqual(result["status"], "provisional")
        self.assertEqual(result["readiness"], "incomplete")
        self.assertIsNone(result["score_out_of_100"])
        self.assertIsNone(result["effective_score_out_of_100"])

    def test_zero_weight_severe_criterion_still_cannot_hide(self):
        self.data["profile"] = "theory"
        criterion(self.data, "jargon-acronyms")["rating"] = 0
        result = self.score()
        self.assertEqual(result["score_out_of_100"], 100)
        self.assertEqual(result["effective_score_out_of_100"], 69)
        self.assertEqual(result["readiness"], "needs_revision_or_evidence")

    def test_null_domain_does_not_fabricate_numeric_failure(self):
        self.data["profile"] = "theory"
        weights = self.rubric["profiles"]["theory"]["weights"]
        for cid in s.MANUSCRIPT_DOMAINS["communication"]:
            weights[cid] = 0
        weights["research-question"] += 12
        result = self.score()
        domain = next(d for d in result["domain_scores"] if d["id"] == "communication")
        self.assertIsNone(domain["score_out_of_100"])
        self.assertEqual(result["score_caps"], [])
        self.assertEqual(result["readiness"], "reviewed")

    def test_noncore_low_confidence_does_not_cap_and_resolved_blocker_does_not_block(self):
        for row in self.data["criteria"]:
            if row["id"] not in s.MANUSCRIPT_CORE:
                row["confidence"] = "low"
        self.data["critical_blockers"] = [blocker("resolved")]
        result = self.score()
        self.assertEqual(result["score_out_of_100"], 100)
        self.assertEqual(result["effective_score_out_of_100"], 100)
        self.assertEqual(result["readiness"], "reviewed")

    def test_caps_cannot_raise_an_already_lower_raw_score(self):
        for row in self.data["criteria"]:
            row["rating"] = 0
        self.data["critical_blockers"] = [blocker()]
        result = self.score()
        self.assertEqual(result["score_out_of_100"], 0)
        self.assertEqual(result["effective_score_out_of_100"], 0)
        self.assertEqual(result["score_cap_out_of_100"], 39)
        self.assertEqual(result["readiness"], "blocked")

    def test_scoring_and_returned_records_do_not_mutate_input(self):
        criterion(self.data, "research-question")["rating"] = 2
        original = copy.deepcopy(self.data)
        result = self.score()
        self.assertEqual(self.data, original)
        result["criteria"][0]["evidence"][0]["observation"] = "changed returned record"
        result["score_caps"][0]["evidence"][0]["locator"] = "changed returned cap"
        self.assertEqual(self.data, original)

    def test_randomized_ratings_match_independent_fraction_oracle(self):
        rng = random.Random(20261030)
        weights = self.rubric["profiles"]["empirical-ml"]["weights"]
        for case in range(150):
            self.data = evaluation_fixture(self.rubric)
            for row in self.data["criteria"]:
                row["rating"] = rng.randrange(5)
                row["confidence"] = rng.choice(("low", "medium", "high"))
            if case % 5 == 0:
                self.data["critical_blockers"] = [blocker()]
            caps = [100]
            for row in self.data["criteria"]:
                core = row["id"] in s.MANUSCRIPT_CORE
                rating, confidence = row["rating"], row["confidence"]
                if rating < 2:
                    caps.append(49 if core else 69)
                elif core and rating == 2:
                    caps.append(69)
                if core and confidence != "high":
                    caps.append(59 if confidence == "low" else 79)
            rows = {row["id"]: row for row in self.data["criteria"]}
            for ids in s.MANUSCRIPT_DOMAINS.values():
                domain = Fraction(25 * sum(weights[c] * rows[c]["rating"] for c in ids), sum(weights[c] for c in ids))
                if domain < 60:
                    caps.append(59)
                elif domain < 75:
                    caps.append(74)
            if self.data["critical_blockers"]:
                caps.append(39)
            expected_raw = round(sum(Fraction(weights[c] * rows[c]["rating"], 4) for c in rows), 2)
            result = self.score()
            with self.subTest(case=case):
                self.assertEqual(result["score_out_of_100"], expected_raw)
                self.assertEqual(result["score_cap_out_of_100"], min(caps))
                self.assertEqual(result["effective_score_out_of_100"], min(expected_raw, *caps))
                self.assertEqual(result["readiness"], "blocked" if self.data["critical_blockers"] else "needs_revision_or_evidence")

    def test_cli_honors_input_mode_and_rejects_tampered_policy(self):
        self.data["strictness"] = "aggressive"
        criterion(self.data, "research-question")["rating"] = 2
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, rubric, output = [root / name for name in ("input.json", "rubric.json", "output.json")]
            source.write_text(json.dumps(self.data), encoding="utf-8")
            rubric.write_text(json.dumps(self.rubric), encoding="utf-8")
            command = [sys.executable, str(SCRIPT), str(source), "--rubric", str(rubric), "--out", str(output)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            scored = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(scored["strictness"], "aggressive")
            self.assertEqual(scored["effective_score_out_of_100"], 69)
            scored["scoring_policy_sha256"] = "0" * 64
            source.write_text(json.dumps(scored), encoding="utf-8")
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("scoring_policy_sha256", run.stderr)


if __name__ == "__main__":
    unittest.main()
