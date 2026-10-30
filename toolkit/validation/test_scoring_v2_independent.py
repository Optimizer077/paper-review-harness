"""Independent offline adversarial checks against the shipped rubric catalogs.

No production constants or synthetic catalog copied from the scorer are used.
The all-four input is an arithmetic fixture, not a manuscript evaluation.
"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper-writing/scripts/score_evaluation.py"
spec = importlib.util.spec_from_file_location("independent_scoring", SCRIPT)
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def manuscript():
    rubric = load("paper-writing/assets/manuscript-rubric.json")
    data = {
        "version": 2, "rubric_id": rubric["rubric_id"], "profile": "empirical-ml",
        "subject": {"id": "independent-arithmetic-fixture", "revision": "one"},
        "reviewer": {"id": "independent-auditor", "type": "agent"},
        "evaluated_at": "2026-10-30",
        "criteria": [{"id": c["id"], "status": "assessed", "rating": 4,
                      "confidence": "high", "rationale": "Explicit arithmetic fixture.",
                      "evidence": [{"locator": "fixture", "observation": "Not a scientific assessment."}]}
                     for c in rubric["criteria"]],
        "critical_blockers": [],
    }
    return rubric, data


def row(data, cid):
    return next(x for x in data["criteria"] if x["id"] == cid)


class IndependentScoringTests(unittest.TestCase):
    def test_real_profiles_have_distinct_design_weights_and_gate_low_core(self):
        rubric, data = manuscript()
        row(data, "design-validity")["rating"] = 0
        for profile, expected in {"empirical-ml": 93, "theory": 90,
                                  "clinical": 91, "systematic-review": 92}.items():
            with self.subTest(profile=profile):
                data["profile"] = profile
                out = scorer.score(data, rubric)
                self.assertEqual(out["score_out_of_100"], expected)
                self.assertEqual(out["readiness"], "needs_revision_or_evidence")

    def test_perfect_score_cannot_hide_explicit_blocker_in_json_or_report(self):
        rubric, data = manuscript()
        data["critical_blockers"] = [{"id": "fabricated-endpoint", "criterion_id": "claim-evidence-entailment",
            "description": "Abstract outcome was never measured.", "status": "open",
            "evidence": [{"locator": "abstract; Table 2", "observation": "Outcome absent from table."}]}]
        out = scorer.score(data, rubric)
        self.assertEqual(out["score_out_of_100"], 100)
        self.assertEqual(out["readiness"], "blocked")
        self.assertEqual(out["revision_priorities"][0]["kind"], "critical_blocker")
        report = scorer.render_markdown(out, rubric)
        self.assertIn("readiness: blocked", report)
        self.assertIn("Abstract outcome was never measured.", report)

    def test_unknown_na_and_confidence_are_three_different_operations(self):
        rubric, data = manuscript()
        row(data, "design-validity").update(status="unassessed", rating=None, confidence=None,
                                         evidence=[], rationale="Proof unavailable.")
        out = scorer.score(data, rubric)
        self.assertIsNone(out["score_out_of_100"])
        self.assertEqual(out["assessment_coverage_percent"], 93)
        self.assertEqual(out["missing_assessment_bounds"], {"lower": 93, "upper": 100})
        self.assertEqual(out["applicable_weight"], 100)
        self.assertEqual(out["readiness"], "incomplete")
        rubric, data = manuscript()
        row(data, "figures-tables").update(status="not_applicable", rating=None, confidence=None,
            applicability_reason="No displays and no display-dependent claim.")
        row(data, "design-validity")["rating"] = 0
        out = scorer.score(data, rubric)
        self.assertEqual(out["score_out_of_100"], 92.86)
        self.assertEqual(out["excluded_weight"], 2)
        rubric, data = manuscript()
        row(data, "design-validity")["confidence"] = "low"
        out = scorer.score(data, rubric)
        self.assertEqual(out["score_out_of_100"], 100)
        self.assertEqual(out["readiness"], "needs_revision_or_evidence")

    def test_input_cannot_remove_categories_reweight_or_exclude_core(self):
        for mutation in ("omit", "weight", "unknown", "core-na"):
            rubric, data = manuscript()
            if mutation == "omit":
                data["criteria"].pop()
            elif mutation == "weight":
                data["criteria"][0]["weight"] = 100
            elif mutation == "unknown":
                data["criteria"][0]["id"] = "invented"
            else:
                row(data, "design-validity").update(status="not_applicable", rating=None,
                    confidence=None, applicability_reason="Unavailable evidence.")
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                scorer.score(data, rubric)

    def test_changed_coverage_applicability_or_instrument_cannot_emit_total_delta(self):
        rubric, data = manuscript()
        prior = scorer.score(data, rubric)
        for change in ("coverage", "applicability"):
            current = copy.deepcopy(data)
            target = row(current, "figures-tables")
            target.update(status="unassessed", rating=None, confidence=None)
            if change == "applicability":
                target.update(status="not_applicable", applicability_reason="No display-dependent claims.")
            comparison = scorer.compare_evaluations(prior, current, rubric)
            self.assertIsNone(comparison["total_score_delta"])
            self.assertIsNone(next(x for x in comparison["criterion_deltas"]
                                   if x["id"] == "figures-tables")["rating_delta"])
        changed = copy.deepcopy(rubric)
        changed["criteria"][0]["anchors"]["4"] += " Additional constraint."
        with self.assertRaises(ValueError):
            scorer.compare_evaluations(prior, data, changed)
        current = copy.deepcopy(data)
        current["profile"] = "theory"
        with self.assertRaises(ValueError):
            scorer.compare_evaluations(prior, current, rubric)

    def test_comparison_recomputes_tampered_derived_fields(self):
        rubric, data = manuscript()
        prior = scorer.score(data, rubric)
        prior.update(score_out_of_100=0, readiness="blocked", assessment_coverage_percent=1)
        self.assertEqual(scorer.compare_evaluations(prior, data, rubric)["total_score_delta"], 0)

    def test_toolkit_limitation_anchor_with_synthetic_arithmetic(self):
        rubric = load("paper-writing/assets/toolkit-rubric.json")
        _, data = manuscript()
        data.update(rubric_id=rubric["rubric_id"], profile="toolkit")
        data["criteria"] = [{"id": c["id"], "status": "assessed", "rating": 4,
                             "confidence": "high", "rationale": "Synthetic arithmetic fixture.",
                             "evidence": [{"locator": "fixture", "observation": "Invented ratings; not a toolkit evaluation."}]}
                            for c in rubric["criteria"]]
        row(data, "real-manuscript-calibration")["rating"] = 1
        out = scorer.score(data, rubric)
        self.assertLess(out["score_out_of_100"], 100)
        self.assertEqual(out["assessment_coverage_percent"], 100)
        self.assertEqual(row(out, "real-manuscript-calibration")["rating"], 1)
        self.assertIn("not scientific certification", scorer.render_markdown(out, rubric))

    def test_cli_against_actual_catalog_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "duplicate.json"
            target.write_text('{"version":2,"version":1}', encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(target), "--rubric",
                str(ROOT / "paper-writing/assets/manuscript-rubric.json")],
                capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("duplicate JSON object key", run.stderr)
            self.assertNotIn("Traceback", run.stderr)


if __name__ == "__main__":
    unittest.main()
