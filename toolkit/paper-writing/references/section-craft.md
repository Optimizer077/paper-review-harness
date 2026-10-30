# Section craft: build a paper the reader can check

Use this playbook for a requested manuscript section or a whole-paper argument. First record the audience, actual contribution type, study design, target venue/year, evidence available, and editing scope. A replication, negative result, dataset, theory, or conceptual analysis can be a contribution; do not turn every paper into a new-method success story. The examples in the [NeurIPS/ICLR notes](historical-paper-lessons.md), [CVPR notes](historical-paper-lessons.md), and [medical notes](historical-paper-lessons.md) are a purposive sample, not evidence that a writing formula causes acceptance.

## 1. Make the argument before polishing it

An optional reasoning scaffold is **problem → relevant knowns → specific justified gap/question → approach and evidence → bounded contribution**. It specifies logical dependencies, not five paragraphs. A question can concern reliability, a boundary condition, replication, measurement, or interpretation; a gap need not be the absence of an algorithm. Show why the uncertainty matters to the reader and what would resolve it. Never infer “nobody has studied this” from a small source collection.

Write a one-sentence answer to “What can readers now conclude, under which conditions?” Then separate the claims needed to establish that answer. Peyton Jones recommends explicit, testable contribution statements linked to their supporting analysis, theorem, measurement, or case study. Treat his page allocations and section ordering as conference-writing advice, not universal rules. [Peyton Jones, slides 14–24](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/07/How-to-write-a-great-research-paper.pdf)

Use a claim–evidence map before drafting; the following is an **invented planning example**, not a record of research:

| Claim ID and proposed assertion | Evidence needed / planned locator | Required boundary | Draft action |
|---|---|---|---|
| C1: The proposed pooling rule improves macro-F1 on two specified synthetic shifts. | Matched baselines, split records, per-seed outputs, Table 1. | Two tasks, fixed backbone and data budget; uncertainty defined. | Include only after records support it. |
| C2: Confidence weighting explains the improvement. | Controlled replacement of that component, Table 2; consider competing explanations. | An ablation supports a component's contribution, not a complete causal mechanism. | Prefer “consistent with a contribution from…” unless stronger evidence exists. |
| C3: The system transfers to clinical images. | Separate clinical evaluation in the intended setting. | Synthetic shift results do not establish this. | Unsupported: omit from abstract and conclusion. |
| C4: This is the first such method. | A scoped, defensible novelty search and comparison. | Corpus size alone cannot establish priority. | Replace with the actual difference from inspected work. |

For real work, add exact claim text, source/result identifiers, version, population/task, comparator, metric, uncertainty, evidence locator, status, and unresolved issues. A citation key or a status label does not establish entailment. If only a paragraph edit was requested, preserve its facts and return separate notes for broader evidence problems.

## 2. Title and abstract

**Title.** Name the searchable task and contribution. “Confidence-weighted pooling under two synthetic texture shifts” promises less than “Universal robust visual intelligence” and tells the reader more. A question title may suit unresolved questions; a declarative title needs evidence. Include a clinical study design when the reporting guideline/journal requires it. [ICMJE, title page](https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html)

**ML/computer-vision abstract.** Give enough task/setup to interpret the result, the substantive approach, the principal evidence, and the consequential qualification. Explain what changes relative to a named comparator rather than saying only “extensive experiments demonstrate effectiveness.” Pair an improvement with the metric, dataset/setting, and essential training or resource condition. Keep essential training, data, workload, hardware and evaluation conditions beside the headline claim; consult the [historical examples](historical-paper-lessons.md).

Nature's annotated summary moves from accessible context to the specific problem, main result, comparison with previous knowledge, and wider relevance. Borrow that progression when helpful; its sentence counts and broad-audience summary format are not a generic ML abstract specification. [Nature summary guide](https://www.nature.com/documents/nature-summary-paragraph.pdf)

**Medical structured abstract.** Use the journal's actual headings and design-specific checklist. Include setting/participants, procedures, primary findings with appropriate estimates and uncertainty, important limitations, and a supported conclusion. Reconcile every value with the body. ICMJE distinguishes statistical and clinical significance and recommends trial registration information where applicable. Do not impose a structured clinical abstract on an ordinary ML benchmark paper. [ICMJE, abstract](https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html)

After substantive revisions, draft or reconcile the abstract from the final evidence; do not leave an earlier, stronger conclusion in it.

