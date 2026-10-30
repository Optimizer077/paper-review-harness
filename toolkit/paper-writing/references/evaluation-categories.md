# Category boundaries and evidence for manuscript scoring

The [v2 catalog](../assets/manuscript-rubric.json) contains 24 editorial criteria in five domains and four contribution profiles. Its weights, anchors and core flags are original toolkit design choices, not a validated scientific-quality scale, acceptance predictor or venue mandate. Use the [scorecard protocol](evaluation-scorecard.md) for inputs, computation and decisions. This guide explains category boundaries and evidence.

## Evidence before a rating

Freeze the manuscript revision and identify the reading packet: main text, supplement, accessible displays, supplied analyses or proofs, artifacts and sources. An evidence entry needs a retrievable `locator` and a concrete `observation`; add `source_id` when an inspected source or registered artifact supports it. Synthetic example: `locator: "draft-r3.pdf, p. 4, Table 2, row M"`; `observation: "The table reports 80% and 84% accuracy; abstract sentence 3 calls this a 4% relative improvement."` A filename, citation number, URL or checklist tick alone is not an observation.

Use stable local artifact IDs for manuscript, analysis and teach-back records; use existing registry IDs for literature or guidance. Record version and passage beside the ID. IDs aid traceability, not truth verification. The [source registry](sources.json) separates historical papers, editorial guidance and current compliance sources. Preserve that distinction and each record's inspection limits. A download, extracted text, regex match or known DOI establishes neither semantic support nor visual inspection.

Select an anchor from inspected facts and explain consequential gaps. Rating 4 means supported within the declared inspection scope, not certified correct. Distinguish `not supplied`, `not inspected`, `inconclusive` and `observed failure`. Use `unassessed` when the category cannot yet be judged. An inspected omission can justify a low reporting rating without proving the procedure never occurred. State confidence separately.

Only `figures-tables` permits N/A: document absent displays **and** why no claim needs one. Existing inaccessible displays are unassessed. The six core criteria never permit N/A. For numeric-free theory, inspect the absence of numeric assertions and any constants, rates or quantified counts; do not invent empirical denominators. Without a saved blind reader response, `reader-teachback` remains unassessed.

## Category boundaries

| Criterion | Judge here | Boundary and useful evidence |
|---|---|---|
| `research-question` | The exact question, target and answer conditions. | Extract the question. Importance belongs in motivation; unsupported answers belong in entailment. |
| `motivation-gap` | Why the unresolved need follows from prior knowledge and matters. | Trace gap premises to prior passages or observations. Attribution accuracy belongs in literature positioning. |
| `contribution-calibration` | What is added and the kind of value supplied. | Compare additions with delivered objects or arguments. Do not demand novelty or SOTA for every contribution. |
| `literature-positioning` | Accurate attribution and relationships to alternatives and contrary evidence. | Inspect source passages and versions. Misleading comparison conditions belong primarily in comparison fairness. |
| `method-specification` | Whether decisive procedures or constructions are described. | Trace inputs, choices and outputs. A specified invalid procedure can score well here and poorly on validity. |
| `design-validity` | Whether design or proof supports the intended inference under its assumptions. | Inspect leakage, units, identification or proof steps. Missing description alone does not establish an invalid procedure. |
| `comparison-fairness` | Whether conditions permit the attributed comparison. | Inspect comparator/data/resource/assumption records and controls. Distinguish comparison defects from general design flaws. |
| `analysis-uncertainty` | Calculation and meaning of estimates, bounds and uncertainty. | Inspect analysis selection, dependence and quantifiers. Wrong repeated numbers belong in numbers/denominators. |
| `robustness-failures` | Evidence locating consequential sensitivities and failures. | Inspect stress tests, counterexamples or sensitivity arguments. An untested setting is a limitation, not a completed robustness check. |
| `claim-evidence-entailment` | Whether a central claim follows at its stated strength and scope. | Pair clauses with results or proof steps. Lower validity separately only with evidence of its distinct failure. |
| `concept-definitions` | Operational meaning and identity of constructs and aliases. | Compare definition-ledger entries. A stable but unexplained acronym belongs in jargon/acronyms. |
| `notation-units` | Symbol domains, dimensions, scales, units and formal references. | Inspect equations, legends and conversions. Arithmetic or denominator mistakes belong in numbers/denominators. |
| `numbers-denominators` | Numeric agreement, counting units, aggregation and change descriptions. | Reconcile counts and recompute supplied quantities. Inference from the numbers belongs in analysis or entailment. |
| `cross-section-alignment` | Agreement of repeated facts, conditions and conclusions. | Cite conflicting locations. A claim repeated consistently but unsupported everywhere is an entailment defect. |
| `title-abstract` | Summary communication of question, approach, finding and essential boundary. | Use the summary packet. Inaccuracy belongs primarily in alignment or entailment; explain any distinct orientation failure. |
| `introduction-logic` | How context leads through the unresolved problem to this study. | Map argumentative steps and missing bridges. Sound ordering cannot validate an unsupported gap premise. |
| `paragraph-sentence-logic` | Local dependencies, referents and evidence-to-takeaway links. | Cite ambiguous phrases or missing links. Sentence length, voice and word counts are not rating thresholds. |
| `jargon-acronyms` | Audience-appropriate introduction of necessary terminology. | Inspect first uses in separate reading scopes. Conflicting technical meanings belong in concept definitions. |
| `reader-teachback` | What a blind intended reader actually reconstructs. | Save the first response before revealing the ledger. This outcome diagnostic is not a second prose-polish judgment. |
| `figures-tables` | Interpretability of visual encodings and captions. | Inspect pixels or actual tables, axes and uncertainty. Numeric contradictions belong primarily in numbers or alignment. |
| `reproducibility-artifacts` | A traceable route to reconstruct central results. | Inspect versions, derivations, configurations and access instructions. Method prose and artifact access are distinct; access is not a successful rerun. |
| `limitations-transfer` | Disclosure of limits and their interpretive consequences. | Connect limits to affected claims. An untested condition earns no robustness credit and need not trigger unrelated experiments. |
| `ethics-disclosures` | Truthful, relevant declarations supported by records. | Inspect actual approvals/exemptions, consent, interests, funding, contributions and assistance. Missing records prove neither misconduct nor exemption. |
| `venue-compliance` | Formal requirements for the exact venue, cycle, track, stage and design. | Link dated official rules to artifact checks. Checklist completion establishes neither scientific validity nor ethical truthfulness. |

