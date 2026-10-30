---
name: paper-writing
description: Draft, revise, and review scientific manuscripts with claim-to-evidence checks, consistent terminology, reader comprehension review, and venue-specific guidance. Use for paper sections, whole manuscripts, and reviewer responses in ML, computer vision, and health research.
---

# Paper writing

Produce the requested manuscript or edit, preserving the actual science. Use this skill for academic argument and prose; use the appropriate document or LaTeX tools when rendered layout is also requested. The bundled harness provides inspectable mechanical checks and reviewer packets, not an automatic scientific-quality verdict.

## Establish the working record

The active writing-example corpus contains 300 papers from 2022 or earlier, restricted to CVPR, ICCV, NeurIPS, ICLR, ICML, NEJM, The Lancet, JAMA, BMJ, Nature Medicine, and Nature. Use [historical paper lessons](references/historical-paper-lessons.md) for these examples. Exclude later papers and workshops from this reference collection; do not infer that every paper at a named venue is exemplary. This cutoff governs the example corpus, not the manuscript's own date or the author's future literature needs. Current submission instructions remain a separate compliance reference.

Infer the audience, contribution type, requested scope, manuscript stage, target venue/year/track, and available evidence. Work with existing drafts and records. Missing venue details do not prevent a useful section edit; label any provisional structure. Follow the author's format rather than imposing IMRAD on theory, position papers, or narrative reviews.

For a substantial draft or several writers, create a versioned project context using [the project template](assets/project-template.json). Record the question, thesis, terminology, protected facts, source passages with locators, claim status, and section dependencies. A source ID and a `supported` label are declarations to inspect, not proof. Separate proposed experiments from completed work. Keep essential limitations with their claims.

Do not invent results, methods, datasets, citations, ethics approvals, registrations, author declarations, or completed revisions. For a material missing fact, use an explicit unresolved marker in a working draft or explain the gap outside clean prose. Preserve comparators, denominators, metric direction, units, negation, uncertainty definitions, and generalization scope during editing.

## Choose the relevant work

- For an outline, title, abstract, introduction, related work, methods, results, or discussion, read [section craft](references/section-craft.md). Build paragraphs around the scientific argument and their supporting evidence. Do not force every paper into the same introduction formula.
- For jargon, acronyms, symbols, wording, or reader difficulty, read [clarity and consistency](references/clarity-and-consistency.md). For changed conceptual roles, units, denominators, or scientific meaning across sections, also use [concept consistency](references/concept-consistency.md). Retain precise technical language; distinguish permitted aliases from changes in meaning.
- For claim support, comparisons, uncertainty, reproducibility, or medical inference, read [evidence review](references/evidence-review.md). Select checks by study design and contribution type.
- For submission preparation, read [venue profiles](references/venue-profiles.md), then verify the exact current official instructions for the intended cycle, track, and stage. Historical policies are examples, not standing requirements.
- For a whole-paper or explicitly rigorous review, read [the review protocol](references/review-protocol.md). Use [the ten reviewer roles](assets/review-roles.json) when independent perspectives will help. A narrow edit usually needs only the relevant passes.
- When a score is requested, use [scoring v2](references/evaluation-scorecard.md), [aggressive review](references/aggressive-review.md), [category boundaries](references/evaluation-categories.md), and [the evaluation protocol](references/evaluation-protocol.md). New assessments use `aggressive` strictness unless the author requests standard mode. Select the appropriate contribution profile, use the 24 anchored criteria, require evidence and rationale, and report raw and effective scores, caps, coverage, confidence, domain scores and critical blockers separately. For a narrow task leave unrelated criteria unassessed; do not expand the task just to obtain a complete number. A reviewed scorecard is not submission approval.

## Draft and reconcile

Make the question and contribution understandable before polishing individual sentences. For each central claim, identify the supporting experiment, analysis, proof, or source passage and the condition that limits it. A lack of prior work alone does not establish importance; a novel method or state-of-the-art score is not required for every contribution.

During revision, preserve the author's scientific stance and confidence. Explain supported findings directly; separate observation, interpretation, and speculation. Inspect the source passage for consequential citations. Citation membership, paper titles, and neighboring sentences do not establish entailment.

After a substantive change, reconcile the title, abstract, introduction, contribution list, methods, results, captions, discussion, and conclusion that were supplied. Check the main finding, terminology, sample, uncertainty, and scope against the same context revision. If source material is partial, state which consistency checks remain unperformed.

For a reviewer response, connect each comment to a substantive answer and a verified revision location. Distinguish completed changes from proposed analyses. Explain justified disagreements without inventing extra experiments or page numbers.

## Use the harness proportionately

Run `python scripts/paper_harness.py --help` from this skill directory. See [the harness guide](references/harness-guide.md) for concrete commands and limitations. The checker accepts text, Markdown, and common LaTeX structures; it does not render figures or fully parse TeX.

An audit can check registered IDs, literal facts, declared variants, unresolved markers, and configured section limits. Its warnings are prompts for inspection, not automatic edits. A passing audit does not establish that a citation exists, a result is correct, a number refers to the right cohort, or the paper is readable.

For multiple agents, generate a plan, dispatch the relevant independent roles using the available agent tools, and run in waves within the runtime's actual capacity. Record which agents actually ran and their access levels. The CLI generates task packets; it does not call an LLM service. Require evidence and locations in reviews, preserve manuscript/context hashes, and invalidate stale reviews after revisions. Never present ten generated packets as ten completed reviews.

Use blind reader teach-back to test understanding before showing the reader the intended thesis. Use a separate evidence reviewer to check whether that understanding is supported. Resolve supported blockers before optional prose polish; do not seek a fault quota or infer correctness from majority agreement.

## Deliver

Return the requested paper, section, revision, or review. For substantial review, include the principal changes, unresolved evidence issues, applicable verification limits, and next decision. Keep review instructions out of manuscript prose. Do not call a manuscript submission-ready when material evidence or required declarations remain unresolved.

The source-backed research behind this skill is summarized in [the research basis](references/research-basis.md). The local convenience corpus illustrates writing choices; it does not measure what causes acceptance or establish universal stylistic rules.