## 3. Introduction and related work

Give each paragraph a job: orient a reader, establish an inspected finding, explain a consequential uncertainty, motivate the approach, or state the contribution. Remove a paragraph only after checking which dependency it carries. An unexplored combination is not automatically useful: explain the limitation it tests or the decision it enables. Contrast the closest relevant work on the same dimensions—inputs, assumptions, supervision, task, scale, and evidence—rather than relying on a broad adjective such as “limited.”

Mensh and Kording advocate an explicit central message, stable terminology, and an introduction that makes the knowledge gap consequential. Their context/content/conclusion pattern is a useful diagnostic for missing connections, not a mandatory sentence or paragraph template. [Mensh and Kording, Rules 1–6](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005619)

**Respect genre differences.** An ML introduction may preview results and point to evidence. For medical original research, ICMJE instead recommends context and the specific objective/hypothesis without including this study's data or conclusions. Preserve prespecified questions separately from explanations developed after observing results. [ICMJE, introduction](https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html)

**Related work.** Organize around the comparisons that determine the paper's position. A compact comparison matrix can reveal an unsupported novelty claim before prose hides it. Cite work where a definition or borrowed component is used, even if there is a separate related-work section. Describe an earlier approach accurately before explaining the difference. Peyton Jones warns against making competing work look bad to elevate one's own and emphasizes giving the reader enough problem context before technical comparisons. [Peyton Jones, slides 27–31](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/07/How-to-write-a-great-research-paper.pdf)

## 4. Methods and results

**Methods answer “what, why this choice, and how to inspect it?”** Start with the object being estimated or constructed, inputs/outputs, assumptions, and unit of analysis. Then present the mechanism and protocol in dependency order. Define a symbol's meaning, shape, indexing, units, and coordinate frame when applicable. Distinguish a proposed protocol from work completed. A reference to an implementation does not replace a material decision such as a data split, threshold, exclusion, or tuning rule.

The [CVPR DUSt3R case](historical-paper-lessons.md) illustrates the need to distinguish direct pointmap predictions from downstream estimation. The [medical Zech case](historical-paper-lessons.md) illustrates why patients and images need separate counts and split definitions. These are observations reported in those local research notes; this guide did not independently reread their complete papers.

**Results follow the questions and evidence dependencies.** For each main result, identify the comparison and measured outcome, give the relevant estimate and defined uncertainty, then state the narrow finding. Tell readers what a table establishes without transcribing every entry. Report findings that challenge the headline, including relevant null, negative, or failed cases. Mensh and Kording recommend planning results as a sequence of evidence-backed statements that jointly establish the contribution. [Mensh and Kording, Rule 7](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005619)

In computational comparisons, label reproduced versus quoted numbers and unequal access to data, masks, prompts, post-processing, tuning, or compute. In a theory paper, replace a benchmark narrative with definitions, assumptions, theorem, proof argument, and consequences. A guarantee belongs to its stated assumptions. The [NeurIPS/ICLR Adam and GAT observations](historical-paper-lessons.md) illustrate why a theoretical framework or inductive setting cannot disappear during summarization.

## 5. Discussion and conclusion

Answer the stated question, distinguish observation from interpretation, and test plausible alternative explanations. Link each limitation to an inference it blocks: “Only two simulated shifts were evaluated, so the result does not establish robustness to a new acquisition device” is more useful than a generic “generalization is limited.” Mensh and Kording connect discussion to the gap, evidence, interpretation limits, and next questions. [Mensh and Kording, Rule 8](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005619)

A conclusion should retain the task, evidence strength, and decisive conditions. Do not introduce a new experiment or turn future work into a finding. In medical AI, preserve the distinction between diagnostic accuracy, simulated workflow performance, and observed clinical benefit; the [medical MASAI and McKinney cases](historical-paper-lessons.md) show why analysis stage and workflow type change the permitted conclusion.

## 6. Annotated synthetic example

**Everything in this example is invented: method, datasets, measurements, and literature situation. No experiments were performed. These numbers and statements must never be copied into a real manuscript as evidence.** The example demonstrates an ML abstract/introduction, not a medical report. Annotation labels are teaching notes to remove from manuscript prose.

### Synthetic abstract

