# Synthetic manuscript for harness validation

## Abstract

We test a confidence gate that defers uncertain image classifications to a human reviewer. On a synthetic held-out split, test accuracy was 82.4% at the prespecified operating point [@synthetic-results]. This descriptive result does not establish a causal effect or performance on clinical data.

## Introduction

Image classification systems can give confident answers on uncertain inputs. We examine whether an uncertainty gate makes the tradeoff between automatic coverage and human review explicit. The contribution is a reproducible evaluation protocol for this synthetic example, rather than a claim of deployment readiness.

## Methods

The uncertainty gate defers an input when its maximum predicted probability falls below a threshold selected using the validation split. The held-out split is used once for descriptive reporting. The same preprocessing and split assignments apply to both configurations. These choices are specified in the synthetic protocol [@synthetic-protocol].

## Results

Test accuracy was 82.4% at the selected operating point [@synthetic-results]. Automatic coverage was 71.0%. The experiment uses one synthetic split and does not estimate uncertainty across independent datasets. A reader should inspect the protocol and complete output before comparing this result with another system.

## Limitations

The synthetic data do not represent clinical image distributions. We have not evaluated clinician workload, patient outcomes, or robustness across acquisition devices. The reported associations do not establish that the gate causes an improvement. Source registry entries in this fixture are invented solely to test the harness.