Assign each finding a primary criterion. Cross-reference related categories without copying its severity or mechanically lowering every linked rating. One issue can have distinct observable effects: a denominator error can also create an abstract/body contradiction. Document the arithmetic error and conflicting passages separately, explaining each consequence. If one repair removes the whole concern, record one revision action with the affected criteria. Do not turn defect counts into a score. Central blockers remain explicit even when other categories are strong.

## Contribution-specific use

Select the profile before rating; its weights are fixed. Every profile includes all 24 criteria. Guidance changes interpretation rather than deleting inconvenient categories. Domain totals in catalog order are empirical ML **20/35/20/15/10**, theory **22/37/23/10/8**, clinical **16/39/19/15/11**, and systematic review **18/39/18/15/10**. Each sums to 100. These allocations express editorial emphasis, not empirical importance estimates.

**Empirical ML:** Separate benchmark observations, mechanism attribution and deployment claims. Inspect split and selection access, input information, comparator budgets and represented variability. A resource, replication, feasibility or negative-result contribution can be strong without a new method or leaderboard win. Request additional analyses only when they could change a central conclusion.

**Theory:** Inspect assumptions, quantifiers, regimes, proof dependencies and summaries. Compare guarantees under compatible conditions; use counterexamples or assumption sensitivity instead of forcing empirical experiments. Complete proofs or derivations can provide a reconstruction route. Deterministic arguments need precise bounds and meanings, not manufactured confidence intervals. Validity remains unassessed when the relevant proof has not been inspected.

**Clinical:** Route by actual design: trial, observational, diagnostic, prediction or another study. Identify population, endpoint, analysis unit and care context. Distinguish discrimination, calibration, diagnostic accuracy, utility and causal benefit. Apply registration, consent, harms or flow requirements only where relevant. Restricted data can have a sound controlled-access route; privacy alone does not establish reproducibility failure.

**Systematic review:** Inspect actual search, screening, extraction, appraisal and synthesis. Separate records, reports and studies; reconcile flow and per-outcome denominators. Judge pooling only when appropriate; qualitative synthesis still needs traceable reasoning and uncertainty. Separate review-process limits from included-study limits. This profile cannot turn narrative related work or the toolkit's 300-paper convenience sample into a systematic review.

## Basis and limits

Operational anchors, weights, core threshold, profiles and teach-back scoring are original editorial synthesis. Existing guidance informs checks without validating the numeric rubric. Relevant existing source IDs are:

- `clarity-gopen-swan-1990`, `clarity-mensh-kording-2017`, `clarity-ehrhart-evelo-2021`: reader expectations, structure, stable terminology and abbreviation access; see [clarity](clarity-and-consistency.md).
- `evidence-asa-statement-2016`, `evidence-hurlbert-pseudoreplication-1984`, `evidence-lakens-equivalence-2017`, `evidence-nature-reproducibility-2018`, `evidence-acl-checklist-2021`, `evidence-neurips-checklist`: inference, units, uncertainty, assumptions and reconstruction; see [evidence review](evidence-review.md).
- `med-guidance-prisma2020`, `med-guidance-strobe`, `med-guidance-tripod-ai`, `med-guidance-consort2025`, `med-guidance-stard2015`, `med-guidance-equator`: design-specific reporting scopes; see [venue profiles](venue-profiles.md). Current guidance remains separate from historical <=2022 paper examples.

These IDs resolve to recorded inspection levels and limitations in the registry. Recheck current official rules for an actual submission. The rubric adds no new paper evidence and claims no fresh review of the unchanged historical corpus.
