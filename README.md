<p align="center">
  <img src="assets/banner.svg" alt="Paper Review Harness — Review deeply. Revise deliberately." width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.9 or newer">
  <img src="https://img.shields.io/badge/Reviewers-30_personas-7C3AED?style=flat-square" alt="30 reviewer personas">
  <img src="https://img.shields.io/badge/Venues-CVPR_%C2%B7_ICLR_%C2%B7_ICML_%C2%B7_NeurIPS-0891B2?style=flat-square" alt="CVPR, ICLR, ICML and NeurIPS">
  <img src="https://img.shields.io/badge/Workflow-No_repeat_churn-059669?style=flat-square" alt="No repeat churn by default">
</p>

<p align="center">
  <a href="#how-it-works">How it works</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#choose-your-venue">Venues</a> ·
  <a href="#choose-your-panel">Panels</a> ·
  <a href="#review-the-figures">Figures</a> ·
  <a href="#turn-reviews-into-a-revision-plan">Revision plan</a> ·
  <a href="#the-revision-loop">Revision loop</a> ·
  <a href="#reading-the-results">Results</a> ·
  <a href="#troubleshooting">Troubleshooting</a>
</p>

## Give your paper a demanding first audience

**Find the weak points in your paper. Revise them. Check whether the changes helped.** Paper Review Harness turns a PDF into independent simulated reviews, section scores, and a prioritized revision plan. Thirty personas cover CVPR, ICLR, ICML and NeurIPS. Choose a venue, examine the evidence through distinct scientific lenses, and track each open criticism through later drafts. Reviewers look at rendered figure images with measured text sizes, and an optional figure job checks each figure and table.

**Start here:** [Run a review with an agent](REVIEW_PAPER.md) · [Read the operating rules](AGENTS.md) · [Explore the supporting research](01_sources/README.md)

> This is an independent research tool for simulated feedback. It is not affiliated with these conferences, and its scores are not acceptance predictions.

## How it works

<p align="center">
  <picture>
    <source media="(max-width: 640px)" srcset="assets/workflow-mobile.svg">
    <img src="assets/workflow.svg" alt="One round of review and revision: (1) the Python CLI freezes the draft and writes one prompt per job; (2) each reviewer persona runs in a fresh agent; (3) the CLI validates and ranks the output into FEEDBACK.md and SCORES.md; (4) a writer agent or the author answers each point and rebuilds the PDF. In the next round each reviewer rechecks its own points: satisfied points close, partly and not satisfied points stay open, new issues are added." width="100%">
  </picture>
</p>

The **Python CLI** (cyan) prepares snapshots and prompts, validates outputs, and builds reports. It does not launch agents or call a model API. Your **agent environment** (violet) runs each reviewer in a separate context; a writer agent or the author revises the paper.

The figure shows the default `dialogue` loop. With `--loop fresh`, later rounds repeat full reviews from scratch instead of rechecking earlier points.

## Quick start

### 1. Set up the harness

You need **Python 3.9+**, **PyMuPDF**, a paper PDF with extractable text, and an agent environment. A supplement is optional. Supply the paper's source directory if you want a writer agent to revise it.

```sh
git clone <repository-url> paper-review-harness
cd paper-review-harness
python -m pip install pymupdf
python 06_scripts/hx.py personas
```

These examples use `python`; use `python3` if that is your Python command (common on macOS and Linux). [REVIEW_PAPER.md](REVIEW_PAPER.md) and [AGENTS.md](AGENTS.md) write `python3`.

<details>
<summary>Optional: install in a virtual environment</summary>

Before installing PyMuPDF, create and activate an environment:

**PowerShell**

```powershell
python -m venv ../paper-review-env
../paper-review-env/Scripts/Activate.ps1
python -m pip install pymupdf
```

**macOS / Linux**

```sh
python3 -m venv ../paper-review-env
source ../paper-review-env/bin/activate
python -m pip install pymupdf
```

The environment sits beside the repository so it is not included in commits or exports.

</details>

