"""Offline regressions for the conservative writing-review harness."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

OUTPUT = Path(__file__).resolve().parents[1]
SCRIPT = OUTPUT / "paper-writing" / "scripts" / "paper_harness.py"
spec = importlib.util.spec_from_file_location("paper_harness", SCRIPT)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.context = json.loads((OUTPUT / "examples" / "project.json").read_text(encoding="utf-8"))
        self.text = (OUTPUT / "examples" / "manuscript.md").read_text(encoding="utf-8")
        h.validate_context(self.context)

    def codes(self, text=None, context=None):
        return [f["code"] for f in h.audit(text or self.text, context or self.context)["findings"]]

    def test_fixture_usable_and_does_not_claim_semantic_verification(self):
        result = h.audit(self.text, self.context)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["manual_review_needed"])
        self.assertNotIn("quality_score", result)

    def test_locked_fact_mismatch_has_location(self):
        text = self.text.replace("82.4%", "83.4%", 1)
        findings = h.audit(text, self.context)["findings"]
        mismatch = next(f for f in findings if f["code"] == "locked_fact_mismatch")
        self.assertEqual(mismatch["severity"], "error")
        self.assertGreater(mismatch["location"]["line"], 1)

    def test_numerically_equal_locked_value_allowed(self):
        self.assertNotIn("locked_fact_mismatch", self.codes(self.text.replace("82.4%", "82.40%")))

    def test_unassociated_fact_is_warning_not_fabricated_verification(self):
        text = self.text.replace("Test accuracy was", "The measured value was").replace("test accuracy was", "the measured value was")
        self.assertIn("locked_fact_unverified", self.codes(text))

    def test_allowed_aliases_are_not_inconsistency(self):
        self.assertNotIn("terminology_inconsistent", self.codes())
        self.assertNotIn("terminology_inconsistent", self.codes(self.text.replace("uncertainty gate", "confidence gate")))

    def test_disallowed_alias_is_inconsistency(self):
        self.assertIn("terminology_inconsistent", self.codes(self.text.replace("uncertainty gate", "reliability engine")))

    def test_undefined_markdown_and_tex_citations(self):
        for citation in ("[@absent]", r"\citep[see][p. 2]{absent,synthetic-results}"):
            self.assertIn("undefined_citation", self.codes(self.text + "\n" + citation))

    def test_bare_email_is_not_a_citation(self):
        self.assertNotIn("undefined_citation", self.codes(self.text + "\nContact person@example.org."))

    def test_placeholder_warning(self):
        self.assertIn("unresolved_placeholder", self.codes(self.text + "\nTODO add results"))

    def test_acronym_first_use_definition_heuristic(self):
        self.assertIn("acronym_definition", self.codes(self.text + "\nWe use ABC here."))
        self.assertNotIn("acronym_definition", self.codes(self.text + "\nWe use adaptive batch calibration (ABC) here."))

    def test_section_limit_and_prohibited_claim_are_errors(self):
        ctx = copy.deepcopy(self.context)
        ctx["sections"][0]["max_words"] = 1
        result = h.audit(self.text + "\nThis is clinically validated.", ctx)
        self.assertEqual(result["counts"]["error"], 2)

    def test_rejects_wrong_type_evidence_and_unknown_ids(self):
        for value in ("synthetic-results", [42], ["unknown-source"]):
            ctx = copy.deepcopy(self.context)
            ctx["claims"][0]["evidence_ids"] = value
            with self.assertRaises(h.InputError):
                h.validate_context(ctx)

    def test_rejects_unsupported_required_claim(self):
        ctx = copy.deepcopy(self.context)
        ctx["claims"][0]["status"] = "pending"
        with self.assertRaisesRegex(h.InputError, "unsupported"):
            h.validate_context(ctx)

    def test_rejects_broken_and_duplicate_ids(self):
        for value in ("invalid id", "synthetic-results"):
            ctx = copy.deepcopy(self.context)
            ctx["sources"][1]["id"] = value
            with self.assertRaises(h.InputError):
                h.validate_context(ctx)

    def test_dependency_cycle_rejected(self):
        ctx = copy.deepcopy(self.context)
        ctx["sections"][1]["depends_on"] = ["results"]
        with self.assertRaisesRegex(h.InputError, "Cyclic"):
            h.validate_context(ctx)

    def test_packet_keeps_transitive_dependencies_and_all_global_guardrails(self):
        ctx = copy.deepcopy(self.context)
        ctx["extra_global_policy"] = {"must_preserve": "retain this entire extension"}
        packet = h.build_packet(self.text, ctx, "results")
        self.assertEqual([s["id"] for s in packet["dependencies"]], ["introduction", "methods"])
        for key in ("guardrails", "prohibited_claims", "locked_facts", "terminology", "extra_global_policy"):
            self.assertEqual(packet["global_context"][key], ctx[key])
        self.assertEqual({s["id"] for s in packet["sources"]}, {"synthetic-results", "synthetic-protocol"})

    def test_cited_source_not_in_required_claims_still_in_packet(self):
        ctx = copy.deepcopy(self.context)
        ctx["sections"][1]["required_claims"] = []
        text = self.text.replace("## Methods", "A prior protocol is described elsewhere [@synthetic-protocol].\n\n## Methods")
        packet = h.build_packet(text, ctx, "introduction")
        self.assertEqual([s["id"] for s in packet["sources"]], ["synthetic-protocol"])

    def test_packet_budget_fails_without_clipping_or_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet.json"
            code = h.main(["packet", str(OUTPUT / "examples/manuscript.md"), "--context", str(OUTPUT / "examples/project.json"),
                           "--section", "results", "--max-chars", "100", "--out", str(out)])
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())
        packet = h.build_packet(self.text, self.context, "abstract")
        maximum = len(h.encoded(packet))
        self.assertIs(h.enforce_budget(packet, maximum), packet)
        with self.assertRaises(h.InputError):
            h.enforce_budget(packet, maximum - 1)

    def test_common_tex_sections_and_abstract(self):
        text = "\\begin{abstract}\nTest accuracy was 82.4%.\n\\end{abstract}\n"
        for s in self.context["sections"][1:]:
            text += "\\section{" + s["heading"] + "}\n"
            if s["id"] == "results":
                text += "Test accuracy was 82.4%. Automatic coverage was 71.0%.\n"
            else:
                text += "Ordinary section text.\n"
        self.assertNotIn("missing_section", self.codes(text))
        self.assertNotIn("locked_fact_mismatch", self.codes(text))

    def plan(self):
        return h.build_plan(self.text, self.context, h.load_roles())

    def passed_report(self, plan, role):
        return {"version": 1, "role_id": role, "manuscript_sha256": plan["manuscript_sha256"],
                "context_sha256": plan["context_sha256"], "verdict": "pass", "findings": [],
                "checks": [{"id": "reasoning", "check_type": "semantic", "status": "passed", "reviewed_by": "agent",
                            "reviewer": "synthetic-test-agent", "evidence": ["Synthetic manuscript lines 5-7; this is a software fixture review."],
                            "rationale": "Synthetic fixture review for merge validation only."}]}

    def save_reports(self, directory, reports):
        paths = []
        for i, report in enumerate(reports):
            path = Path(directory) / (str(i) + ".json")
            path.write_text(json.dumps(report), encoding="utf-8")
            paths.append(path)
        return paths

    def test_plan_has_ten_roles_and_does_not_dispatch(self):
        plan = self.plan()
        self.assertEqual(len(plan["tasks"]), 10)
        self.assertEqual(len(set(plan["expected_role_ids"])), 10)
        self.assertEqual(plan["execution"], "packets_only_no_agents_dispatched")

    def test_readability_packet_does_not_leak_author_answer_key(self):
        packet = next(t for t in self.plan()["tasks"] if t["role_id"] == "readability")
        for key in ("context", "global_context", "claims", "section_packets", "sources"):
            self.assertNotIn(key, packet)
        self.assertIn("comparison_context_file", packet)
        self.assertIn("teach-back", packet["instructions"])

    def test_plan_exports_separate_packets_and_comparison_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "plan.json"
            code = h.main(["plan", str(OUTPUT / "examples/manuscript.md"), "--context", str(OUTPUT / "examples/project.json"), "--out", str(target)])
            self.assertEqual(code, 0)
            manifest = h.load_json(target)
            self.assertNotIn("context", manifest)
            self.assertNotIn("manuscript", manifest)
            self.assertEqual(len(manifest["tasks"]), 10)
            for task in manifest["tasks"]:
                self.assertTrue(Path(task["packet_file"]).exists())
            blind = next(t for t in manifest["tasks"] if t["role_id"] == "readability")
            self.assertTrue(Path(h.load_json(blind["packet_file"])["comparison_context_file"]).exists())

    def test_plan_budget_overflow_writes_no_manifest_or_packets(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "plan.json"
            code = h.main(["plan", str(OUTPUT / "examples/manuscript.md"), "--context", str(OUTPUT / "examples/project.json"),
                           "--max-chars", "100", "--out", str(target)])
            self.assertEqual(code, 2)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_complete_reviews_accept_agent_semantic_review(self):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.save_reports(tmp, [self.passed_report(plan, role) for role in plan["expected_role_ids"]])
            result = h.merge_reviews(plan, paths)
            self.assertEqual((result["status"], result["verdict"]), ("complete", "pass"))
            self.assertEqual(result["check_summary"]["semantic"], 10)

    def test_malformed_pass_cannot_yield_pass(self):
        plan = self.plan()
        for corruption in ("checks", "revision", "contradiction", "evidence", "attribution", "wrong-type"):
            reports = [self.passed_report(plan, role) for role in plan["expected_role_ids"]]
            bad = reports[0]
            if corruption == "checks":
                bad["checks"] = []
            elif corruption == "revision":
                bad["manuscript_sha256"] = "0" * 64
            elif corruption == "contradiction":
                bad["findings"] = [{"id": "unresolved", "severity": "error", "check_type": "semantic", "message": "Unresolved."}]
            elif corruption == "evidence":
                bad["checks"][0]["evidence"] = []
            elif corruption == "attribution":
                bad["checks"][0].pop("reviewed_by")
            else:
                bad["checks"] = "passed"
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as tmp:
                result = h.merge_reviews(plan, self.save_reports(tmp, reports))
                self.assertEqual(result["status"], "incomplete")
                self.assertEqual(result["verdict"], "blocked")
                self.assertTrue(result["invalid_reviews"])

    def test_missing_role_critical_blocker_and_pending_semantics_incomplete(self):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as tmp:
            reports = [self.passed_report(plan, role) for role in plan["expected_role_ids"]]
            reports[0]["verdict"] = "blocked"
            reports[0]["findings"] = [{"id": "critical", "severity": "critical", "check_type": "semantic", "message": "Evidence unavailable."}]
            result = h.merge_reviews(plan, self.save_reports(tmp, reports[:-1]))
            self.assertEqual(result["status"], "incomplete")
            self.assertTrue(result["critical_blockers"])
            self.assertEqual(len(result["missing_roles"]), 1)
        reports = [self.passed_report(plan, role) for role in plan["expected_role_ids"]]
        reports[0]["verdict"] = "revise"
        reports[0]["checks"][0]["status"] = "needs_review"
        with tempfile.TemporaryDirectory() as tmp:
            result = h.merge_reviews(plan, self.save_reports(tmp, reports))
            self.assertEqual(result["status"], "incomplete")
            self.assertTrue(result["pending_semantic_checks"])

    def test_duplicate_report_not_silently_accepted(self):
        plan = self.plan()
        reports = [self.passed_report(plan, role) for role in plan["expected_role_ids"]]
        reports.append(reports[0])
        with tempfile.TemporaryDirectory() as tmp:
            result = h.merge_reviews(plan, self.save_reports(tmp, reports))
            self.assertEqual(result["status"], "incomplete")
            self.assertTrue(result["invalid_reviews"])

    def test_explicit_missing_roles_path_rejected(self):
        with self.assertRaises(h.InputError):
            h.load_roles(OUTPUT / "validation/missing/review-roles.json")

    def test_cli_help_and_exit_codes(self):
        help_result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("audit", help_result.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            result_file = Path(tmp) / "audit.json"
            args = ["audit", str(OUTPUT / "examples/manuscript.md"), "--context", str(OUTPUT / "examples/project.json"), "--out", str(result_file)]
            self.assertEqual(h.main(args), 0)
            self.assertTrue(h.load_json(result_file)["manual_review_needed"])
            bad_text = Path(tmp) / "bad.md"
            bad_text.write_text(self.text + "\n[@missing]", encoding="utf-8")
            args[1] = str(bad_text)
            self.assertEqual(h.main(args), 1)
            args[3] = str(Path(tmp) / "missing.json")
            self.assertEqual(h.main(args), 2)


if __name__ == "__main__":
    unittest.main()
