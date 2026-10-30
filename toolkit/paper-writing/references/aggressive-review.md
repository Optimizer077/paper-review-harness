# Aggressive editorial review

Choose `aggressive` when the review should expose consequential weak areas that a weighted average can hide. Choose the manuscript contribution profile before rating. Inspect the criterion anchors and source evidence, preserve all ratings, and record uncertainty honestly. This policy is an original editorial convention. Its thresholds and caps have not been calibrated as scientific quality, acceptance likelihood, or venue requirements.

The shared [policy asset](../assets/scoring-policies.json) defines both modes. Existing inputs without `strictness` retain `standard` behavior. New assessment workflows can set `"strictness": "aggressive"` or pass `--strictness aggressive` to the scorer. Version 1 supports standard scoring only; migrate to a version 2 rubric for aggressive review.

## Raw score and effective score

`score_out_of_100` preserves the weighted anchored score. Confidence never multiplies a rating. For complete assessments only, `effective_score_out_of_100` is the minimum of that raw score and every triggered cap. Multiple problems do not add penalties; the weakest applicable cap controls. Both numbers and the underlying evidence remain visible.

| Observed condition | Effective score ceiling |
| --- | ---: |
| Any open critical blocker | 39 |
| Any core criterion rated 0 or 1 | 49 |
| Any core criterion rated 2 | 69 |
| Any applicable noncore criterion rated 0 or 1 | 69 |
| Any completely rated domain below 60 | 59 |
| Any completely rated domain from 60 to below 75 | 74 |
| Any assessed core criterion with low confidence | 59 |
| Any assessed core criterion with medium confidence | 79 |

Each cap records its rule, ceiling, reason, criterion/domain/blocker identity and evidence. A complete raw score of 97.5 with a core rating of 2 can therefore become an effective score of 69. A complete domain of 55 caps the effective total at 59 even if other domains are strong. These are disclosed editorial decisions, not discoveries about a manuscript's underlying scientific value.

Domain thresholds use the unrounded ratio. Displayed domain scores round to two decimals; a value just below 75 can therefore display as 75 while still failing the gate.

Missing assessments remain unknown. Any applicable unassessed criterion makes both the raw total and effective total null, even when assessed weight happens to reach 100 because the missing criterion has zero weight. Raw missing-assessment bounds retain their existing meaning; there are no effective-score bounds. A cap observed in an incomplete assessment is diagnostic and does not create an effective total. N/A still requires explicit rubric permission, evidence and rationale; core criteria cannot be excluded.

## Readiness and revision

Readiness follows this order:

1. An open blocker produces `blocked`.
2. Any applicable unassessed criterion produces `incomplete`.
3. Otherwise aggressive review requires every core rating at least 3, every core confidence high, no applicable criterion rated 0 or 1, and every domain score at least 75. A violated gate produces `needs_revision_or_evidence`.
4. An assessment meeting those gates is `reviewed`.

`Reviewed` is not submission approval. High confidence records a stable basis for the judgment; it does not certify the science. Do not increase declared confidence just to remove a cap. Obtain the missing evidence or explain why a judgment changed. An unratable zero-applicable-weight domain has no numerical domain score; it triggers no fabricated failure or cap.

Use the existing [evaluation protocol](evaluation-protocol.md) for independent observation, blind teach-back, evidence adjudication and repair verification. Start with open blockers and missing assessments, then review the triggered caps and gates. A score increase never closes a blocker; keep explicit resolution evidence.

## Run and compare

```powershell
python .\paper-writing\scripts\score_evaluation.py .\my-ratings.json --rubric .\paper-writing\assets\manuscript-rubric.json --strictness aggressive --out .\my-score.json --markdown .\my-score.md
```

Scored v2 JSON records `strictness`, `scoring_policy_id`, and a SHA-256 fingerprint of the selected policy and policy format version. The scorer recomputes derived fields from the recorded judgments and rejects a supplied policy fingerprint that differs from the current selected policy. Keep the reviewed artifact and inputs: fingerprints identify settings, not source truth or reviewer authenticity.

Comparison requires the same subject, rubric fingerprint, profile, strictness mode and policy fingerprint. Raw total deltas remain available under the existing comparison rules. Effective total deltas additionally use the same policy and are withheld if either assessment is incomplete or applicability differs. Do not compare an aggressive effective score to a standard score as improvement, and do not treat different-revision scores as proof of better science.

The toolkit assessment's prior raw v2 score of 83.5 is retained. Under aggressive policy its completely rated validation domain of 55 triggers a ceiling of 59. That exposes the recorded validation weakness; it is not an independently validated quality or acceptance estimate.
