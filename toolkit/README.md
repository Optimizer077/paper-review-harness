# Paper writing toolkit

A portable scientific writing skill, mechanical manuscript audit, independent reviewer packet workflow, and evidence-backed editorial scoring tools. The audit and scorer use Python's standard library; they do not call an AI service.

Start with [the skill](paper-writing/SKILL.md), [harness commands](paper-writing/references/harness-guide.md), and [the scorecard](paper-writing/references/evaluation-scorecard.md). Run commands below from this toolkit directory.

```sh
python paper-writing/scripts/paper_harness.py --help
python paper-writing/scripts/paper_harness.py audit examples/manuscript.md --context examples/project.json --out audit.json
python paper-writing/scripts/paper_harness.py plan examples/manuscript.md --context examples/project.json --out review-plan.json
python paper-writing/scripts/score_evaluation.py --help
python -m unittest discover -s validation -p 'test*.py' -v
```

The examples contain explicitly invented data for software validation. Generated review packets are tasks, not completed reviews. Audit passes, declared evidence, and editorial scores do not verify scientific truth or predict acceptance.

The manuscript rubric defines 24 anchored criteria across five domains, with empirical ML, theory, clinical, and systematic-review contribution profiles. Choose the relevant profile, supply inspected evidence and rationale, and report coverage and blockers alongside scores.

The scorer also includes an explicit aggressive scoring policy in `paper-writing/assets/scoring-policies.json`; consult `score_evaluation.py --help` and the scorecard for selection and interpretation. The aggressive policy changes scoring expectations, not the scientific evidence available.

## Historical citations and access

`research/historical-2022/papers.jsonl` contains 300 stable citation IDs with authors, venues, source links and bounded inspection provenance. This is a metadata-only export: zero local abstracts and zero article bodies. The original collection recorded 300 abstracts and 238 available bodies; those original counts are explicitly distinguished in `summary.json`. The accompanying specialist notes are original editorial observations, not complete article reviews. No journal full articles are mirrored. Use original publisher or repository links to inspect sources under their applicable access terms.

Collectors remain available as source code. They require the optional packages in `paper-writing/scripts/corpus-requirements.txt` and perform network access only when explicitly run. Collection metadata, downloads and selected-section inspection are separate evidence levels.

## Reproducing the public export

```sh
python publish_toolkit.py --source PATH_TO_OUTPUT_ROOT --dest PATH_TO_NEW_PUBLIC_TOOLKIT
```

The exporter uses a narrow allowlist, removes source abstracts and local body paths, converts known host-specific Markdown paths, rejects unrecognized home paths and common credentials, and emits a deterministic SHA-256 `public-manifest.json`. It excludes private drafts, research sessions, assessments, raw logs, archives and downloaded bodies. Re-running may replace only a destination previously marked by this exporter.
