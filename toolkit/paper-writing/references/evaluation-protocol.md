# Evaluation protocol for a reviewable manuscript

This protocol adds semantic review and revision discipline to [the scorecard](evaluation-scorecard.md) and [review protocol](review-protocol.md). The rubric organizes editorial judgments; it has not been empirically validated as a scientific-validity measure or acceptance predictor. Historical examples retain the 300-paper, <=2022 scope in [historical lessons](historical-paper-lessons.md). Use their bounded cases alongside [section craft](section-craft.md), [evidence review](evidence-review.md), and [concept consistency](concept-consistency.md).

## Freeze the subject and select the profile

Assess an identified artifact: record subject ID, revision, manuscript/context hashes where available, reviewer identity/type, date, rubric ID/fingerprint, and access to figures, supplement, sources, code, or data. A review of captions is not visual inspection. A source ID is not verified entailment. Keep the actual reviewed packet and access limits so a later reader can reproduce the judgment.

Choose the catalog's contribution profile before rating: `empirical-ml`, `theory`, `clinical`, or `systematic-review`. Document why it fits and apply its guidance and weights. For mixed work, explain the selected emphasis; do not improvise input weights or demand experiments from a proof-only contribution. Theory requires assumptions/proof inspection; clinical conclusions require the relevant design and endpoint interpretation; a review requires its actual search, selection, and synthesis record. Profile selection does not establish that these activities were performed.

## Preserve independent observation

Dispatch only useful perspectives from the [existing ten roles](../assets/review-roles.json). The [24-criterion map](../assets/category-review-map.json) routes criteria to those roles; it creates no roles, agents, or completed reviews. Record actual reviewers and inspected material. Multiple criteria can be covered by one reviewer; independence means an initial judgment formed before seeing another review, not a packet count.

Keep the reader pass blind. Initially supply the readability reviewer only the versioned manuscript and intended audience/reading instructions. Hide the author thesis, claim ledger, expected answers, and other critiques. Ask for a teach-back of question, approach/proposed mechanism, input/output, evidence/finding, and limits, each with a locator or “not recoverable.” Save that artifact **before** opening the comparison context. Then compare interpretation with author intent and inspected evidence. A matched answer is a comprehension observation, not independent confirmation of science.

## Rate evidence, anchors, and confidence separately

For each of all 24 catalog IDs, select `assessed`, `unassessed`, or permitted `not_applicable`. Read that criterion's 0–4 anchors and the profile override; generic labels alone do not define the rating. Record the best-supported anchor, structured evidence `{locator, observation, source_id?}`, rationale, confidence (`low`, `medium`, or `high`), and an actionable repair where needed. Quote only enough passage to identify the issue. Explain why the neighboring anchor is less appropriate when the choice is consequential.

Use confidence for the strength and completeness of the review basis, not writing fluency or agreement among agents. Low-confidence assessment can still identify an observed issue; unavailable essential evidence may instead require `unassessed`, with null rating/confidence and a reason. Distinguish an actual contradiction, consequential ambiguity, missing reporting, inaccessible evidence, and demonstrated methodological failure. Never turn “not inspected” into “failed.” Only `figures-tables` initially permits N/A, with documented absence of displays and no claim needing one; core criteria cannot be N/A.

Preserve raw ratings. A full score requires all applicable criteria assessed. Missing-assessment bounds describe possible completion scores, not statistical confidence intervals. Explicit justified N/A changes the applicable denominator; unassessed criteria do not. Confidence does not multiply the score. Report coverage, core deficits, low-confidence core checks, and blockers beside the number. `reviewed` means the configured checks are complete without specified readiness deficits; it is not submission approval.

## Calibrate and adjudicate without voting

Before consequential comparisons, have reviewers independently rate a small common packet with the same artifact/profile/anchors. Compare the cited passages and reasoning, identify whether disagreement comes from access, interpretation, applicability, or anchor use, and document an agreed interpretation of the rubric where possible. This is local calibration, not evidence that the rubric is validated. Preserve initial ratings; a revised judgment needs its reason and supporting evidence.

For disputed manuscript findings, inspect the actual passages, results, proofs, or sources that could discriminate between interpretations. Request a targeted independent review when useful. Do not resolve by majority vote, average conflicting ratings away, require a criticism quota, or invent a defect because a role found none. Keep justified dissent and unresolved evidence explicit. A preference for wording is not a scientific error.

The criterion map lists a primary owner first, followed by collaborating roles. Consolidate duplicate reports into one finding ID with a primary criterion and links to affected criteria. For example, a denominator copied incorrectly into the abstract belongs primarily to `numbers-denominators`; record the cross-section symptom without mechanically reducing every communication/consistency rating. If the abstract independently removes a decisive scope condition, that separate failure may affect `cross-section-alignment` or `title-abstract`, with its own evidence and anchor rationale. Ratings are criterion judgments, not repeated deductions per reviewer or per occurrence.

## Close actions against the changed artifact

Maintain a revision ledger: finding ID, primary criterion, severity, exact observation/locator, evidence state, requested action, owner, status, changed artifact/revision, and verification/resolution. Prioritize open blockers, missing assessments, core deficits, then weaker assessed criteria. Missing evidence is a request to assess or narrow the claim, not proof of failure. A score increase cannot close a blocker.

Verify each consequential repair against the revised passage and underlying evidence. Reconcile abstract, body, displays, and conclusion after changes; rerun affected checks and obtain fresh affected reviews. Preserve old reviews as history rather than relabeling them current. Close with a specific resolution and locator, or retain the unresolved item and its consequence. Compare scores only for matching subject ID, rubric fingerprint, and profile; total deltas also require complete assessments and matching applicability. Preserve criterion disagreements. Before/after scores do not demonstrate increased scientific truth.
