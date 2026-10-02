# Project specification

## Assignment

See [sujet.md](../sujet.md) for the original assignment. This document records the team's decisions as the study develops.

## Objective

Use steel weld data to investigate which measured properties represent weld quality and evaluate how well those properties can be predicted from available inputs. Derive evidence-supported recommendations and summarize the study in an approximately five-page report.

## Dataset and preprocessing

- Source: the Cambridge welding database linked in the assignment.
- Record the downloaded files, retrieval date, variable definitions, units, and missing-value encodings in `data/README.md`.
- Describe distributions, missingness, duplicated or related observations, and plausible data-quality issues.
- Justify each transformation, including imputation and the choice to scale or leave features unscaled.
- Use PCA to explore structure and explain the variance captured by its components.

## Prediction task

To decide after inspecting the dataset:

- Target variable(s), their physical meaning, and their relationship to weld quality.
- Regression or classification framing, including any justified thresholds.
- Input features available at prediction time and excluded leakage-prone variables.
- Treatment of observations without target labels, separately for each target if necessary.

## Validation protocol

- Define cross-validation splits and justify any grouping required by related observations.
- Fit all learned preprocessing within each training fold.
- Use inner validation for parameter tuning when needed; evaluate competing methods on common outer splits.
- Keep evaluation labels separate from training and pseudo-label generation.
- State whether unlabeled data comes only from the training partition and whether the semi-supervised protocol is inductive or transductive.
- Record random seeds and report variation across validation folds.

## Models and metrics

- Establish a simple baseline.
- Compare suitable supervised methods covered in class.
- Research, justify, and apply at least one semi-supervised method appropriate to the selected task.
- Select metrics after defining the targets; explain their formulas, units, and practical interpretation.
- Compare methods under the same evaluation protocol.

## Deliverables

- EDA and modeling notebooks backed by reusable Python code.
- Reproducible results and figures supporting model comparisons.
- An approximately five-page report with team details, task formulation, dataset description, PCA, method justifications, metric definitions, numerical results, discussion, conclusions, and evidence-supported welding recommendations.
- A Gantt diagram documenting tasks, actual time spent, and responsible team members.
- References cited in the report, page numbers, and titled figures and tables referenced in the text.

## Decisions and experiment log

Record decisions here as they are made. No target, final model, or semi-supervised method has been selected yet.
