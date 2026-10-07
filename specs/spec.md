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

### Preliminary EDA audit — 2026-10-03

The checked observations, unit uncertainties, distribution analysis, and proposed next steps are recorded in [the first-part report draft](../reports/01_eda_report.md) and [the detailed audit](../reports/01_eda_audit_details.md). This audit makes no unit correction and does not adopt a target, preprocessing pipeline, grouping rule, or model.

- Distinguish exact numeric values, missing measurements, censored values, intervals, and annotations. The current distribution plots describe exact numeric values only.
- Verify possible source-dependent unit differences before any conversion, especially aluminium in EPRI records and tin/arsenic/antimony in the same 90 records. No automatic conversion based on value magnitude is justified.
- Resolve nitrogen and hardness annotations and confirm the meaning of zero-valued PWHT settings and electrode polarity before preprocessing.
- General physical-bound checks do not confirm domain validity or unit consistency; `fatt_50` had no bound check because its unit was unspecified.
- Inspect repeated weld identifiers, related variants, and publication sources before choosing validation groups. Keep unresolved choices pending until this inspection and task definition are complete.

### Proposed preprocessing investigation — 2026-10-05

The user requested further analysis and a plan before notebook implementation. The [preprocessing plan](../reports/02_preprocessing_plan.md) records additional raw-data checks, proposed status-specific handling, grouped masking experiments, and separate PCA analyses for inputs and mechanical properties. These are proposals, not adopted transformations or completed experiments; no target or final grouping rule is selected.

- Missingness depends on observed welding process: nickel is absent in 70.0% of `MMA` rows versus 14.6% of `SA` rows. Current/voltage are jointly absent in the same 248 rows. Compare global and process-aware imputation rather than assuming random missingness.
- There are 650 rows with all four tensile properties observed, 144 with both yield strength and Charpy energy, and none with both Charpy energy and hardness reported, including annotated hardness. Explore mechanical-property relationships on observed subsets before considering reconstruction.
- In 89 rows with five exact microstructure fractions, three sums differ from 100% (90%, 99%, 119%). The 119% row is `Evans-Ti/CMn-1992-P0.1mic` at pandas index 582. Verify definitions and provenance before normalization or independent imputation.
- Proposed comparisons: median, process-specific median with fallback, and constrained multivariate imputation on inputs; assess grouped masking error, distributions, correlations, and PCA stability. Keep censoring/interval approximations in separate sensitivity scenarios and preserve their original status and bounds.
- Keep sparse variables available for secondary analyses without claiming domain irrelevance. Fit learned preprocessing within training folds for predictive evaluation; never use imputed targets as measured labels. Notebook implementation is pending.

### Implemented preprocessing investigation — 2026-10-05

The user approved implementation of the investigation. `notebooks/01_eda.ipynb`
now calls reusable functions in `src/weld_quality/schema.py`, `preprocessing.py`,
`exploration.py` and `plotting.py`. Existing exploratory cells are preserved.
This implements comparisons and sensitivity diagnostics, not a final target,
scientific imputation winner or verified correction of source units.

- Raw strings are retained independently of `df`. Exact values, original status,
  lower/upper bounds, censor operators, annotation tokens, review flags and
  estimated-cell provenance are exported separately. `N` and the notebook's
  documented missing encodings mean unreported, never measured zero.
- Review positive values below 1 ppm for titanium/aluminium/tin/arsenic/antimony,
  `<0.01` for titanium/aluminium, and `<5` for vanadium. These are unresolved
  heuristics, not proven errors. Reviewed cells are unavailable in numeric
  scenarios and remain distinguishable from original absences if estimated.
  Nitrogen `tot`/`res`/`nd` and hardness Vickers protocols are extracted lexically
  without semantic reinterpretation or automatic pooling.
- Numeric scenarios use nonnegative left-censor substitutions 0, L/2, L/sqrt(2)
  only outside review flags, and interval positions lower/midpoint/upper. These
  are explicit approximations, not inferred true values. Measured zeros and
  extreme values are retained; no automatic unit conversion is performed.
- Documented process synonyms `ShMA -> MMA` and `SMA -> SA` are normalized.
  Other modalities are unchanged. Categories and missingness indicators are
  supplementary to the main numeric PCA.
- Verification groups use inspected identifier prefix/year series, explicit
  undated/letter/report families and exact-ID fallback. Exact raw duplicates
  excluding identifiers connect otherwise distinct series. The linked
  `Evans-V/Mn-1991` and `Evans-Nb/Mn-1991` series illustrate this conservative
  rule. These are identifier-derived series, not validated publication IDs;
  grouping must be reconsidered for the final generalization task.
