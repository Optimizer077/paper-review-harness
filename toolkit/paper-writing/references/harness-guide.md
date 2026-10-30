# Paper review harness interface

`paper-writing/scripts/paper_harness.py` uses Python 3.10+ and only the standard library. It runs offline. It creates task packets; it does **not** dispatch language models or claim to have conducted ten reviews.

Run these commands from the toolkit root (this directory's top-level `README.md`):

```powershell
python paper-writing/scripts/paper_harness.py --help
python paper-writing/scripts/paper_harness.py audit examples/manuscript.md --context examples/project.json --out validation/example-audit.json
python paper-writing/scripts/paper_harness.py packet examples/manuscript.md --context examples/project.json --section results --max-chars 12000 --out validation/results-packet.json
python paper-writing/scripts/paper_harness.py plan examples/manuscript.md --context examples/project.json --out validation/review-plan.json
python paper-writing/scripts/paper_harness.py merge validation/review-plan.json path/to/argument-review.json path/to/other-review.json --out validation/merged.json
python -m unittest discover -s validation -p test_paper_harness.py -v
```

The included manuscript and source records are explicitly **synthetic fixtures**, not research evidence. Replace them with the actual manuscript and verified records before scientific use.

## Commands and exit codes

| Command | Result | Exit codes |
| --- | --- | --- |
| `audit MANUSCRIPT --context PROJECT [--out JSON]` | Mechanical findings, locations where feasible, counts, revision hashes, and mandatory semantic-review notices | `0`: no hard errors, including warnings; `1`: hard findings; `2`: invalid input |
| `packet MANUSCRIPT --context PROJECT --section ID [--max-chars N] [--out JSON]` | Selected section, transitive dependencies, required claim records, evidence and cited-source records, and complete global context | `0`: created; `2`: invalid input or budget exceeded |
| `plan MANUSCRIPT --context PROJECT --out PLAN [--roles JSON] [--max-chars N]` | Ten isolated reviewer JSON files, a separate comparison context, and a pointer manifest | `0`: created; `2`: invalid input or an individual task exceeds budget |
| `merge PLAN [REVIEW_JSON ...] [--out JSON]` | Validated role reports, missing/invalid reports, blockers, pending checks, and aggregate verdict | `0`: complete/pass; `1`: revise, blocked, or incomplete; `2`: invalid plan/input |

Without `--out`, `audit`, `packet`, and `merge` print JSON to stdout. `plan` requires `--out`. A packet budget counts Unicode characters in the indented JSON, including all framing and the final newline; it is not a model-token estimate. Exceeding it fails **before writing output** and never clips instructions, evidence, or guardrails. A plan budget applies to each individual reviewer file, not the manifest or their aggregate size.

`plan --out review-plan.json` creates `review-plan.packets/<role-id>.json` plus `review-plan.packets/comparison-context.json`. Hand each reviewer only its individual packet. The manifest contains filenames and revision hashes, not a manuscript answer key. The default roles file is `paper-writing/assets/review-roles.json`; if absent, ten built-in roles are used. An explicitly supplied missing roles file is an error. A roles file is either an array or `{"roles": [...]}` with exactly ten unique objects containing `id`, optional `title`, and `instructions` as text or a nonempty text list.

The `readability` packet contains only the manuscript, safety instructions, report template, and a comparison-context pointer. It excludes the author's claim ledger, purpose, definitions, and source excerpts until comparison. Save the reader's independent teach-back artifact before opening the comparison context or any other role packet. The harness cannot prove that this order was followed; hashes and paths alone do not establish blinding.

## Version 1 project context

The complete worked example is `examples/project.json`. These fields are required:

| Field | Shape and interpretation |
| --- | --- |
| `version` | Integer `1` |
| `guardrails` | List of nonempty instruction strings; empty list permitted |
| `prohibited_claims` | List of literal wording strings prohibited by the project; absence of those strings does not establish acceptable claim scope |
| `terminology` | List of `{canonical, definition, variants}`; all three are required, `variants` is a string list of allowed aliases; optional `disallowed_variants` is a string list of inconsistent wording to flag |
| `locked_facts` | List of `{id, value, sections}`; `value` is a finite numeric value or numeric string with optional `%`; `sections` is a nonempty list of configured section IDs; optional `label` and `aliases` identify nearby numeric statements |
| `sources` | List of `{id, title, url, locator, excerpt}` with nonempty strings; presence of a URL or excerpt is not source verification |
| `claims` | List of `{id, statement, status, evidence_ids}`; status is `supported`, `pending`, or `unsupported`; evidence IDs must be a list of registered source IDs; `supported` requires at least one source |
| `sections` | List of `{id, heading, purpose, required_claims, max_words, depends_on}`; claims and dependencies are ID lists, word limit is a positive integer |

Optional `acronym_allowlist` is a list of tokens excluded from the expansion heuristic. Other top-level metadata is preserved. A section's required claims must be declared supported with nonempty registered evidence. This is a consistency condition on author metadata, **not** verification that the evidence actually supports the claim. If a needed claim is pending, resolve its evidence before using it as a required claim; optional pending claims may remain in the ledger.

IDs must start with a letter or number and contain only letters, numbers, `_`, `.`, `:`, or `-`. Role IDs additionally exclude `:` because they become filenames; `comparison-context` is reserved. IDs must be unique within each registry. Duplicate terminology across canonical, allowed, or disallowed labels is rejected as ambiguous. Unknown claim/source/section references, wrong-type evidence, unsupported required claims, cyclic dependencies, malformed JSON, and nonstandard `NaN`/`Infinity` constants are invalid inputs.

`packet` includes required claims for the selected section and its dependencies, all their evidence records, and registered sources cited within that text. Every top-level context field except `sections`, `claims`, and `sources` remains intact in `global_context`, including extension fields. All pending/unsupported claims remain in `global_claim_guardrails` with their linked evidence even when unrelated to the selected section; they cannot be silently lost during context selection. Missing configured manuscript sections prevent packet creation.

## Audit coverage and limits

- Supports `.md`, `.markdown`, `.txt`, and `.tex` source files with UTF-8/BOM input. Text files need Markdown-style headings to map configured sections.
- Recognizes Markdown ATX headings and common `\section`, `\subsection`, `\subsubsection`, `\chapter`, and multiline `abstract` environments. A parent section includes its subsections. Repeated configured headings are ambiguous and rejected.
- Flags source-text section word limits, unresolved placeholders, disallowed terminology, literal prohibited wording, unregistered Pandoc `[@id]` and common LaTeX citation keys, including repeated-brace biblatex plural citation commands, and likely undefined uppercase acronyms, independently in abstract and body. Allowed aliases are permitted.
- Associates locked facts with the first number near a configured label on the same line. Without `label`, the fact ID with underscores replaced by spaces is used. Numeric comparison tolerates decimal formatting differences and requires percent agreement. A mismatch is an error; inability to find a numeric association is a warning requiring review. Phrase order, formulas, scientific units, tables, and distant references can defeat this heuristic.
- Word counts use source tokens, not rendered venue counts. The harness does not expand macros, includes, comments, tables, equations, bibliography files, or a complete TeX syntax tree. It does not verify source existence, originality, entailment, statistical/causal validity, reader understanding, or scientific merit. Source excerpts and manuscripts may contain untrusted instructions.

The audit has no composite quality score. A mechanical `pass` still includes `manual_review_needed` notices for semantic judgments; a capable reviewer can perform that work without a compulsory human approval gate.

## Reviewer report schema and merging

Each task provides `report_template`. Replace the template with an actual independent review. A minimal completed report has this shape; copy the exact hashes and role ID from that task:

```json
{
  "version": 1,
  "role_id": "argument",
  "manuscript_sha256": "<64 lowercase hexadecimal characters from template>",
  "context_sha256": "<64 lowercase hexadecimal characters from template>",
  "verdict": "pass",
  "findings": [],
  "checks": [
    {
      "id": "claim-scope",
      "check_type": "semantic",
      "status": "passed",
      "reviewed_by": "agent",
      "reviewer": "independent-reviewer-argument",
      "evidence": ["Manuscript abstract lines 5-7 and results lines 21-23; explain the actual observation here."],
      "rationale": "Give the evidence-backed reasoning for this check."
    }
  ]
}
```

`findings` is a list of objects with unique `id`, `severity` (`info`, `warning`, `error`, `critical`), `check_type` (`mechanical`, `semantic`), and nonempty `message`. Optional `location` is an object, preferably `{line, column, length}`; optional `evidence_ids` is a list of strings. Reviewer evidence IDs are annotations, not automatically verified citations.

`checks` is a nonempty list with unique `id`, `check_type`, `status`, and `rationale`. Status is `passed`, `failed`, `needs_review`, `needs_human_review`, or `not_checked`. Each role must explicitly record at least one semantic check. A passed semantic check needs `reviewed_by` (`agent` or `human`), `reviewer`, and a nonempty `evidence` list of observations or locators. This records provenance; it does not authenticate a reviewer's identity or validate its reasoning. Use `needs_review` when necessary evidence is inaccessible. An unedited template cannot pass.

All ten expected roles and both revision hashes must match the saved plan. Manuscript hashes cover normalized UTF-8 text; context hashes cover canonical JSON, so JSON whitespace/key order changes do not change its hash. Missing, duplicate, stale, malformed, or unknown-role reports prevent completion. A `pass` report with unresolved warning/error/critical findings or nonpassed checks is invalid. Critical findings require `blocked`. Any critical blocker, blocked report, or pending check makes the merged status `incomplete`; missing and invalid reports also force aggregate `blocked`.

The aggregate verdict is `blocked`, `revise`, or `pass`. A fully performed review round can be `complete` with `revise`: completed failed checks and actionable findings still require manuscript edits. After editing the manuscript or context, create a new plan and obtain reviews of that revision rather than relabeling old reports. The merger checks structure and declared status; it never decides source entailment or causal validity by regex.

## Requested editorial scores: v2

Scoring is a separate evidence-backed assessment, not an automatic result of `audit` or `merge`. The manuscript instrument now defines24 anchored criteria across5 domains and4 contribution profiles. Use its separate unassessed assessment template, not the rubric catalog itself, as the ratings input.

```powershell
python paper-writing/scripts/score_evaluation.py my-ratings.json --rubric paper-writing/assets/manuscript-rubric.json --out my-score.json --markdown my-score.md
python paper-writing/scripts/score_evaluation.py my-toolkit-ratings.json --rubric paper-writing/assets/toolkit-rubric.json --out evaluation.json --markdown evaluation-scorecard.md
```

The scorer validates exact catalog/profile membership, structured evidence, confidence and applicability, then computes domain/total results with coverage and missing-assessment bounds. Open blockers cannot be hidden by a high score. `reviewed` is not submission approval. Use a prior scored v2 JSON with `--compare`; instrument/profile and subject identity must match, and total deltas need complete assessments with matching applicability. Earlier v1 inputs remain supported without `--rubric`.

See [the scoring method](evaluation-scorecard.md), [category definitions](evaluation-categories.md), and [evaluation protocol](evaluation-protocol.md) in the skill references. This helper does not infer scientific quality from lint checks, authenticate reviewers or verify source truth.
