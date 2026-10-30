"""Behavioral invariants for catalog-bound editorial scoring (stdlib only)."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "paper-writing/scripts/score_evaluation.py"
spec = importlib.util.spec_from_file_location("scoring_v2", SCRIPT)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


def rubric_fixture():
    criteria = []
    for domain, ids in s.MANUSCRIPT_DOMAINS.items():
        for cid in ids:
            criteria.append({
                "id": cid, "title": cid.replace("-", " ").title(), "domain": domain,
                "description": f"Assess the inspected evidence relevant to {cid}.",
                "core": cid in s.MANUSCRIPT_CORE, "allow_not_applicable": cid == "figures-tables",
                "anchors": {
                    "0": "Absent or contradicted by inspected source evidence.",
                    "1": "Major observed defects prevent the criterion being met.",
                    "2": "Partially supported, with specific remaining evidence gaps.",
                    "3": "Strongly supported within scope, with bounded gaps.",
                    "4": "Fully supported within the inspected scope and limitations.",
                },
                "checks": [f"Inspect and cite relevant source locations for {cid}."],
                "role_ids": ["reviewer"],
            })
    profiles = {
        name: {"title": name, "weights": dict(s.EMPIRICAL_WEIGHTS), "guidance": {"design-validity": f"Evaluate validity appropriate to {name}."}}
        for name in ("empirical-ml", "theory", "clinical", "systematic-review")
    }
    # Deliberately distinct contribution weights to verify selected-profile use.
    profiles["theory"]["weights"]["research-question"] += 3
    profiles["theory"]["weights"]["figures-tables"] -= 1
    profiles["theory"]["weights"]["jargon-acronyms"] -= 2
    return {
        "version": 2, "rubric_id": "paper-writing-v2", "max_rating": 4,
        "default_profile": "empirical-ml", "core_threshold": 2,
        "domains": [{"id": did, "title": did.title()} for did in s.MANUSCRIPT_DOMAINS],
        "criteria": criteria, "profiles": profiles,
    }


def evaluation_fixture(rubric=None):
    rubric = rubric or rubric_fixture()
    return {
        "version": 2, "rubric_id": rubric["rubric_id"], "profile": rubric["default_profile"],
        "subject": {"id": "manuscript-example", "revision": "r1", "artifact_sha256": "a" * 64},
        "reviewer": {"id": "independent-reviewer", "type": "agent"}, "evaluated_at": "2026-10-30",
        "criteria": [{
            "id": criterion["id"], "status": "assessed", "rating": 4, "confidence": "high",
            "evidence": [{"locator": f"manuscript §{index + 1}", "observation": f"Inspected support for {criterion['id']}", "source_id": "manuscript-r1"}],
            "rationale": "All applicable anchor requirements supported in inspected scope.",
        } for index, criterion in enumerate(rubric["criteria"])],
        "critical_blockers": [],
    }


def criterion(data, cid):
    return next(row for row in data["criteria"] if row["id"] == cid)


def unassess(row):
    row.update(status="unassessed", rating=None, confidence=None, evidence=[], rationale="Relevant source has not been inspected.")


def exclude_displays(data):
    criterion(data, "figures-tables").update(
        status="not_applicable", rating=None, confidence=None,
        applicability_reason="No displays are present and no claim needs a display.",
        rationale="The inspected manuscript has no display-dependent claims.",
    )


def blocker(status="open"):
    value = {
        "id": "unsupported-claim", "criterion_id": "claim-evidence-entailment", "status": status,
        "description": "The polished headline claim is unsupported by the inspected experiment.",
        "evidence": [{"locator": "abstract line 4; results §3", "observation": "The abstract claims an outcome that the results do not measure."}],
    }
    if status == "resolved":
        value["resolution"] = "Narrowed the claim to the measured outcome and checked both cited locations."
    return value


class ScoringV2Tests(unittest.TestCase):
    def setUp(self):
        self.rubric = rubric_fixture()
        self.data = evaluation_fixture(self.rubric)

    def score(self):
        return s.score(self.data, self.rubric)

    def test_complete_catalog_and_domain_weights(self):
        result = self.score()
        self.assertEqual(result["score_out_of_100"], 100)
        self.assertEqual(result["assessment_coverage_percent"], 100)
        self.assertEqual(result["readiness"], "reviewed")
        self.assertEqual(result["status"], "complete")
        self.assertEqual({row["id"]: row["nominal_weight"] for row in result["domain_scores"]}, {
            "argument": 20, "evidence": 35, "consistency": 20, "communication": 15, "transparency": 10,
        })
        self.assertEqual(result["missing_assessment_bounds"], {"lower": 100, "upper": 100})

    def test_domains_use_criterion_weights_without_double_weighting(self):
        criterion(self.data, "design-validity")["rating"] = 0
        result = self.score()
        evidence = next(row for row in result["domain_scores"] if row["id"] == "evidence")
        self.assertEqual(evidence["score_out_of_100"], 80)
        self.assertEqual(evidence["earned_subtotal"], 28)
        self.assertEqual(result["score_out_of_100"], 93)
        self.assertEqual(result["readiness"], "needs_revision_or_evidence")

    def test_polished_high_score_stays_blocked(self):
        self.data["critical_blockers"] = [blocker()]
        result = self.score()
        self.assertEqual(result["score_out_of_100"], 100)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["readiness"], "blocked")
        self.assertEqual(result["active_blockers"], self.data["critical_blockers"])
        self.assertEqual(result["revision_priorities"][0]["kind"], "critical_blocker")

    def test_resolution_is_explicit_and_does_not_change_score(self):
        self.data["critical_blockers"] = [blocker("resolved")]
        result = self.score()
        self.assertEqual(result["score_out_of_100"], 100)
        self.assertEqual(result["readiness"], "reviewed")
        self.assertEqual(result["active_blockers"], [])
        del self.data["critical_blockers"][0]["resolution"]
        with self.assertRaises(ValueError):
            self.score()

    def test_unassessed_is_unknown_and_keeps_denominator(self):
        unassess(criterion(self.data, "figures-tables"))
        result = self.score()
        self.assertIsNone(result["score_out_of_100"])
        self.assertEqual(result["applicable_weight"], 100)
        self.assertEqual(result["excluded_weight"], 0)
        self.assertEqual(result["earned_subtotal"], 98)
        self.assertEqual(result["assessment_coverage_percent"], 98)
        self.assertEqual(result["missing_assessment_bounds"], {"lower": 98, "upper": 100})
        self.assertEqual(result["readiness"], "incomplete")
        self.assertEqual(result["revision_priorities"][0]["kind"], "missing_assessment")
        self.assertIn("unknown", result["revision_priorities"][0]["reason"])

    def test_justified_na_renormalizes_only_applicable_weight(self):
        exclude_displays(self.data)
        criterion(self.data, "research-question")["rating"] = 0
        result = self.score()
        self.assertEqual(result["applicable_weight"], 98)
        self.assertEqual(result["excluded_weight"], 2)
        self.assertEqual(result["assessment_coverage_percent"], 100)
        self.assertEqual(result["score_out_of_100"], round(93 / 98 * 100, 2))
        communication = next(row for row in result["domain_scores"] if row["id"] == "communication")
        self.assertEqual(communication["applicable_weight"], 13)
        self.assertEqual(communication["score_out_of_100"], 100)

    def test_missing_bounds_and_coverage_after_na(self):
        exclude_displays(self.data)
        unassess(criterion(self.data, "research-question"))
        result = self.score()
        self.assertEqual(result["assessment_coverage_percent"], round(93 / 98 * 100, 2))
        self.assertEqual(result["missing_assessment_bounds"], {"lower": round(93 / 98 * 100, 2), "upper": 100})
        self.assertIsNone(result["score_out_of_100"])

    def test_na_requires_permission_reason_and_evidence(self):
        for change in ("missing_reason", "empty_evidence", "core", "not_permitted"):
            with self.subTest(change=change):
                self.data = evaluation_fixture(self.rubric)
                exclude_displays(self.data)
                row = criterion(self.data, "figures-tables")
                if change == "missing_reason":
                    del row["applicability_reason"]
                elif change == "empty_evidence":
                    row["evidence"] = []
                else:
                    row["id"] = "research-question" if change == "core" else "title-abstract"
                    self.data["criteria"] = [item for item in self.data["criteria"] if item is row or item["id"] != row["id"]]
                with self.assertRaises(ValueError):
                    self.score()

    def test_all_na_and_zero_applicable_weight_are_invalid(self):
        self.rubric["rubric_id"] = "custom-toolkit-v2"
        self.data["rubric_id"] = self.rubric["rubric_id"]
        for row in self.rubric["criteria"]:
            row.update(core=False, allow_not_applicable=True)
        for row in self.data["criteria"]:
            row.update(status="not_applicable", rating=None, confidence=None, applicability_reason="Outside documented artifact scope.")
        with self.assertRaisesRegex(ValueError, "all criteria"):
            self.score()
        # One applicable criterion with zero weight still cannot create a denominator.
        unassess(criterion(self.data, "research-question"))
        del criterion(self.data, "research-question")["applicability_reason"]
        for profile in self.rubric["profiles"].values():
            profile["weights"]["motivation-gap"] += profile["weights"]["research-question"]
            profile["weights"]["research-question"] = 0
        with self.assertRaisesRegex(ValueError, "positive applicable weight"):
            self.score()

    def test_zero_weight_unassessed_still_means_incomplete(self):
        self.data["profile"] = "theory"
        weights = self.rubric["profiles"]["theory"]["weights"]
        weights["motivation-gap"] += weights["research-question"]
        weights["research-question"] = 0
        unassess(criterion(self.data, "research-question"))
        result = self.score()
        self.assertEqual(result["assessment_coverage_percent"], 100)
        self.assertEqual(result["status"], "provisional")
        self.assertEqual(result["readiness"], "incomplete")
        self.assertIsNone(result["score_out_of_100"])

    def test_confidence_does_not_multiply_score_but_core_low_confidence_matters(self):
        before = self.score()
        criterion(self.data, "research-question")["confidence"] = "low"
        result = self.score()
        self.assertEqual(result["score_out_of_100"], before["score_out_of_100"])
        self.assertEqual(result["readiness"], "needs_revision_or_evidence")
        self.assertEqual(result["low_confidence_core_checks"][0]["criterion_id"], "research-question")
        criterion(self.data, "research-question")["confidence"] = "medium"
        criterion(self.data, "title-abstract")["confidence"] = "low"
        self.assertEqual(self.score()["readiness"], "reviewed")

    def test_priority_order_distinguishes_unknown_from_observed_failure(self):
        self.data["critical_blockers"] = [blocker()]
        unassess(criterion(self.data, "literature-positioning"))
        criterion(self.data, "research-question")["rating"] = 1
        criterion(self.data, "title-abstract").update(rating=2, action="Narrow the abstract conclusion to the observed finding.")
        priorities = self.score()["revision_priorities"]
        self.assertEqual([row["kind"] for row in priorities], ["critical_blocker", "missing_assessment", "core_deficit", "rated_weakness"])
        self.assertIn("unknown", priorities[1]["reason"])
        self.assertEqual(priorities[-1]["action"], "Narrow the abstract conclusion to the observed finding.")
        self.assertTrue(priorities[0]["evidence"])

    def test_raw_ratings_are_preserved_and_input_is_not_mutated(self):
        original = copy.deepcopy(self.data)
        result = self.score()
        self.assertEqual(self.data, original)
        self.assertEqual(result["criteria"], original["criteria"])
        result["criteria"][0]["evidence"][0]["observation"] = "Changed only returned data"
        self.assertEqual(self.data, original)

    def test_selected_profile_weights_are_used(self):
        criterion(self.data, "research-question")["rating"] = 0
        empirical = self.score()
        self.data["profile"] = "theory"
        theory = self.score()
        self.assertEqual(empirical["score_out_of_100"], 95)
        self.assertEqual(theory["score_out_of_100"], 92)
        self.assertEqual(next(row for row in theory["domain_scores"] if row["id"] == "argument")["nominal_weight"], 23)

    def test_omitted_unknown_duplicate_and_inline_weight_rejected(self):
        for change in ("omitted", "unknown", "duplicate", "inline_weight", "top_weight"):
            with self.subTest(change=change):
                self.data = evaluation_fixture(self.rubric)
                if change == "omitted":
                    self.data["criteria"].pop()
                elif change == "unknown":
                    self.data["criteria"][0]["id"] = "invented-category"
                elif change == "duplicate":
                    self.data["criteria"].append(copy.deepcopy(self.data["criteria"][0]))
                elif change == "inline_weight":
                    self.data["criteria"][0]["weight"] = 100
                else:
                    self.data["weights"] = {"research-question": 100}
                with self.assertRaises(ValueError):
                    self.score()

    def test_canonical_catalog_cannot_be_redefined(self):
        self.rubric["criteria"].pop()
        for profile in self.rubric["profiles"].values():
            profile["weights"]["research-question"] += profile["weights"].pop("venue-compliance")
        with self.assertRaisesRegex(ValueError, "24-criterion"):
            self.score()

    def test_rubric_requires_complete_profile_weights_and_canonical_empirical_weights(self):
        for change in ("missing_weight", "negative", "bad_sum", "inline_catalog_change", "missing_profile"):
            with self.subTest(change=change):
                self.rubric = rubric_fixture()
                weights = self.rubric["profiles"]["empirical-ml"]["weights"]
                if change == "missing_weight":
                    del weights["title-abstract"]
                elif change == "negative":
                    weights["title-abstract"] = -1
                elif change == "bad_sum":
                    weights["title-abstract"] = 100
                elif change == "missing_profile":
                    del self.rubric["profiles"]["clinical"]
                else:
                    weights["title-abstract"] += 1
                    weights["introduction-logic"] -= 1
                with self.assertRaises(ValueError):
                    self.score()

    def test_rubric_anchors_core_domain_and_na_contract(self):
        for change in ("anchor", "same_anchors", "core", "core_na", "domain", "na_permission"):
            with self.subTest(change=change):
                self.rubric = rubric_fixture()
                row = self.rubric["criteria"][0]
                if change == "anchor":
                    del row["anchors"]["0"]
                elif change == "same_anchors":
                    row["anchors"]["0"] = row["anchors"]["1"]
                elif change == "core":
                    row["core"] = False
                elif change == "core_na":
                    row["allow_not_applicable"] = True
                elif change == "domain":
                    row["domain"] = "communication"
                else:
                    self.rubric["criteria"][1]["allow_not_applicable"] = True
                with self.assertRaises(ValueError):
                    self.score()

    def test_different_toolkit_catalog_uses_same_strict_schema(self):
        self.rubric["rubric_id"] = "paper-writing-toolkit-v2"
        self.data["rubric_id"] = self.rubric["rubric_id"]
        self.rubric["criteria"][0]["id"] = "toolkit-scope"
        self.data["criteria"][0]["id"] = "toolkit-scope"
        for profile in self.rubric["profiles"].values():
            profile["weights"]["toolkit-scope"] = profile["weights"].pop("research-question")
        result = self.score()
        self.assertEqual(result["score_out_of_100"], 100)
        self.data["criteria"].pop()
        with self.assertRaises(ValueError):
            self.score()

    def test_assessed_requires_structured_evidence_confidence_and_rationale(self):
        for key, value in (("evidence", []), ("evidence", ["polished prose"]), ("evidence", [{"locator": "§2"}]), ("evidence", [{"locator": "§2", "observation": ""}]), ("confidence", None), ("rationale", " ")):
            with self.subTest(key=key, value=value):
                self.data = evaluation_fixture(self.rubric)
                self.data["criteria"][0][key] = value
                with self.assertRaises(ValueError):
                    self.score()

    def test_unassessed_cannot_keep_numeric_rating_or_confidence(self):
        for key, value in (("rating", 0), ("confidence", "high")):
            with self.subTest(key=key):
                self.data = evaluation_fixture(self.rubric)
                row = self.data["criteria"][0]
                unassess(row)
                row[key] = value
                with self.assertRaises(ValueError):
                    self.score()

    def test_bool_fractional_and_nonfinite_rating_or_weight_rejected(self):
        for value in (True, False, 4.0, -1, 5, float("nan"), float("inf"), -float("inf"), "4"):
            with self.subTest(rating=value):
                self.data = evaluation_fixture(self.rubric)
                self.data["criteria"][0]["rating"] = value
                with self.assertRaises(ValueError):
                    self.score()
        self.data = evaluation_fixture(self.rubric)
        for value in (True, float("nan"), float("inf"), -1, "5"):
            with self.subTest(weight=value):
                self.rubric = rubric_fixture()
                self.rubric["profiles"]["theory"]["weights"]["research-question"] = value
                with self.assertRaises(ValueError):
                    self.score()

    def test_malformed_types_produce_validation_errors(self):
        mutations = [
            lambda d, r: d.update(subject=[]), lambda d, r: d.update(criteria={}),
            lambda d, r: d.update(reviewer="agent"), lambda d, r: d.update(critical_blockers={}),
            lambda d, r: d["criteria"][0].update(id=[]), lambda d, r: d["criteria"][0].update(status=[]),
            lambda d, r: r["criteria"][0].update(domain=[]), lambda d, r: r["criteria"][0].update(anchors=[]),
            lambda d, r: r["criteria"][0].update(core=1), lambda d, r: r.update(profiles=[]),
            lambda d, r: r.update(version=True), lambda d, r: d.update(version=True),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.data, self.rubric = evaluation_fixture(), rubric_fixture()
                mutate(self.data, self.rubric)
                with self.assertRaises(ValueError):
                    self.score()

    def test_dates_ids_and_artifact_hash_are_validated(self):
        for key, value in (("evaluated_at", "2026-02-30"), ("evaluated_at", "20261030"), ("evaluated_at", None), ("profile", "unknown"), ("rubric_id", "other")):
            with self.subTest(key=key, value=value):
                self.data = evaluation_fixture(self.rubric)
                self.data[key] = value
                with self.assertRaises(ValueError):
                    self.score()
        for value in ("A" * 64, "abc", None):
            with self.subTest(hash=value):
                self.data = evaluation_fixture(self.rubric)
                self.data["subject"]["artifact_sha256"] = value
                with self.assertRaises(ValueError):
                    self.score()
        self.data = evaluation_fixture(self.rubric)
        self.data["evaluated_at"] = "2026-10-30T12:04:59+09:00"
        self.assertEqual(self.score()["status"], "complete")

    def test_blocker_reference_evidence_status_and_uniqueness_validated(self):
        for change in ("criterion", "evidence", "status", "duplicate"):
            with self.subTest(change=change):
                self.data = evaluation_fixture(self.rubric)
                item = blocker()
                if change == "criterion":
                    item["criterion_id"] = "invented"
                elif change == "evidence":
                    item["evidence"] = []
                elif change == "status":
                    item["status"] = "probably-fixed"
                self.data["critical_blockers"] = [item, copy.deepcopy(item)] if change == "duplicate" else [item]
                with self.assertRaises(ValueError):
                    self.score()

    def test_fingerprint_covers_content_and_is_key_order_independent(self):
        result = self.score()
        reordered = {key: self.rubric[key] for key in reversed(list(self.rubric))}
        self.assertEqual(result["rubric_sha256"], s.rubric_fingerprint(reordered))
        self.assertEqual(s.score(result, self.rubric)["score_out_of_100"], 100)
        self.rubric["criteria"][0]["anchors"]["4"] += " Additional required check."
        with self.assertRaisesRegex(ValueError, "rubric_sha256"):
            s.score(result, self.rubric)

    def test_comparison_different_revisions_and_same_revision_disagreement(self):
        prior = self.score()
        self.data["subject"]["revision"] = "r2"
        criterion(self.data, "research-question")["rating"] = 2
        different = s.compare_evaluations(prior, self.data, self.rubric)
        self.assertEqual(different["comparison_kind"], "different_revisions")
        self.assertEqual(different["total_score_delta"], -2.5)
        self.assertEqual(different["criterion_deltas"][0]["rating_delta"], -2)
        self.data["subject"]["revision"] = "r1"
        self.data["reviewer"]["id"] = "second-reviewer"
        same = s.compare_evaluations(prior, self.data, self.rubric)
        self.assertEqual(same["comparison_kind"], "same_revision_assessments")
        self.assertIn("rater disagreement", same["limitations"])
        self.assertEqual(same["current_reviewer"]["id"], "second-reviewer")

    def test_comparison_missing_coverage_has_no_total_or_missing_to_zero_delta(self):
        prior = self.score()
        unassess(criterion(self.data, "research-question"))
        comparison = s.compare_evaluations(prior, self.data, self.rubric)
        self.assertIsNone(comparison["total_score_delta"])
        self.assertIn("complete", comparison["total_score_delta_reason"])
        self.assertIsNone(comparison["criterion_deltas"][0]["rating_delta"])
        self.assertIn("not zero", comparison["criterion_deltas"][0]["rating_delta_reason"])
        self.assertEqual(comparison["current_coverage_percent"], 95)

    def test_comparison_changed_applicability_suppresses_total_delta(self):
        prior = self.score()
        exclude_displays(self.data)
        comparison = s.compare_evaluations(prior, self.data, self.rubric)
        self.assertIsNone(comparison["total_score_delta"])
        self.assertFalse(comparison["applicability_patterns_match"])
        self.assertIn("denominators", comparison["total_score_delta_reason"])
        display_delta = next(row for row in comparison["criterion_deltas"] if row["id"] == "figures-tables")
        self.assertIsNone(display_delta["rating_delta"])

    def test_comparison_rejects_other_subject_profile_fingerprint_or_raw_prior(self):
        prior = self.score()
        for change in ("subject", "profile", "fingerprint", "raw_prior", "v1"):
            with self.subTest(change=change):
                self.data = evaluation_fixture(self.rubric)
                before = copy.deepcopy(prior)
                if change == "subject":
                    self.data["subject"]["id"] = "other-manuscript"
                elif change == "profile":
                    self.data["profile"] = "theory"
                elif change == "fingerprint":
                    before["rubric_sha256"] = "f" * 64
                elif change == "raw_prior":
                    del before["rubric_sha256"]
                else:
                    before["version"] = 1
                with self.assertRaises(ValueError):
                    s.compare_evaluations(before, self.data, self.rubric)

    def test_markdown_exposes_blocker_unknown_and_evidence_without_false_approval(self):
        self.data["critical_blockers"] = [blocker()]
        unassess(criterion(self.data, "motivation-gap"))
        report = s.render_markdown(self.score(), self.rubric)
        for fragment in ("revision: **r1**", "empirical-ml", "Rubric SHA-256", "readiness: blocked", "Score: not available", "coverage: 95%", "abstract line 4; results §3", "Missing-assessment bounds", "not statistical confidence intervals", "not submission approval", "unknown", "## Domains", "## Criteria"):
            self.assertIn(fragment, report)
        self.assertNotIn("ready to submit", report.lower())
        self.assertNotIn("submission approved", report.lower())

    def test_v1_compatibility_and_blocker_visibility(self):
        data = {"version": 1, "criteria": [{"id": "a", "weight": 80, "rating": 3, "evidence": ["Observed passage"]}, {"id": "b", "weight": 20, "rating": 4, "evidence": ["Verified artifact"]}]}
        result = s.score(data)
        self.assertEqual(result["score_out_of_100"], 80)
        self.assertEqual(result["assessed_weight_percent"], 100)
        data["critical_blockers"] = ["Unresolved evidence gap"]
        result = s.score(data)
        self.assertEqual(result["score_out_of_100"], 80)
        self.assertEqual(result["readiness"], "blocked")
        self.assertIn("Unresolved evidence gap", s.render_markdown(result))

    def test_v2_requires_rubric_and_version_typos_cannot_fall_back_to_v1(self):
        with self.assertRaisesRegex(ValueError, "separate rubric"):
            s.score(self.data)
        for version in ("2", 3, True):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    s.score({"version": version, "criteria": [{"id": "a", "weight": 100, "rating": 4, "evidence": ["x"]}]})

    def test_cli_writes_report_and_comparison_and_v1_still_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inp, rubric, out, report, prior = [root / name for name in ("input.json", "rubric.json", "out.json", "report.md", "prior.json")]
            inp.write_text(json.dumps(self.data), encoding="utf-8")
            rubric.write_text(json.dumps(self.rubric), encoding="utf-8")
            prior.write_text(json.dumps(self.score()), encoding="utf-8")
            command = [sys.executable, str(SCRIPT), str(inp), "--rubric", str(rubric), "--out", str(out), "--markdown", str(report), "--compare", str(prior)]
            run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["comparison"]["total_score_delta"], 0)
            self.assertIn("## Assessment comparison", report.read_text(encoding="utf-8"))
            legacy = {"criteria": [{"id": "a", "weight": 100, "rating": 3, "evidence": ["Observed evidence"]}]}
            inp.write_text(json.dumps(legacy), encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(inp)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["score_out_of_100"], 75)

    def test_cli_rejects_duplicate_keys_nonfinite_and_v2_without_rubric(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "input.json"
            for source in ('{"criteria":[],"criteria":[]}', '{"criteria":[],"extra":NaN}', json.dumps(self.data)):
                with self.subTest(source=source[:50]):
                    inp.write_text(source, encoding="utf-8")
                    run = subprocess.run([sys.executable, str(SCRIPT), str(inp)], capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(run.returncode, 2)
                    self.assertIn("Invalid evaluation", run.stderr)
                    self.assertNotIn("Traceback", run.stderr)


if __name__ == "__main__":
    unittest.main()
