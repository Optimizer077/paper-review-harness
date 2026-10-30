#!/usr/bin/env python3
"""Compare browser arithmetic with Python using fictional bundled-profile cases.

Run from any directory with Python 3.10+ and Node.js 20+ installed.
This checks software arithmetic, not the quality of editorial judgments.
"""
import copy
import importlib.util
import json
from pathlib import Path
import random
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "scorer", ROOT / "toolkit/paper-writing/scripts/score_evaluation.py")
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main():
    rubric = load("docs/data/manuscript-rubric.json")
    policies = load("docs/data/scoring-policies.json")
    base = load("docs/data/demo-assessment.json")
    assert rubric == load("toolkit/paper-writing/assets/manuscript-rubric.json")
    assert policies == load("toolkit/paper-writing/assets/scoring-policies.json")
    rng, cases = random.Random(413), []
    for profile in rubric["profiles"]:
        for mode in ("standard", "aggressive"):
            for scenario in range(22):
                data = copy.deepcopy(base)
                data.update(profile=profile, strictness=mode, critical_blockers=[])
                for row in data["criteria"]:
                    row.update(rating=4, confidence="high")
                    if scenario < 5:
                        row["rating"] = scenario
                    elif scenario >= 10:
                        row.update(rating=rng.randrange(5),
                                   confidence=rng.choice(["high", "medium", "low"]))
                if scenario == 5:
                    data["critical_blockers"] = copy.deepcopy(base["critical_blockers"])
                if scenario == 6:
                    data["criteria"][0].update(status="unassessed", rating=None,
                                               confidence=None, evidence=[])
                if scenario == 7:
                    row = next(r for r in data["criteria"] if r["id"] == "figures-tables")
                    row.update(status="not_applicable", rating=None, confidence=None,
                               applicability_reason="Synthetic display-free artifact.")
                if scenario == 8:
                    data["criteria"][0]["confidence"] = "medium"
                if scenario == 9:
                    data["criteria"][0]["rating"] = 2
                cases.append(data)
    javascript = """
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const {scoreAssessment}=await import(pathToFileURL(process.argv[1]).href);
process.stdout.write(JSON.stringify(input.cases.map(d=>scoreAssessment(d,input.rubric,input.policies))));
"""
    process = subprocess.run(
        ["node", "--input-type=module", "-e", javascript,
         str(ROOT / "docs/scoring-engine.js")],
        input=json.dumps(dict(cases=cases, rubric=rubric, policies=policies)),
        capture_output=True, text=True, encoding="utf-8", check=True)
    results = json.loads(process.stdout)
    fields = ("score_out_of_100", "effective_score_out_of_100", "score_cap_out_of_100",
              "strictness", "scoring_policy_sha256", "rubric_sha256", "readiness",
              "status", "assessment_coverage_percent", "domain_scores",
              "missing_assessment_bounds", "score_caps", "strict_gate_failures")
    errors = []
    for index, (data, browser) in enumerate(zip(cases, results)):
        python = scorer.score(data, rubric)
        for field in fields:
            if browser.get(field) != python.get(field):
                errors.append(dict(case=index, field=field,
                                   python=python.get(field), browser=browser.get(field)))
    if len(results) != len(cases):
        errors.append(dict(error="Browser result count differs"))
    print(json.dumps(dict(cases=len(cases), mismatches=len(errors)), indent=2))
    if errors:
        print(json.dumps(errors[:3], indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