- GroupKFold uses 3 folds, deterministic default ordering without shuffle.
  Mask seeds are 42 and 43, requested rates 10/20/40%, and patterns are cells
  and empirical training-only blocks. PWHT temperature/time are masked jointly.
  Test truths consist only of exact, usable inputs. All methods receive the
  same masks and folds; SHA-256 mask hashes and row-level split assignments
  are exported. Reconstruction error on observed cells does not establish
  accuracy on genuinely unreported measurements.
- Candidates: global median; process median requiring at least 3 distinct
  observed training groups per feature with global fallback; IterativeImputer
  with default BayesianRidge, median initialization, ascending order,
  random_state=42, max_iter=100, tol=1e-3, skip_complete=False. Iterative scaling
  and one-hot process categories are fitted on training only; unseen categories
  have an all-zero encoding. Convergence state is recorded rather than hidden.
  No entirely unobserved training column is fabricated.
- Broad physical bounds constrain estimates only. Original values are preserved.
  Missing PWHT pairs are projected onto nearest actual joint training pairs
  using training standard deviations; partial observations require compatible
  pairs. This preserves empirical pair structure without claiming confirmed
  semantics of the zero-valued regime.
- Report MAE/RMSE in native units by variable, process and series. Normalize MAE
  by training IQR, with standard-deviation fallback; leave it undefined for
  constant training columns. Summaries are macro averages, not raw-unit averages.
  Correlation reconstruction uses the same originally exact pairs, requiring
  at least 20 pairs. A diagnostic PCA/scaler is fitted on complete exact TRAINING
  inputs only; held-out exact rows are transformed to score PC1/PC2 reconstruction
  RMSE. Leave this metric undefined when complete training/verification support
  is insufficient. No benchmark PCA/scaler is fitted on verification groups.
- Exploratory PCA families: 11-input core, 22-input extension, complete-case
  references where available, and four tensile properties on complete measured
  rows. Also examine PCA excluding PWHT. Center/scale, full SVD, no whitening;
  squared component coefficients provide per-axis contributions summing to 100%.
  Principal angles/projector distances handle component signs and rotations;
  the matrices have to share the same feature space. No angle is reported for
  PWHT exclusion because the dimensionality changes.
- ECDFs and diagnostics distinguish exact values, approximations and estimates,
  both globally and for the three most frequent processes. Missingness-axis
  correlations and per-series scores help identify provenance structure.
  Microstructure sums and sparse mechanical properties remain separate audits;
  no automatic renormalization or global imputation of outcomes is performed.
- Full-data imputation/PCA fits are descriptive only. Never reuse them in
  predictive evaluation. The input-only sklearn transformer rejects properties
  and identifiers as predictors; refit imputation, scale, selection and PCA
  within training folds. A missing target remains unlabeled, and no
  semi-supervised training is implemented by this preprocessing investigation.
- Local exports live in `data/processed/preprocessing/`, which Git ignores.
  The manifest records raw/code SHA-256 hashes, versions and experiment settings.
  No trained models are persisted. Figures are reproducible notebook outputs.

The initial execution at max_iter=20 did not converge in one core fold or any
extended fit. A targeted check at 100 iterations found convergence in all core
fits (3, 4, 21 iterations across folds; 17 on the full data), but not in the
extended fits. The final notebook uses a 100-iteration cap and explicitly reports
this limitation. Extended iterative results remain a diagnostic sensitivity
scenario, not an adopted imputation method.

Executed results are summarized in [the preprocessing results report](../reports/03_preprocessing_results.md).
Across the recorded masks, macro normalized MAE for core inputs is 1.6966
(median), 1.2541 (process median), and 0.8532 (iterative). For extended inputs it
is 2.2532, 2.0599, and 2.0089 respectively. These dimensionless, scenario-averaged
reconstruction scores are not quality-prediction errors and cannot establish
accuracy on genuinely absent values. On the extension, mean absolute correlation
change is 0.1060, 0.1063, and 0.1589 respectively; the iterative candidate thus
has lower reconstruction error but greater correlation distortion and fails
the convergence check. No final preprocessing winner is adopted.

Validation completed: 17 offline unit tests pass; all 22 code cells execute
without errors or stderr; 15 new figures were generated and representative
figures visually inspected. Raw-data and implementation hashes match the
manifest. Row-level grouped splits and shared-mask hashes were checked, and
all scored estimates satisfy the broad physical bounds. Derived datasets remain
ignored by Git. The notebook's original EDA cells are retained.
