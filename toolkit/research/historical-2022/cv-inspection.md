# CVPR / ICCV historical writing inspection

Date: 2026-10-30. Scope: six abstract/introduction pairs from the 100-paper CV shard, all published by 2022. The full PDFs were downloaded, but only the abstract and introduction were semantically inspected. This is a qualitative writing inspection, not a scientific reproducibility review or a full-paper read.

The corpus contains 25 CVPR papers per year for 2020, 2021 and 2022, plus 12 ICCV 2019 and 13 ICCV 2021 papers. Collection uses evenly spaced ranks over title-sorted official main-conference proceedings. The six inspection examples are the first extractable selected titles in each year stratum, with one additional CVPR 2020 example. This favors early alphabetical titles and must not be described as a random or quality-ranked sample. Workshop papers are excluded.

## Observations grounded in inspected text

### 1. Separate the supervision signal from the architecture

**Paper:** ["Looking at the Right Stuff" - Guided Semantic-Gaze for Autonomous Driving (CVPR 2020)](https://openaccess.thecvf.com/content_CVPR_2020/html/Pal_Looking_at_the_Right_Stuff_-_Guided_Semantic-Gaze_for_Autonomous_CVPR_2020_paper.html).

The abstract introduces a semantic augmentation and then the larger prediction framework. The introduction makes the motivation concrete by enumerating ways that recorded gaze can fail to capture task-relevant attention. This connects an observable failure to a proposed input or supervision change.

**Reusable check:** identify whether each named entity is a target label, an input, a module, or a complete system. Preserve that role from the abstract through the introduction and methods. Here SAGE and SAGE-Net should not silently become interchangeable. For a statement such as performance on 49 of 56 cases, retain the denominator and definition of a case; do not rewrite it as an unqualified accuracy score. Broad safety implications require evidence beyond improved saliency prediction.

### 2. Teach the task before naming the machinery

**Paper:** [Actor-Transformers for Group Activity Recognition (CVPR 2020)](https://openaccess.thecvf.com/content_CVPR_2020/html/Gavrilyuk_Actor-Transformers_for_Group_Activity_Recognition_CVPR_2020_paper.html).

The introduction uses an individual player's motion and a volleyball group's activity to distinguish two levels of prediction. The abstract and introduction maintain the same mapping between static actor information and pose features, and between dynamic information and video features. Readers can connect the vocabulary to a specific representation.

**Reusable check:** ask a reader to distinguish the target tasks and the model's information sources before reading the methods. Keep a concept table mapping static/dynamic, individual/group, and input/representation/output. The abstract's qualitative claim about a performance margin is less informative than a result with a named metric, benchmark and comparator; publication does not make every stylistic choice exemplary.

### 3. Give each component a location and a job

**Paper:** [(AF)2-S3Net: Attentive Feature Fusion With Adaptive Feature Selection for Sparse Semantic Segmentation Network (CVPR 2021)](https://openaccess.thecvf.com/content/CVPR2021/html/Cheng_AF2-S3Net_Attentive_Feature_Fusion_With_Adaptive_Feature_Selection_for_Sparse_CVPR_2021_paper.html).

Both sections connect feature fusion to the encoder and feature selection/reweighting to the decoder. The introduction's contribution list repeats those roles, making the architectural claims traceable. Its sensor background also illustrates why a review should check how long it takes to reach the specific research limitation.

**Reusable check:** a component description should state its location, consumed representation, operation and intended effect. A claim about leaderboard position must retain its historical time qualifier. Normalize typographic forms such as `(AF)2-S3Net` and `AF2-S3Net` through an explicit alias table instead of treating typesetting variants as separate methods.

### 4. Preserve the population attached to every result

**Paper:** ["The Pedestrian Next to the Lamppost" Adaptive Object Graphs for Better Instantaneous Mapping (CVPR 2022)](https://openaccess.thecvf.com/content/CVPR2022/html/Saha_The_Pedestrian_Next_to_the_Lamppost_Adaptive_Object_Graphs_for_CVPR_2022_paper.html).

The introduction distinguishes map regions corresponding to objects from background surfaces, describes a distance-related localization failure, and motivates relationships between objects. The abstract's improvement claim concerns a particular object subset and benchmark context. Those restrictions are part of the claim, not expendable wording.

**Reusable check:** attach every percentage to a metric, population, comparator and relative/absolute interpretation. Do not generalize an object-subset improvement to all map categories. Define technical category names once, then use the same category boundary across prose, tables and figures.

### 5. Connect failure conditions to control decisions

**Paper:** ['Skimming-Perusal' Tracking: A Framework for Real-Time and Robust Long-Term Tracking (ICCV 2019)](https://openaccess.thecvf.com/content_ICCV_2019/html/Yan_Skimming-Perusal_Tracking_A_Framework_for_Real-Time_and_Robust_Long-Term_Tracking_ICCV_2019_paper.html).

The introduction distinguishes long-term tracking through sequence length and target disappearance rather than relying only on a broad claim that the task is difficult. The abstract describes how a verification score determines local or global search, and the two named modules have different roles in that decision process.

**Reusable check:** write the causal design rationale as a failure condition, required capability, mechanism and observable evaluation. Keep component names tied to those operations. Claims of real-time operation need a runtime definition and hardware context from the experiments; the title alone is not sufficient evidence.

### 6. Make apparent contradictions explicit through assumptions

**Paper:** [(Just) A Spoonful of Refinements Helps the Registration Error Go Down (ICCV 2021)](https://openaccess.thecvf.com/content/ICCV2021/html/Agostinho_Just_A_Spoonful_of_Refinements_Helps_the_Registration_Error_Go_ICCV_2021_paper.html).

The abstract and introduction explain how an estimator can be optimal for fixed correspondences while a different training procedure improves the correspondences themselves. The problem changes at the training objective, so the two statements do not inherently contradict each other. The introduction also distinguishes an extra training layer from inference cost.

**Reusable check:** when two claims seem incompatible, compare their assumptions, optimized variable and operating phase before editing either. Track training versus inference, fixed inputs versus learned inputs, and module-level versus system-level outcomes. Preserve the qualification on a maximum reported relative error decrease; do not turn it into a universal gain.

## Proposed review questions

1. Can a reader state the task, limitation, mechanism and evidence after reading only the abstract?
2. Does each introduction explain why a limitation leads to the proposed design?
3. Does every technical name keep one role, with justified typesetting aliases recorded?
4. Are task subsets, datasets, metrics, denominators and historical qualifiers preserved in each repeated claim?
5. Can a reader explain the distinction between training behavior and deployed behavior?
6. Are claimed benefits supported by the relevant experiment, rather than inferred from a benchmark name or publication venue?

These are candidate editorial checks motivated by six inspected examples. Neither this sample nor acceptance at a venue establishes that a writing pattern causes acceptance. No empirical estimate of writing quality or acceptance probability is made.

## Reproduction and evidence boundaries

Collection command: `python paper-writing/scripts/collect_historical_cv.py --output-root research/historical-2022 --download`.

The collection log records source URLs and request outcomes. Each downloaded PDF has a SHA-256 digest. `cv-inspection.json` records the six section-level reviews and original observations; `cv-inspection-candidates.json` retains extracted text for inspection. PDF source block order was used to reduce two-column interleaving. Figure captions, footnotes and page headers can still occur in the extraction, so extraction is not itself proof of reading. The six reviews were performed after viewing the extracted abstracts and introductions. No claim is made that the full methods, experiments or references were checked.
