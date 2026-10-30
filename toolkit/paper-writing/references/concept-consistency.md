# Concept consistency: preserve what the paper means

Use this pass before polishing a consequential claim and after changing methods, results, or terminology. Read with [clarity and consistency](clarity-and-consistency.md), [section craft](section-craft.md), and [evidence review](evidence-review.md). These are editorial diagnostics, not empirically validated measures of correctness or acceptance. The historical collection remains 300 papers published by 2022; the [historical lessons](historical-paper-lessons.md) illustrate checks rather than establish universal rules.

## Track objects, not just words

Create a compact ledger for each central construct: **concept ID; operational definition; canonical label and permitted aliases; symbol and domain; unit; population/task; input/output role; training/inference phase; supporting locator**. Record unresolved definitions explicitly. Two labels can name the same object; the same label can conceal different objects. Test identity using the definition, computation, source population, and role in the argument, not spelling similarity.

Ask whether replacing one occurrence with the other would preserve the scientific statement. “Features” and explicitly defined “representations” may be aliases. A representation and its complete prediction system, relative and metric depth, or physician adoption and patient benefit are different concepts. Preserve useful technical repetition. Do not invent a distinction to justify a synonym, or merge a distinction to make prose shorter. Historical cases 1, 2, 5, and 10 show why these boundaries matter.

For notation, trace every consequential symbol from definition to equation, algorithm, display, and conclusion. Check shape, index, range, probability conditioning, sign, quantifier, time basis, and unit. A locally reused symbol is acceptable when its scope is explicit. An unexplained switch from sample count to training-step count is not. Check dimensional compatibility and conversions against the actual definition; a consistent wrong unit remains wrong.

## Audit the task and the quantity

Write the task as **input available to whom and when → operation → output evaluated against what target**. Distinguish training supervision, validation access, and deployed inference inputs. Look for a hidden first-frame mask, test-time adaptation, extra modalities, prompts, calibration data, or an external tool. A training-only operation does not automatically increase inference cost; a method requiring privileged evaluation inputs does not establish performance without them. Compare fixed assumptions and optimized variables before calling an apparent contradiction an error (historical cases 4, 6–8).

For each principal number, record **value; metric/direction; comparator; dataset/cohort version; inclusion rule; numerator/denominator; independent unit; aggregation; uncertainty type; time window**. Distinguish participant, visit, lesion, image, crop, run, and checkpoint. Check whether `n` describes observed measurements or independent units used in inference. Separate macro from micro averages, accuracy from error reduction, percentage points from relative percent, and per-image from per-batch latency. Recalculate any claimed conversion from the supplied values; never fill in missing uncertainty.

## Reconcile claims across the paper

Build one row per central claim with exact passages from title/abstract, introduction, methods, results, displays/captions, discussion, conclusion, and available supplement. Compare **claim type, object, population, comparator, input access, phase, quantity, certainty, and boundary**. A shorter abstract may omit implementation detail, but must retain a condition that changes its principal interpretation. A caption should identify enough of the measured quantity and uncertainty to prevent a conflicting reading. Record displays or sections unavailable for inspection.

Trace the chain **question → proposed explanation/intervention → performed procedure → measured result/proof → conclusion**. Flag unsupported links: a system comparison does not isolate a module; an initialization theorem does not prove an entire training trajectory; mouse mechanism does not establish patient benefit. Observed association, proposed mechanism, measured outcome, and demonstrated causal effect retain distinct statuses (historical cases 8, 11–12). A missing report makes an inference unassessed; supplied contradictory evidence supports an actual defect.

## Four original synthetic minimal pairs

These invented records isolate difficult editing decisions. Each faithful version preserves the supplied facts; no example reports a published result.

1. **Adjustment does not identify causation.** Record: observational cohort, 420 adults, adjusted risk ratio 0.78; residual confounding remains possible. Faithful: “Exposure was associated with 22% lower risk after adjustment.” Problematic: “Exposure caused 22% lower risk after adjustment.” The changed verb creates an unsupported causal conclusion. Adding the observational design and confounding qualification clarifies scope; obtaining causal identification would require evidence, not a stronger verb.

2. **The same percentage can refer to different quantities.** Record: accuracy is 75% for baseline and 80% for the method on the same split. Faithful: “The method reduces error by 20% relative to baseline.” Problematic: “The method increases accuracy by 20% relative to baseline.” Error falls from 25% to 20%; accuracy rises by 5 percentage points, about 6.67% relative. This is a numeric-meaning error. “Accuracy improves by 5%” alone is ambiguous: request the intended scale, then clarify it rather than presume the calculation is wrong.

3. **Measurements are not participants.** Record: 60 held-out participants contribute six images each; evaluation reports a mean over 360 images, with no interval supplied. Faithful: “We evaluated 360 images from 60 participants.” Problematic: “We evaluated 360 independent participants.” The latter changes both the data unit and independence claim. “We evaluated 360 cases” instead needs clarification because *case* is undefined; the record alone does not show that an unreported analysis used the wrong unit. Do not invent an interval or silently change the reported averaging rule.

4. **A measured gain does not measure its explanation.** Record: macro-F1 rises by 3 points with augmentation; nuisance sensitivity is not measured. Faithful: “We propose that reduced nuisance sensitivity explains the 3-point gain.” Problematic: “We demonstrate that reduced nuisance sensitivity explains the 3-point gain.” The second asserts unsupported mechanism evidence. State the measured contrast separately and identify the mechanism as a hypothesis. An undefined use of “robustness” may first need clarification; an explicit claim that sensitivity was measured contradicts the record.

## Test understanding and assign findings

Before showing the intended ledger, ask a blind reader to recover the question, task/input/output, proposed mechanism, evidence, and scope, with passage/display locators and explicit uncertainty. Save the response, then compare against the ledger and sources. A reader's plausible but unintended causal or population interpretation identifies a repair target; agreement with intent establishes neither truth nor validity. Follow [the evaluation protocol](evaluation-protocol.md) for adjudication and closure.

Give each finding one primary criterion and evidence-backed action. Prefer `concept-definitions` for identity, `notation-units` for symbolic/unit meaning, `numbers-denominators` for quantitative referents, `cross-section-alignment` for inconsistent repeated accounts, and `claim-evidence-entailment` for an unsupported inference. Link related criteria without copying a penalty across them. A separate lowered rating requires a distinct anchor-based failure; see the ownership rules in the evaluation protocol.
