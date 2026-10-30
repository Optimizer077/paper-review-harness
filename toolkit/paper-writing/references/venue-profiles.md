# Select the venue, cycle, track, stage, and study design

Snapshot checked **2026-10-30**. These profiles support editorial routing; they are not a current submission certification. Select the author's intended venue/year explicitly. A published 2027 page does not make its rules applicable to a 2026 submission. Record the exact URL, access date, track, and submission stage when refreshing a rule.

## ML and computer vision

| Profile | Evidence-backed emphasis | Authoritative starting points |
|---|---|---|
| NeurIPS 2026 | Review according to contribution type, including theory, use-inspired work, conceptual/feasibility contributions and negative results. Match abstract/introduction claims to evidence, assumptions and scope. Use honest checklist answers and traceable reproducibility details; code release is not the only route to reproducibility. | [Reviewer guidelines](https://neurips.cc/Conferences/2026/ReviewerGuidelines), [main-track handbook](https://neurips.cc/Conferences/2026/MainTrackHandbook), [paper checklist](https://neurips.cc/public/guides/PaperChecklist) |
| ICLR 2027 published guidance | Put decisive evidence and limitations where reviewers are expected to read them. Evaluate the contribution without requiring state-of-the-art results in every case. This cycle has an AI-use statement requirement with activity-specific rules. | [Author guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines), [reviewer guidelines](https://iclr.cc/Conferences/2027/ReviewerGuidelines), [AI policy for authors](https://iclr.cc/Conferences/2027/AIPolicyForAuthors) |
| CVPR 2027 published guidance | Verify template, anonymity, page accounting, supplement rules, and required LLM Usage Statement. The statement requirement covers writing/grammar assistance, so preserve a truthful tool-use record. | [Author guidelines](https://cvpr.thecvf.com/Conferences/2027/AuthorGuidelines) |
| CVPR 2026 historical comparison | Technical contribution is broader than benchmark dominance. Supplementary material and code have specific roles; do not use public camera-ready papers as anonymous-submission formatting templates. | [Author guidelines](https://cvpr.thecvf.com/Conferences/2026/AuthorGuidelines), [reviewer guidelines](https://cvpr.thecvf.com/Conferences/2026/ReviewerGuidelines) |

These summaries paraphrase the named sources. The following is an implementation recommendation: keep a requirement record with `rule`, `applies_to`, `source_url`, `accessed_date`, `evidence_location`, and `status` (`verified`, `unresolved`, or `not_applicable`). Inspect the current template for exact page/word accounting rather than putting a generic limit in the manuscript checker. A manuscript word count cannot certify page-limit compliance.

Author assistance on the author's own manuscript and confidential official reviewing have different permissions and policies. Do not infer permission to upload an assigned confidential submission from an author-writing workflow. Verify the applicable venue's actual rules before using assistance in that setting. [CVPR 2026 reviewer guidelines](https://cvpr.thecvf.com/Conferences/2026/ReviewerGuidelines)

## Health and clinical AI

Select by the actual research question and design, using [EQUATOR](https://www.equator-network.org/), then the intended journal's current instructions. Reporting guidance makes the work inspectable; completing a checklist does not prove the design is valid.

| Actual design | Starting guideline | Important applicability boundary |
|---|---|---|
| Randomized intervention trial | [CONSORT 2025](https://www.bmj.com/content/389/bmj-2024-081123), relevant extensions such as [CONSORT-AI](https://pmc.ncbi.nlm.nih.gov/articles/PMC7598943/) | CONSORT 2025 supersedes the 2010 core. AI-extension item numbering predates this revision; check how the journal combines the documents. |
| Cohort, case-control or cross-sectional observational study | [STROBE](https://www.strobe-statement.org/checklists/) | Report relevant confounding and selection limits. Observational data do not automatically preclude causal inference, but causal language requires justified identification assumptions and evidence. |
| Diagnostic test accuracy | [STARD 2015](https://www.bmj.com/content/351/bmj.h5527), [STARD-AI record](https://pubmed.ncbi.nlm.nih.gov/40954311/) | State intended use, reference standard and thresholds. STARD-AI is published and its record links a correction; inspect the full current checklist before claiming compliance. |
| Individual clinical prediction-model development/evaluation | [TRIPOD+AI 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/) | Applies to regression and ML. Discrimination, calibration, and clinical utility answer different questions. |
| Systematic review/meta-analysis | [PRISMA 2020](https://www.prisma-statement.org/prisma-2020) | A related-work narrative is not a systematic review without the actual search, selection and synthesis methods. |

For original medical research, use the journal's structured-abstract headings and required content. Reconcile the abstract with the body and report estimates with relevant uncertainty. Clinical importance and statistical significance are distinct. [ICMJE preparation guidance](https://icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html)

Do not activate trial registration or trial-flow requirements solely because a paper uses medical images or AI. Determine whether it actually reports a clinical trial, diagnostic study, model evaluation, or another design. Likewise, do not turn an image-quality metric improvement into a clinical benefit claim. These routing decisions are editorial synthesis of the design-specific scopes above.

## Declarations and final checks

Verify actual records for ethics/consent, registration where applicable, funding, competing interests, contributions, data/code availability, and assistance disclosures. Missing information is unresolved, not evidence of an exemption or no conflicts. Use truthful descriptions of the work performed. [ICMJE recommendations](https://www.icmje.org/recommendations/), [ICLR 2027 author AI policy](https://iclr.cc/Conferences/2027/AIPolicyForAuthors)

Keep three decisions separate: whether the prose is clear, whether the scientific claims are supported, and whether this version meets the applicable submission rules. A manuscript can satisfy one while failing another.