**[Problem/setup]** Image classifiers can mistake texture changes for changes in class, making texture-shift evaluation useful for testing feature aggregation. **[Specific question]** We ask whether weighting pooled features by local agreement improves classification under a fixed training budget. **[Approach]** We introduce agreement-weighted pooling, which downweights spatial features that disagree with their neighbors without adding labeled training images. **[Evidence; invented]** On the invented SketchShift and IconShift benchmarks, mean macro-F1 over five training seeds is 78.4 and 74.2, compared with 76.1 and 73.8 for uniform pooling; the corresponding seed standard deviations are 0.6/0.7 and 0.5/0.6. **[Bounded implication]** These constructed results illustrate a possible task-dependent benefit; they establish neither performance under natural distribution shifts nor clinical utility.

The comparison states absolute scores, identifies the replication unit behind SD, and leaves the small second difference uninterpreted. It makes no significance claim. A real paper would need split/protocol records, per-seed results, justified aggregation, and an uncertainty analysis appropriate to its intended inference.

### Synthetic introduction

**[Orient through the concrete task]** Consider a classifier trained on smooth line drawings and evaluated on the same classes rendered with dense texture. Correct labels do not change, but spatial features may. This setting motivates a narrow question: can the aggregation rule reduce errors caused by the altered texture while the training images and backbone remain fixed?

**[Knowns and gap, explicitly fictional]** In this invented literature scenario, two inspected baselines compare uniform pooling and a learned attention module, but their evaluations change both training data and aggregation. Those comparisons therefore leave the contribution of the aggregation rule unresolved. This gap concerns attribution under a controlled protocol; it is not a claim that pooling has never been studied. A real introduction would replace this paragraph with verified primary-source findings and precise citations.

**[Rationale and falsifiable contribution]** We study agreement-weighted pooling because local feature disagreement provides a candidate signal for suppressing inconsistent features. This rationale is a hypothesis, not evidence that the rule identifies spurious texture. We compare pooling rules with matched data and tuning budgets and use a component-removal experiment to examine the contribution of the weighting step.

**[Preview appropriate to this ML example]** The synthetic scores in the abstract show a larger difference on SketchShift than on IconShift. Accordingly, the contribution is a controlled test of one aggregation choice in two simulated settings. Natural shifts, other architectures, and clinical decisions remain outside the demonstrated scope.

The paragraphs build dependencies rather than fill a required count. The second establishes why the comparison is needed; the third explains why the proposed test addresses it; the final one prevents the headline from swallowing the limitation. In a medical introduction following ICMJE, omit the result preview and finish with the study objective/hypothesis.

### When no results exist

Write a proposal, protocol, or evidence-needed outline: “We propose to compare agreement-weighted and uniform pooling under matched training budgets. The primary outcome will be macro-F1 on prespecified held-out shifts. The study will test whether the weighting rule improves this outcome; no performance conclusion is currently available.” Mark missing details and planned analyses explicitly. For a theory or conceptual contribution, describe the actual argument/proof evidence instead; absence of experiments does not mean absence of results. Never fill an empty Results section with plausible numbers or treat planned checks as passed.

## 7. Rebuttal and final consistency pass

Map each substantive reviewer concern to a direct answer, supporting evidence, actual change, and verified location/version. Separate clarification, a new analysis completed, work merely proposed, and a reasoned disagreement. Respond to multiple issues within one comment separately. Make the response understandable without requiring the reviewer to hunt through the paper; obey the venue's rebuttal constraints rather than importing a journal letter's format. Noble explicitly recommends direct answers, full point coverage, self-contained explanations, and distinguishing old text from new revisions. [Noble, Rules 4–9](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005730)

Before delivery, compare title, abstract, contribution list, methods, results, captions, conclusion, and response letter against the claim map. Check the question, technical terms, task/population, denominators, units, metric direction, conditions, uncertainty, and result status. Ask a fresh reader to restate the question, approach, main finding, and strongest justified conclusion; compare that restatement with the evidence rather than treating agreement as proof. Recheck only affected dependencies after changes. A passed mechanical check cannot establish novelty, fairness, or scientific validity.

## Source scope

Five primary writing guides were inspected: Nature's one-page summary guide; selected ICMJE manuscript-preparation sections; selected Peyton Jones slides; and the relevant full editorial text of Mensh/Kording and Noble. The active case examples are now the <=2022 top-venue collection, with exact inspection levels recorded in its three specialist inspection ledgers; the earlier case collection is superseded for this purpose. Exact records are in [the source registry](sources.json). No acceptance prediction, systematic literature coverage, experiment verification, or scientific-validity certification is claimed.