> [!TIP]
> **Let an agent run steps 2–5.** If your agent can read local files and start sub-agents, give it one line:
>
> ```text
> Follow REVIEW_PAPER.md for PAPER=path/to/main.pdf NAME=mypaper
> ```
>
> It creates the session, starts one fresh sub-agent per reviewer, validates, aggregates, and reports the scores. An agent that cannot start sub-agents should hand you the launch lines instead of reviewing in its own context. The steps below do the same by hand.

### 2. Create a review session

```sh
python 06_scripts/hx.py new --paper "path/to/main.pdf" --name mypaper
```

Replace `path/to/main.pdf` with your PDF path. This uses the defaults: the CVPR profile, **three reviewers** from the `realistic` panel, and `full` review mode. For ICLR, ICML or NeurIPS, add `--venue` ([Choose your venue](#choose-your-venue)). The output looks like this (paths shortened):

```text
session sessions/YYYY-MM-DD_mypaper
panel ['R12', 'R09', 'R03']
round 1 -> sessions/YYYY-MM-DD_mypaper/round_01

Launch one fresh agent per pending prompt (initial); give each exactly this instruction:
  [R03] Read sessions/YYYY-MM-DD_mypaper/round_01/prompts/initial/R03.md and follow it exactly. Write only the files it names.
  [R09] Read .../prompts/initial/R09.md and follow it exactly. Write only the files it names.
  [R12] Read .../prompts/initial/R12.md and follow it exactly. Write only the files it names.
```

The first line names your **session**. Wherever a command below says `<session>`, use that folder path or its full folder name (`YYYY-MM-DD_mypaper`, plus `_<tag>` if you passed `--tag`). The short `--name` alone is not the session identifier.

Each bracketed line is one **job** for one fresh agent. The default panel gives 3 jobs. `--mode both` adds dedicated section jobs (about 13 jobs in total for CVPR, 4–6 for the ML venues, depending on the sections found). `--figures` adds 1, and each `--heldout` ID adds 1.

| Optional input | Add to the command |
|---|---|
| Supplementary PDF | `--supp "path/to/supplement.pdf"` |
| Paper source directory | `--tex "path/to/latex"` |
| Separate evaluation reviewers | `--heldout R02,R11` |
| Dedicated section reviews as well | `--mode both` |
| Figure review job (FIG) | `--figures` ([Review the figures](#review-the-figures)) |

**Anonymity check.** `new` and `round` refuse a PDF that shows who wrote it or where it appeared: an author block or e-mail, a CVF or arXiv stamp, acknowledgements, grant numbers, or a link to the authors' own code. The refusal lists each flag with its page. Use the anonymous review copy, or add `--allow-identified` to review this copy anyway: `SESSION.json` records the choice, every reviewer prompt tells reviewers to ignore the information, and `SCORES.md` lists the flags. For a camera-ready or preprint copy, also pass `--cutoff <the paper's original submission deadline>`.

### 3. Check the extraction

Before launching reviewers, open two files in `round_01/snapshot/` inside the session folder:

- **`sections.json`**: the sections found, with their pages. Missing or merged sections give reviewers the wrong section texts.
- **`FIGURES.md`**: every figure and table found, with its crop image and measured facts. A figure flagged `not_located` is shown to reviewers on its page image.

If text or sections are badly extracted, fix the PDF (it needs a usable text layer) and create a new session with `--tag`.

### 4. Run independent reviewers

Give **each printed prompt to a fresh agent**, using exactly:

```text
Read <prompt path> and follow it exactly. Write only the files it names.
```

Start them in parallel, each in its own context, and add nothing about the paper, your goals, or the other reviewers. Review files appear only after those agents finish. [REVIEW_PAPER.md](REVIEW_PAPER.md) gives the orchestrating agent the full procedure.

### 5. Validate and read the results

```sh
python 06_scripts/hx.py validate "<session>"
python 06_scripts/hx.py aggregate "<session>"
```

`validate` also prints **warnings**, which do not fail a job: a `review.md` more than 20% outside the persona's word band, more weaknesses than the persona allows, a different number of points in `review.md` and `review.json`, and grounding problems (quotes not found in the paper; line, page, figure or table references the paper does not have). Read them as reliability notes; do not rerun a valid job only because of a warning.

**Run `aggregate` only after every job validates.** Then open these files inside the session folder:

1. **`round_01/FEEDBACK.md`** — what to fix first, why, and what would resolve it.
2. **`round_01/SCORES.md`** — overall recommendations and section-level weaknesses. The `Grounding:` line under the headline counts verified quotes and bad references.
3. **`round_01/reviews/<job>/debrief.md`** — what triggered a reviewer's reaction and the smallest useful change.
4. **`round_01/GROUNDING.md`** — each quote and reference that did not match the paper, per feedback reviewer (held-out details are in `heldout/GROUNDING.md`).

If a job fails validation, rerun that job with a fresh agent. Use `python 06_scripts/hx.py status "<session>"` to recover launch instructions for pending jobs only.

## Finish the useful work, then stop

A review request gets one careful panel review and its report. Revision is a separate requested task: make the changes, verify the evidence, and deliver. Additional panels, retests and score-optimization rounds are optional.

- **Resume, do not restart:** `hx.py status <session>` prints launch lines only for missing or invalid jobs.
- **Skip duplicates:** `round` creates no new round for byte-identical PDFs without changed, filled author answers. An empty response template does not count; use `retest` for an intentional repeat.
- **Process the current work:** `aggregate` validates and rebuilds only the latest round. Use `--round N` for an older repair or `--all` to rebuild history. Progress uses the saved reports.
- **Focus follow-ups:** changed-section hints direct attention to open points, changed evidence and dependent claims. Reviewers still inspect relevant figures; a text diff is not proof of unchanged visual evidence.
- **Keep feedback concise:** group duplicate concerns, reference evidence once, and leave resolved points closed unless new contrary evidence appears.

There is no hard cap on explicitly requested iterative work. Each additional pass needs a concrete purpose and new input; missing experiments are reported as blockers, not repeatedly requested through unchanged rounds. Existing sessions keep their frozen protocol text; start a new session to adopt the new concise review instructions.

## Choose your venue

<picture>
<source media="(max-width: 640px)" srcset="assets/venues-mobile.svg">
<img src="assets/venues.svg" alt="Four venue profiles: CVPR behavioral simulation; ICLR knowledge and mechanisms; ICML separate scientific dimensions; NeurIPS contribution-specific panels. Careful mode maps claims, inspects evidence, records uncertainty and explains judgement." width="100%">
</picture>

| `--venue` | Pinned guidance | Default review | Recommendation scale |
|---|---|---|---|
| `cvpr` | CVPR 2027; existing calibration sources | 3-person seeded `realistic` panel | Existing `cvpr26_5`; provenance recorded |
| `iclr` | ICLR 2027 | 3-person `balanced`, careful reading | **Harness-defined 1-5**, not a verified official form |
| `icml` | ICML 2026 main track | 3-person `balanced`, careful reading | Verified 1-6; Weak Reject / Weak Accept at 3/4 |
| `neurips` | NeurIPS 2026 main track | 3-person panel matched to contribution type, careful reading | Verified 1-6; Borderline Reject / Borderline Accept at 3/4 |

```sh
python 06_scripts/hx.py new --paper main.pdf --name mypaper --venue iclr
python 06_scripts/hx.py new --paper main.pdf --name mypaper --venue icml
python 06_scripts/hx.py new --paper main.pdf --name mypaper --venue neurips --contribution-type negative_results
python 06_scripts/hx.py personas --venue neurips
```

These are alternative examples; use a different `--name` or `--tag` if running several on the same day. Venue aliases are case-insensitive. Known full labels such as `ICML 2026` are accepted; unknown years are rejected rather than silently assigned old rules.

**Careful reading is the default for ICLR, ICML and NeurIPS.** It checks central claims against specific evidence, inspects relevant appendices and figures, and records what was not checked. It removes forced score offsets, premature first-impression ratings and invented weaknesses. Add `--reading careful` to use it with CVPR too; each CVPR persona card is then reduced to its name, used as a lens, without its reading habits or rating offset. The original CVPR behavior simulation remains available by default.

Every careful review includes an `evidence_audit` in its JSON. ICML and NeurIPS also include four separately justified venue dimensions. Validation checks the output structure and ranges; a human or orchestrator must still examine the scientific observations. Read unchecked coverage as an unresolved limitation, not evidence that the paper is wrong.

<details>
<summary><strong>Meet the 14 new scientific reviewer lenses</strong></summary>

| Venue | Persona IDs and focus | Panel choices |
|---|---|---|
| ICLR | I01 representation/mechanism; I02 empirical reliability; I03 mathematics; I04 knowledge/scope | `balanced`, `empirical`, `gauntlet` |
| ICML | M01 theory/assumptions; M02 experimental design; M03 algorithms/originality; M04 practical significance | `balanced`, `empirical`, `gauntlet` |
| NeurIPS | N01 broad contribution; N02 theory; N03 use-inspired; N04 concept/feasibility; N05 negative results; N06 reproducibility/responsible evaluation | `balanced`, `theory`, `use_inspired`, `concept_feasibility`, `negative_results`, `gauntlet` |

NeurIPS accepts `--contribution-type general|theory|use_inspired|concept_feasibility|negative_results`. Choose the author's declared type. Unless you supply `--panel`, a non-general type selects its specialist panel. A panel changes reviewers; the contribution type changes evaluation criteria. All reviewers honor the declared type even with a custom panel. The `theory` panel has the same members as `balanced` (N01, N02, N06). The NeurIPS section map (`--mode sections` or `both`) assigns specialists by section whatever the contribution type: N02 and N04 read the method, N03 and N05 the experiments.

New panels are curated fixed sets, so `--seed` does not change them. They are not estimates of real reviewer frequencies. `gauntlet` includes only the selected venue's personas. Custom `--reviewers` and `--heldout` IDs must belong to that venue. `--mode sections` and `both` use that venue's dedicated section assignments.

</details>

New sessions embed their rules, persona cards, rubrics, scales and section assignments so later rounds use the same instruments. Old sessions keep their legacy behavior. Scores from different profiles or reading modes are not directly comparable. Page budgets live in `AUTHOR_CONSTRAINTS.md`; ICLR 2027's budget requires confirmation before layout revisions.

[Read the source-backed design and its limitations](01_sources/multi_venue_review_design.md). The revision loop is for preparing a draft; it does not reproduce official rebuttal submission rules.

## Choose your panel

The presets below are for **CVPR**. For ICLR, ICML and NeurIPS, use the venue-specific panels above.

| Panel | Reviewers | Best used for |
|---|---|---|
| `realistic` | 3, drawn from expertise pools | A varied first assessment. |
| `realistic4` | 4, drawn from expertise pools | One more perspective on the draft. |
| `quick` | R09 · R03 · R08 | An initial pass across first impressions, expertise, and accessibility. |
| `stress` | R02 · R03 · R05 · R11 | Novelty, technical rigor, and difficult objections. |
| `writing` | R07 · R08 · R09 · R12 | Clarity, narrative, and how the contribution comes across. |
| `core` | R01 · R02 · R03 · R05 · R07 · R09 · R11 | Broad coverage with seven perspectives. |
| `gauntlet` | All 16 personas | A comprehensive pass before submission. |

**A practical starting point:** use `realistic` for a broad first review, `writing` to focus on presentation, or `stress` to probe difficult objections.

`--seed 1` draws a different `realistic` or `realistic4` panel; fixed panels ignore it. A new seed needs a new session (add `--tag`); to measure score noise, use `retest` instead. Use `--reviewers R03,R11` to select specific reviewers. The panel stays fixed across revisions within a session.

| Mode | Behavior |
|---|---|
| `full` **(CLI default)** | Whole-paper reviews, with section scores for the sections each reviewer reads. |
| `sections` | Dedicated section-review jobs, without overall recommendations. |
| `both` | Whole-paper reviews plus dedicated jobs from the section panel. |

For a focused pass, add `--sections abstract,introduction`. The section panel uses its own [section-to-persona mapping](04_panels/section_panel.json).

<details>
<summary><strong>Meet the 16 original CVPR reviewer personas</strong></summary>

| ID | Persona | Primary focus |
|---|---|---|
| R01 | Leaderboard reviewer | Baselines, datasets, and the main results table. |
| R02 | Novelty skeptic | Closest prior work and what is actually new. |
| R03 | Subfield expert | Technical details and field-specific expectations. |
| R04 | Theory checker | Assumptions, proofs, and the role of theory. |
| R05 | Rigor methodologist | Fair comparisons, seeds, tuning, and ablations. |
| R06 | Efficiency pragmatist | Runtime, memory, scaling, and practical cost. |
| R07 | Clarity editor | Definitions, structure, figures, and readability. |
| R08 | Adjacent generalist | Intuition and relevance beyond the immediate subfield. |
| R09 | Busy senior | Opening pages, figures, and first impressions. |
| R10 | Junior checklist | Completeness, implementation details, and expected comparisons. |
| R11 | Hostile Reviewer 2 | Ambiguous claims and weaknesses a skeptical reader could press. |
| R12 | Champion | Clear contributions and evidence a supporter can defend. |
| R13 | Reproducibility auditor | Missing settings and results that can be checked. |
| R14 | Competing lab | Attribution and comparison with the closest research line. |
| R15 | LLM-assisted reviewer | Generic objections and surface-level reading patterns. |
| R16 | Misassigned outsider | Whether the paper makes sense outside its niche. |

Persona definitions live in [03_personas/](03_personas/); their supporting research lives in [01_sources/](01_sources/).

</details>

## Review the figures

Every snapshot renders what a reader sees. `snapshot/pages/` holds page images; `snapshot/figures/` holds a crop of each figure and table with its caption, a `_gray` preview and, for colour figures, a `_deuteranopia` preview. `snapshot/FIGURES.md` (and `figures/figures.json`) lists them with measured facts: smallest vector text in pt, raster resolution in ppi, first mention in the text, and flags such as `small_text` (below 6 pt), `low_resolution` (below 150 ppi) and `not_referenced`. Every reviewer prompt points to these files, so reviewers judge figures from the images and the measurements, not from captions.

For a dedicated figure pass, add `--figures` when creating the session:

```sh
python 06_scripts/hx.py new --paper "path/to/main.pdf" --name mypaper --figures
```

This adds one job, `FIG`, run by persona F01, "The Figure Reader", with any venue.

- **Scope:** section-only (no overall rating); never drawn into a panel.
- **Output:** a 1–10 score for every main-paper figure and table, with six criteria (message clarity, legibility, encoding fit, accessibility, caption alignment, comparison fairness), and located defects such as `illegible_text` in "Fig. 3, legend", each with a fix. `SCORES.md` and `FEEDBACK.md` gain a "Figure scores (FIG job)" table, lowest first.
- **Later rounds:** FIG compares the old and new crop of each open point and re-scores every figure; `stage pairwise` also compares changed figure crops blind.
- **Data lock:** the writer may change how a figure looks; changing the data it shows needs your approval.

Rules and anchors: [figure_review_rules.md](02_protocol/figure_review_rules.md), [figure_rubric.md](02_protocol/figure_rubric.md).

## Turn reviews into a revision plan

The reviews are deliberately realistic: terse, sometimes harsh, one list per reviewer. After `aggregate`, an optional coach agent merges them into one prioritized, constructive plan:

```sh
python 06_scripts/hx.py stage "<session>" coach
```

Give the printed `[COACH]` line to one fresh agent. Like `stage writer`, the command works on the latest non-retest round and refuses to run until that round validates. The coach writes two files in `round_NN/coach/`:

- **`REVISION_PLAN.md`**: where the paper stands, strengths to keep, the 3–5 changes that matter most with proposed text, the full plan by section, experiments to consider (and what to write if you cannot run them), where reviewers disagree, and points not worth acting on.
- **`revision_plan.json`**: the same plan for tools. `validate` checks it as the job `COACH`: every open point is planned, requested as an experiment or deferred, exactly once.

The plan has no scores and no reviewer voice, so you can share it with co-authors. The coach reads `FEEDBACK.md`, the feedback reviewers' files, the snapshot and `AUTHOR_CONSTRAINTS.md`. It never opens held-out reviews, `SCORES.md`, `PROGRESS.md` or the LaTeX sources, and it proposes text without inventing results. When a plan exists, the writer brief lists it first.

## The revision loop

**Review → prioritize → revise → check the answers → review again.**

1. **Prepare the writer.** Record your source directory with `--tex "path/to/latex"` when creating the session, or set `tex_dir` in its `SESSION.json` to the absolute source-directory path before starting the writer. Then generate the brief and answer sheet:

   ```sh
   python 06_scripts/hx.py stage "<session>" writer
   ```

   It works on the latest non-retest round and refuses to run until that round validates. The brief points to `FEEDBACK.md` and the feedback reviewers' files, never to `SCORES.md` or `PROGRESS.md`, which can contain held-out results. If you ran `stage coach`, the brief lists `REVISION_PLAN.md` first; `RESPONSE.md` still answers every point.

2. **Address every open point.** Run the printed writer prompt with a writer agent, or follow it yourself. Fill in `writer/RESPONSE.md`, edit the paper sources, rebuild the PDF, and record changes. Each answer should identify the evidence or exact change that resolves the concern. The `stage` command only prepares the brief and answer sheet.

3. **Create the next round.** Supply the revised PDF and, if applicable, the revised supplement:

   ```sh
   python 06_scripts/hx.py round "<session>" --paper "path/to/revised-main.pdf" --supp "path/to/revised-supplement.pdf"
   ```

   Omit `--supp` if there is no supplement. Pass it again when there is one; a revised round does not automatically reuse the previous supplement. `round` refuses to run until the previous round validates.

4. **Run every printed prompt.** In the default `dialogue` loop, fresh instances of the same personas get `satisfy` prompts and check their own feedback threads against the revised draft. A point can be `satisfied`, `partly`, or `not_satisfied`; new issues can be raised. Held-out reviewers, and every reviewer under `--loop fresh`, get `initial` prompts and assess the draft from scratch.

5. **Validate and aggregate again.** Read the updated `FEEDBACK.md` and session-wide `PROGRESS.md`, then report completed fixes and remaining blockers. Start another revision only when useful work remains within the requested scope.

**Finish once the requested changes are verified.** Continue an explicitly requested iterative campaign only with a concrete unresolved issue and new evidence, a changed draft or a substantive answer. There is no hard round cap, but no automatic retesting, cosmetic churn or reopening of resolved points.

Use the session's `AUTHOR_CONSTRAINTS.md` to record project requirements, permitted experiments, and writing preferences. The writer reads this file; reviewers do not.

### Check whether a revision helped

- **Held-out reviewers:** add `--heldout R02,R11` when creating a session. Their reviews stay separate from the writer's feedback. Use a different model from the writer for held-out reviews and blind judging.
- **Repeatability:** `python 06_scripts/hx.py retest "<session>"` prepares fresh reviews of an unchanged draft. Run those prompts, validate, and aggregate to estimate score variability.
- **Fresh reviews:** choose `--loop fresh` at session creation to repeat the configured review jobs from scratch on later rounds. Unlike dialogue reviewers, these reviewers do not receive the earlier feedback thread or the writer's answers.
- **Fix checks and blind comparison:** after a revised round, use the commands below and run their printed prompts to check resolved weaknesses and compare changed sections and figure crops.

```sh
python 06_scripts/hx.py stage "<session>" fixcheck
python 06_scripts/hx.py stage "<session>" pairwise
```

Read scores alongside the underlying evidence. Language-model reviewers can share blind spots, and small score changes can be noise. [AGENTS.md](AGENTS.md) defines the independence and revision-acceptance rules.

## Reading the results

### From criticism to a concrete next step

Every point in `FEEDBACK.md` names a location, a fix, and a test for resolving it. After a revision, it also carries the reviewer's latest verdict. An invented example, in the exact format the harness writes after one revision:

```markdown
### R06:W2 - major, efficiency - The Efficiency Pragmatist [partly]
- **Where:** Sec. 5.3, Table 2
- **Complaint:** The 3x speedup is reported without hardware or batch size, so it cannot be checked.
- **Their suggested fix:** State the GPU, batch size, and resolution next to Table 2.
- **What would satisfy them:** Enough setup detail to tell whether the runtimes are comparable.
- **Fixable by (their guess):** writing
- **Their last verdict (partly):** The GPU is now stated, but the baselines were timed at a different batch size.
- **Still asking for:** Re-time the baselines at batch size 1, or explain why that is not possible.
```

The writer answers each point in `RESPONSE.md` with a change or an evidence-backed explanation. In the next round, a fresh instance of the same persona rules it `satisfied` (closed), `partly`, or `not_satisfied` (both stay open).

### Understand the scores

**Read the criticisms before optimizing the numbers.** A higher mean can hide one decisive objection or a weaker section.

| Signal | How to interpret it |
|---|---|
| Overall recommendation | CVPR (`cvpr26_5`) and ICLR (`iclr_harness_5`) use 1–5: Reject, Weak Reject, Borderline, Weak Accept, Strong Accept. ICML and NeurIPS use their own 1–6 labels ([Choose your venue](#choose-your-venue)). |
| First impression | CVPR persona mode only: the recommendation recorded after the initial skim, before the detailed read. Null in careful mode. |
| Section score | A 1–10 assessment tied to [section rubrics](02_protocol/section_rubrics.md). Each sub-criterion is scored on a separate 1–5 scale. |
| Figure score | With `--figures`: a 1–10 score per figure and table from the FIG job, with six 1–5 criteria. |
| Decisive weakness | A concern the reviewer considers sufficient to block acceptance by itself. |
| Satisfaction status | Whether the revised draft resolves a particular point; unresolved and new points remain in the feedback list. |
| Progress across rounds | Changes in scores, including noise thresholds when repeat reviews are available. |

The headline uses held-out reviewers when present; otherwise it uses feedback reviewers. Section scores are a harness addition. Rating profiles and their source notes live in [scales.json](02_protocol/scales.json).

### Output map

| Artifact | Purpose |
|---|---|
| `round_NN/SCORES.md` · `SCORES.json` | Overall and section scores, reviewer comparisons, and decisive weaknesses. |
| `round_NN/FEEDBACK.md` · `FEEDBACK.json` | Open issues, suggested fixes, and satisfaction criteria. |
| `round_NN/reviews/<job>/` | Initial review, structured scores, and an explanatory debrief. |
| `round_NN/heldout/<job>/` | Held-out reviews; kept out of `FEEDBACK.md` and the writer brief. |
| `round_NN/satisfaction/<job>/` | Follow-up replies and point-by-point satisfaction judgments. |
| `round_NN/coach/` | Optional revision plan: `REVISION_PLAN.md` (shareable) and `revision_plan.json`. |
| `round_NN/writer/` | Answer sheet, change log, and experiment requests. |
| `round_NN/snapshot/` | Frozen PDFs, extracted text, and section views for that round. |
| `round_NN/snapshot/FIGURES.md` · `figures/` · `pages/` | Figure inventory with measured facts, figure crops with gray and deuteranopia previews, and page images. |
| `PROGRESS.md` | Session-wide score history and repeatability information. |

<details>
<summary><strong>Repository map and CLI reference</strong></summary>

```text
01_sources/       Research behind the review design
02_protocol/      Review forms, scoring rubrics, figure rules, and writer rules
03_personas/      Reviewer persona cards and their registry
04_panels/        Whole-paper and section panel definitions
05_templates/     Output schemas and author constraints
06_scripts/       Python CLI, harness library, tests, and exporter
assets/           README logo, banner, and workflow figures
sessions/         Local paper snapshots and review campaigns
```

| Command | Purpose |
|---|---|
| `personas` | List the available reviewer personas. |
| `new` | Create a session and prepare the first review prompts. |
| `status <session>` | Inspect jobs, output files, and launch instructions. |
| `validate <session>` | Check review outputs against the expected schema; print advisory warnings. |
| `aggregate <session> [--round N | --all]` | Generate scores, feedback, grounding, and progress reports. |
| `stage <session> coach` | Prepare the coach prompt: one prioritized revision plan from the feedback reviews. |
| `stage <session> writer` | Prepare the writer brief and response scaffold. |
| `round <session> --paper <pdf>` | Create the next round from a revised draft. |
| `retest <session>` | Prepare fresh reviews of an unchanged snapshot. |
| `stage <session> fixcheck` | Prepare a check of earlier weaknesses. |
| `stage <session> pairwise` | Prepare a blind comparison of changed sections and figures. |

Use `python 06_scripts/hx.py <command> --help` for command-specific options. Select a versioned profile with `--venue`. `--cutoff` is an optional search boundary, not a replacement for venue policy. New ML profiles enforce their documented scales; `--scale` remains available for legacy CVPR calibration.

</details>

## Troubleshooting

| What you see | What to do |
|---|---|
| `No module named fitz` | Install PyMuPDF with the same interpreter: `python -m pip install pymupdf`. |
| `No SESSION.json` | Use the exact printed session path or full date-prefixed folder name, rather than only `mypaper`. |
| Session already exists | Add `--tag second-pass` to create a separate session, or use `round` to revise the existing one. |
| Prompts exist but no reviews | Run the printed reviewer jobs in your agent environment; `new` only prepares them. |
| Validation reports `FAIL` | Inspect the reported errors and rerun the affected job with a fresh agent. |
| `new refused` or `round refused` after an anonymity check | Use the anonymous review copy, or add `--allow-identified` (and `--cutoff` for a camera-ready or preprint copy); see [step 2](#2-create-a-review-session). |
| Poor or missing extracted text | Inspect `snapshot/sections.json` and `paper_main.txt`; use a PDF with a usable text layer before starting the review. |
| `FIGURES.md` flags a figure `not_located` | Use its page image (`snapshot/pages/<doc>_pNN.png`); reviewer prompts already point to it. |
| A review makes a colour claim | Open the figure's `_deuteranopia` and `_gray` previews in `snapshot/figures/`; the claim holds only if two colours that carry meaning become indistinguishable there. |
| Small or inconsistent score gains | Inspect the underlying evidence; report score changes as descriptive. Use `retest` only when deliberately measuring variability. |

## Development and sharing

Run the mechanics checks after changes to scripts, personas, panels, or protocol:

```sh
python 06_scripts/hx.py personas
python 06_scripts/smoke_test.py
python 06_scripts/test_venues.py
python 06_scripts/test_efficiency.py
python 06_scripts/test_figures.py
python 06_scripts/test_figure_job.py
python 06_scripts/test_figure_locate.py
python 06_scripts/test_loop_regressions.py
python 06_scripts/test_validation_regressions.py
python 06_scripts/test_grounding.py
python 06_scripts/test_anonymity.py
python 06_scripts/test_prompts.py
python 06_scripts/test_integration.py
python 06_scripts/test_coach.py
```

The tests use synthetic PDFs and simulated review records; they make no model calls.

Sessions contain paper snapshots and reviews and are excluded from Git by default. To package the reusable harness without sessions, caches, or build notes:

```sh
python 06_scripts/export_public.py
```

The exporter writes a folder and ZIP under `release/`. It scans exported text for generic identifying patterns (home-directory paths, e-mail addresses) plus any private patterns listed in `00_plan/deid_patterns.txt`; it does not check Git history or topic wording. Model execution and data handling depend on the agent environment you choose.
