# Scoring v2: anchored judgments with visible evidence limits

Use scoring when requested. A rating is an editorial judgment about the supplied artifact and inspected evidence, not a scientific truth measure, acceptance probability, or substitute for unresolved blockers. For ordinary section edits use only the necessary review passes; do not expand the task just to fill a scorecard.

## Choose the instrument before rating

[The manuscript catalog](../assets/manuscript-rubric.json) defines **24 criteria in five domains**: scientific argument, evidence/methods, conceptual consistency, communication, and transparency. Each criterion has its own 0–4 anchors, checks and reviewer responsibilities. [Category boundaries](evaluation-categories.md) explain which defect belongs where. [Concept review](concept-consistency.md) and [the evaluation protocol](evaluation-protocol.md) describe how to inspect meaning and adjudicate disagreements.

Select the contribution profile before looking for a desired total: `empirical-ml`, `theory`, `clinical`, or `systematic-review`. Profiles explicitly change weights and interpretive guidance while retaining the full catalog. Theory uses assumptions/proofs/regimes; it must not be penalized for missing an experiment it does not claim. Clinical and review profiles select appropriate study-design checks. These profiles are original editorial conventions, not venue scoring rules or empirically validated measurement scales.

Use the separate [toolkit rubric](../assets/toolkit-rubric.json) to evaluate this software/skill package. A manuscript rubric cannot meaningfully score a writing toolkit. The earlier v1 score of 87.5 used a different instrument; a v2 total is not a before/after improvement estimate on that scale.

## Evidence, anchors and confidence

Record the exact subject ID and revision, reviewer, review date and rubric/profile. For each criterion provide status, rating, rationale, and structured evidence with **locator** and **observation**. Name the actual passage, table, source excerpt, test or artifact inspected. A bibliographic ID or well-formed evidence object does not prove the source exists or supports the claim.

Ratings are integers **0, 1, 2, 3, 4**; use the criterion-specific anchor rather than a generic impression. Broadly these represent absent/contradictory, major defects, partial adequacy, strong with bounded gaps, and supported completeness within inspected scope. Higher is not more confident. An observed contradiction can justify a low rating with high confidence.

Record confidence separately: **high** when the relevant evidence is directly inspectable and the judgment is stable; **medium** when evidence is useful but interpretation or coverage is limited; **low** when a supplied rating remains fragile. Confidence is an assessor declaration, not a statistically calibrated probability, and never multiplies the score. Missing evidence normally means unassessed, rather than a speculative low-confidence rating.

Use three distinct statuses:

| Status | Meaning | Score treatment |
|---|---|---|
| `assessed` | Relevant evidence was inspected and an anchor-based judgment made | Integer0–4, confidence, evidence and rationale required |
| `unassessed` | The check was not performed or the evidence is unavailable | Rating/confidence null; remains in the denominator and prevents a complete total |
| `not_applicable` | A permitted criterion is substantively irrelevant to this artifact | Null rating; rubric permission, applicability reason, evidence and rationale required; excluded weight disclosed |

Only figures/tables initially permits N/A, when the manuscript actually has no displays and no applicable argument needs one. A missing figure file is unassessed, not N/A. Core criteria cannot be excluded. A poor result, awkward section, missing experiment, or unavailable source is not automatically an applicability exception.

## Calculation and coverage

Profile weights sum to100. Let `A` be the applicable weight, `W` the assessed weight, and `E = sum(weight × rating / 4)` over assessed criteria.

- Assessment coverage is `100 × W / A`.
- A complete total is `100 × E / A`, available only when all applicable criteria are assessed.
- With missing assessments, the total is null. The report shows the earned subtotal and lower/upper possible totals by filling missing ratings with0 or4.
- These are **missing-assessment bounds**, not confidence intervals, predictions or estimates of the true paper quality.
- N/A changes `A` only after the explicit checks above; unassessed criteria never silently disappear. The report shows nominal, applicable, assessed and excluded weights, plus each domain's score and coverage.

The arithmetic summarizes anchored ordinal judgments for editorial use. Equal numerical steps are a design convention, not evidence that a change from0to1 has the same scientific meaning as3to4. Preserve the category evidence alongside the total; do not optimize writing to win points while losing meaning.

## Blockers, weak areas and decisions

An open critical blocker remains `blocked` even with a high diagnostic score. Record its criterion, description and evidence; resolving it requires an explicit resolution explanation and fresh supporting evidence. Never mark a blocker closed because the average improved.

Assessment completion and readiness are separate. New skill workflows use the [aggressive policy](aggressive-review.md): core ratings at least 3, high confidence for core judgments, no assessed criterion at 0 or 1, and every scored domain at least 75. Failure of those gates requires revision or evidence. Open blockers and missing assessments take precedence. The following legacy standard policy remains available for compatibility:

1. Open blocker: `blocked`.
2. Any applicable unassessed criterion: `incomplete`.
3. A core criterion below2 or with low confidence: `needs_revision_or_evidence`.
4. Otherwise: `reviewed`.

`Reviewed` is not submission approval. Thresholds are disclosed editorial policies, not scientific boundaries. Aggressive review also reports an effective score: the minimum of the complete raw score and triggered weakest-link caps. Caps do not add together. Unknown assessments keep both totals null. Revision priorities list blockers first, then missing checks, core deficits and weak assessed criteria. Treat an unassessed question as a request for evidence, not a proven failure. One underlying defect has a primary criterion owner; record dependent consequences without applying the same penalty repeatedly.

## Run the CLI

Start from [manuscript-assessment-template.json](../assets/manuscript-assessment-template.json); replace its subject/reviewer/date and add real evidence. Keep all24 IDs. V2 rejects omitted/unknown/duplicate criteria, inline weight changes, invalid statuses and unsupported exclusions.

From the toolkit output directory:

```powershell
python .\paper-writing\scripts\score_evaluation.py .\my-ratings.json --rubric .\paper-writing\assets\manuscript-rubric.json --strictness aggressive --out .\my-score.json --markdown .\my-score.md
python .\paper-writing\scripts\score_evaluation.py .\my-revised-ratings.json --rubric .\paper-writing\assets\manuscript-rubric.json --strictness aggressive --compare .\my-score.json --out .\my-revised-score.json --markdown .\my-revised-score.md
```

A comparison uses a previously scored v2 JSON with its rubric fingerprint, matching subject ID, profile, strictness and policy fingerprint. Revisions can differ; same-revision comparisons can expose reviewer disagreement. Total deltas are withheld when applicability or assessment coverage makes totals incomparable. Do not average away disagreements or present a score change as causal proof of better science. [Evaluation protocol](evaluation-protocol.md) explains calibration and adjudication. Inputs without strictness retain standard behavior; the new assessment template explicitly selects aggressive.

Version1 remains supported for earlier weighted-rating files without `--rubric`; its numerical fields remain compatible, while blockers are visible in readiness. V2 requires an explicit rubric. The separate review harness still emits findings/checks; an editor collates the category evidence into the complete assessment bundle. The scorer validates structure and computes declared judgments; it does not launch models, read the paper, authenticate reviewers, verify sources or decide scientific validity.

Generated JSON/Markdown reports are replaced when those output paths are reused. Keep editorial prose and proposed manuscript text in separate review-notes files; the synthetic forward test demonstrates this separation.
