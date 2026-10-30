# Independent paper review without losing the scientific argument

Use a proportionate review. A sentence edit seldom benefits from ten reviewers; a whole-paper review or an explicit multi-agent request can. The ten roles in [review-roles.json](../assets/review-roles.json) are independent perspectives, not a voting system or a promise that every role needs an agent on every task.

## Freeze the review inputs

Identify the manuscript version, project-context revision, available figures/supplement, and evidence access. Keep a claim ledger with supporting passages and locators. The harness distinguishes `supported`, `pending`, and `unsupported` declarations; keep tentative interpretations pending until their status is resolved. Each consequential source still needs inspection; a registered ID proves neither existence nor entailment.

Generate packets using the harness `plan` command. It writes individual role packets and a plan manifest. Dispatch the individual files using the runtime's actual agent facility; the Python CLI itself does not launch models. Run in waves within the available concurrency, and record actual launches, completions, access failures, and output locations. Never describe generated packets or proposed roles as completed agents.

Ten roles cover argument, abstract/introduction, methods, references, evidence, terminology, readability, figures, limitations, and venue. They may be combined for a smaller task. If using the harness's ten-role merge, all ten role results are necessary to complete that particular plan.

## Preserve the blind reader pass

Give the readability reviewer only the manuscript and reading instructions initially. Do not supply the author's thesis, intended claim ledger, other reviews, or a worked answer. Ask for a brief teach-back of:

1. The specific question and why it matters.
2. The proposed mechanism or approach.
3. The evidence and principal finding.
4. The conditions under which the conclusion holds.
5. Terms or reasoning steps that admit multiple interpretations.

Require manuscript passages supporting each answer and explicit uncertainty where the reader cannot infer an answer. Save this artifact before opening the separate comparison context. Then compare the reader's interpretation with the intended claim ledger and supporting evidence. Agreement with author intent is a comprehension observation; it does not establish scientific truth. A separate evidence role checks the truth support.

## Make reviews actionable

For each finding, provide severity, manuscript location, observed passage/display, reasoning, supporting evidence, a specific repair or decision, and any unverified element. Use the harness-generated JSON template for machine merging. Suggested editorial severities:

| Severity | Decision criterion | Example repair |
|---|---|---|
| Blocking | The central conclusion cannot be supported or assessed from available evidence. | Narrow a claim to the tested setting, or supply the missing analysis. Do not invent the analysis. |
| Major | A consequential ambiguity, missing condition, or inconsistency changes interpretation. | Define the sampling unit and reconcile abstract/body denominators. |
| Minor | Meaning remains intact but presentation impedes the reader. | Define a needed acronym at the start of the main text. |

Missing reporting and invalid methods are different findings. Identify which was observed. Do not require irrelevant experiments merely because an agent specializes in them. A useful review explains what evidence would change its assessment; it does not meet a quota of criticisms. These are editorial practices derived from [NeurIPS 2026 reviewing](https://neurips.cc/Conferences/2026/ReviewerGuidelines) and [ICLR 2027 reviewing](https://iclr.cc/Conferences/2027/ReviewerGuidelines), not additional venue mandates.

## Resolve findings with evidence

The editor compares the passages and actual sources, consolidates duplicates, and separates contradictory judgments from different preferences. Neither majority agreement nor the number of agents establishes correctness. Preserve a justified dissent and its unresolved evidence.

Fix supported scientific blockers first, then ambiguous terms and reasoning, then optional prose polish. Keep the author's facts, uncertainty and stance. After revisions, rerun affected mechanical checks and obtain fresh reviews for affected claims; the harness uses manuscript/context hashes to reject stale review files. Do not relabel an old review as current.

An agent may perform semantic review when it actually has the necessary evidence and competence. Use `unverified` or `needs_review` for inaccessible or insufficient evidence. Do not claim a human reviewed something merely because a model generated a semantic judgment. Conversely, ordinary editing does not require a universal human-signoff barrier.

## Final artifact and tool-use record

Deliver the revised text plus a compact account of consequential changes and unresolved evidence. For a full review preserve the input hashes, raw reviews, consolidated findings and closure evidence. Tool-use records should describe what actually happened, supporting truthful venue disclosures where required; they are not declarations of compliance by themselves.

Maintain three separate outcomes: mechanical checks, semantic/evidence review, and submission compliance. Do not convert a clean lint report into a scientific validity score or an acceptance prediction. Read [the harness guide](harness-guide.md) for the exact machine-readable statuses and CLI.


## Expanded category assessment

The ten independent roles now cover [24 anchored manuscript criteria](evaluation-categories.md), mapped explicitly in [category-review-map.json](../assets/category-review-map.json). Category count and agent count are different. Keep the harness review JSON's findings/checks format; collate a separate complete v2 assessment bundle for the scoring helper rather than assuming a merged review automatically produces a score.

Use [the evaluation protocol](evaluation-protocol.md) for independent anchor/evidence judgments, uncertainty, finding ownership and calibration. Score one underlying defect primarily under its owning category and record dependent consequences; do not multiply penalties for the same contradiction. Use [concept consistency](concept-consistency.md) when matching labels would miss a changed task, denominator, mechanism, representation or inference scope.

V2 reports applicable coverage, domain results and missing-assessment bounds; critical blockers and low-confidence core checks remain visible independently of the mean. Before/after or inter-reviewer comparisons must use the same instrument/profile and compatible applicability; never manufacture comparability by deleting difficult criteria.
