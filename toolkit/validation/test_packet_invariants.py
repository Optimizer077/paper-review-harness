"""Cross-section editorial invariants that must survive packet selection."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

OUTPUT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("invariant_harness", OUTPUT / "paper-writing/scripts/paper_harness.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class ContextInvariants(unittest.TestCase):
    def setUp(self):
        self.ctx = json.loads((OUTPUT / "examples/project.json").read_text(encoding="utf-8"))
        self.text = (OUTPUT / "examples/manuscript.md").read_text(encoding="utf-8")

    def test_nonselected_uncertain_claims_and_evidence_remain_available(self):
        self.ctx["sources"].append({"id": "counterevidence", "title": "Synthetic contrary result",
                                    "url": "https://example.invalid/counter", "locator": "row 9",
                                    "excerpt": "Synthetic data do not establish external generalization."})
        for status in ("pending", "unsupported"):
            self.ctx["claims"].append({"id": "external-" + status, "statement": "External use remains unestablished.",
                                       "status": status, "evidence_ids": ["counterevidence"]})
        h.validate_context(self.ctx)
        packet = h.build_packet(self.text, self.ctx, "abstract")
        self.assertEqual({x["status"] for x in packet["global_claim_guardrails"]}, {"pending", "unsupported"})
        self.assertTrue(any(x["id"] == "counterevidence" and "do not establish" in x["excerpt"] for x in packet["sources"]))

    def test_skill_unresolved_marker_is_reported(self):
        result = h.audit(self.text + "\n[unresolved: source unavailable]", self.ctx)
        self.assertTrue(any(x["code"] == "unresolved_placeholder" for x in result["findings"]))

    def test_abstract_definition_does_not_define_body_acronym(self):
        text = self.text.replace("We test a confidence gate", "We test an uncertainty gate (UG)")
        text = text.replace("Image classification systems", "UG classification systems")
        findings = h.audit(text, self.ctx)["findings"]
        warnings = [x for x in findings if x["code"] == "acronym_definition" and "'UG'" in x["message"]]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["scope"], "body")
        self.assertGreater(warnings[0]["location"]["line"], 7)

    def test_defining_in_both_scopes_removes_acronym_warning(self):
        text = self.text.replace("We test a confidence gate", "We test an uncertainty gate (UG)")
        text = text.replace("Image classification systems", "An uncertainty gate (UG) helps classification systems")
        findings = h.audit(text, self.ctx)["findings"]
        self.assertFalse(any(x["code"] == "acronym_definition" and "'UG'" in x["message"] for x in findings))

    def test_signed_locked_fact_keeps_sign(self):
        self.ctx["locked_facts"] = [{"id": "difference", "label": "difference", "value": "-0.5", "sections": ["results"]}]
        correct = self.text.replace("Test accuracy was 82.4% at the selected operating point", "The difference was -0.5 at the selected operating point")
        self.assertFalse(any(x["code"] == "locked_fact_mismatch" for x in h.audit(correct, self.ctx)["findings"]))
        wrong = correct.replace("difference was -0.5", "difference was 0.5")
        self.assertTrue(any(x["code"] == "locked_fact_mismatch" for x in h.audit(wrong, self.ctx)["findings"]))


if __name__ == "__main__":
    unittest.main()
