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

### Proposed modeling-ready preprocessing and training plan — 2026-10-08

The user requested a deep review of existing preprocessing results and an
action plan covering special values, duplicate removal and subsequent training.
The analysis and proposed execution order are in
[the preprocessing-to-training plan](../reports/04_preprocessing_training_plan.md).
This section records proposals, not implemented transformations or trained
models. The previous raw files, datasets and exploratory results are unchanged.

- Proposed deduplication: compare all 43 raw non-ID fields, keep the first
  occurrence of each identical record and preserve alternate IDs. There are
  four excess records, at raw zero-based indices 393, 423, 425 and 1434;
  the resulting modeling table would have 1,648 rows. Preserve pre-deduplication
  group links, notably between Evans-V/Mn and Evans-Nb/Mn. Repeated identifiers
  alone are not a deletion rule. Identical reported values do not prove that
  two records are copies of the same physical experiment.
- Proposed special-value policy: numeric representation with provenance rather
  than blanket row deletion. Use L/2 for nonnegative left-censored concentrations
  without unresolved unit flags, and 175 °C for the 150–200 °C interval; retain
  bounds and evaluate sensitivity. Extract nitrogen total/residual tokens and
  hardness number/protocol separately; do not use unresolved nitrogen semantics
  in the primary numeric matrix, map `nd` to neither zero nor an invented limit,
  and do not pool hardness protocols without evidence. Mask unresolved cells,
  preserve valid extremes and observed PWHT zeros. Correct units only with
  source evidence. Removing every special or reviewed row would remove 593
  raw rows and leave 1,059 after the proposed deduplication.
- Proposed tasks: separate regressions for yield strength, UTS and elongation,
  with reduction of area complementary. Their exact label counts would be
  777, 735, 697 and 702 after deduplication. Never impute missing target labels.
  Charpy remains conditional on identifying fixed-energy transition-temperature
  records versus energy-at-temperature records; that audit does not block
  tensile modeling. No global quality score or industrial threshold is adopted.
- Proposed input comparisons: A0 = existing 11-input core; A1 = core plus O/N
  (13 numeric inputs); A2 = A1 plus Ni/Cr/Mo/V/Cu/Ti/Al/Nb (21). Bore is a
  separate sensitivity addition. Include welding process categorically and
  test current type/polarity separately. Exclusions from the initial experiment
  express coverage, ambiguity and prediction-time availability, not demonstrated
  physical irrelevance. For a confirmed Charpy E(T) task, explicitly allow test
  temperature as an exogenous condition only in that task's schema.
- The proposed primary 13-input space has not been benchmarked. After proposed
  deduplication, existing deterministic preparation leaves 1,399 of its 21,424
  cells unavailable (6.53%). The favorable iterative results on the 11-input
  core cannot automatically be transferred to 13 or 21 inputs. Start with
  process-supported/global median candidates; require a new convergence and
  reconstruction audit before adopting an iterative candidate in a new space.
- Export a cleaned, pre-imputation table, cell provenance, stable raw row IDs,
  duplicate aliases, group links, target eligibility and manifests under
  `data/processed/modeling/`. Learned imputation, categorical encoding, scaling,
  selection and optional PCA belong inside training folds. Handle entirely
  unobserved training columns explicitly rather than fabricating their medians.
- Proposed evaluation: five outer group folds and three inner group folds when
  support permits, seed 42 for stochastic estimators, saved assignments and
  common validation rows per target. Compare a constant median baseline, Ridge
  and Random Forest, with SVR optional according to course coverage. Select
  feature sets, imputers and hyperparameters internally. Report MAE/RMSE in
  target units, R² and per-group variability. No predictive results exist yet.
- Proposed semi-supervised candidate: literature-grounded COREG regression,
  evaluated inductively against its supervised counterpart. Keep every reserved
  group's inputs and labels outside fitting and pseudo-labeling, including in
  inner folds. Initially fit preprocessing on the same labeled training rows
  in both methods to isolate the additional effect of permitted unlabeled data.

The proposal is actionable for tensile modeling with unresolved input cells
explicitly unavailable. Source-unit corrections, Charpy task definitions and
final predictive selections remain evidence-dependent.

### Iterative method selected; preparation scope investigated — 2026-10-08

The user fixed iterative imputation as the method and requested a focused
preparation notebook in a later step, with current analysis of feature scope,
unit ambiguities, Charpy protocols and acceptable row exclusions. This supersedes
the earlier proposal to compare imputation families for the new preparation.
The notebook itself and predictive training are not implemented yet.

[The updated design and screening results](../reports/05_data_preparation_notebook_design.md)
record the evidence and proposed execution steps. Local derived audit artifacts
and executable recipes live under `data/processed/preparation_audit_2026-10-08/`
(ignored by Git). The existing source implementations are unchanged.

- On 1,648 records after technical deduplication, grouped iterative fits converge
  on 11, 13 and 16 numeric inputs. The 13-input candidate adds O/N to the core;
  the 16-input candidate additionally includes Ni/Cr/Mo. The 21-input candidate,
  despite removing boron, fails convergence in all three folds at 100 iterations.
  Low coverage is a concern, but individual causal contributions to failure
  have not been established.
- New iterative-only reconstruction screening uses three group folds, mask
  seeds 42/43, rates 10/20/40%, cell and training-derived block masks. Masks
  generated on the 16-input matrix are restricted to each smaller set, ensuring
  identical hidden values for common features. Mean normalized errors on the
  11 common inputs are 0.7651, 0.7924 and 0.8816 for 11/13/16 inputs respectively.
  New splits/masks mean these figures are not directly comparable to the EDA
  benchmark. No predictive model has been evaluated.
- Additional fits on only labeled training rows for YS/UTS/elongation converge
  for all three folds with the 13-input candidate, its at-most-two-unavailable
  variant, and the 16-input candidate (27 fits). Final splits must recheck their
  own convergence rather than relying solely on this three-fold screening.
- Proposed primary preparation candidate: 13 numeric inputs and welding process;
  11 inputs remain a compact control and 16 an enriched comparison. This is a
  proposal of usable feature space, not a validated predictor of all weld quality.
  Initial exclusions reflect coverage, ambiguity and prediction-time scope,
  not empirical proof that an element has no physical effect.
- Export a full cleaned master plus explicit cohort masks. A proposed strict
  13-input cohort allows at most two unavailable cells after deterministic
  preparation: 1,555 rows, 44 groups, 706 YS labels, 677 UTS labels, 631
  elongation labels. It loses entire Cunh-1982, EvHtIp1979 and Natsume-1990
  groups. This threshold is an engineering choice, not guaranteed reliability;
  sensitivity and population changes must be reported. Its reconstruction
  precision has not been benchmarked here, only convergence and coverage.
- Source-unit flags remain unresolved; no conversion is newly adopted. Keep
  raw and per-cell provenance, mask unresolved cells in scenarios that use them,
  and do not drop rows for excluded-variable flags. Preserve observed extremes
  and PWHT zeros. Nitrogen annotations remain lexically extracted but unavailable
  in the primary numeric column pending semantic comparability evidence.
- Deduplicated Charpy data include 355 records at 100 J and 118 at 28 J, spanning
  15 and 6 groups, respectively. These are candidate counts, not confirmed T100J
  or T28J labels. Classify by source/record: E(T) predicts energy with temperature
  as an input; T100J/T28J predict temperature, excluding that temperature and
  the constant energy from predictors. Keep unresolved protocols separate and
  do not infer them from energy equality alone. Tensile tasks can proceed first.
- Proposed notebook `02_data_preparation.ipynb` handles audit, deduplication,
  deterministic numeric representation, feature/task eligibility, source protocol
  review, pre-imputation exports and focused iterative checks. Fold-specific
  learned preprocessing remains part of the modeling pipeline. Fully numeric
  exports for evaluation must identify the target, split and train-only fit;
  inner tuning folds refit imputation rather than reusing outer-fitted matrices.

The user-selected imputation family is adopted. Feature/cohort choices, source
corrections and Charpy task assignments remain proposed or conditional as
explicitly identified above. Raw data and the original assignment are preserved.

### Review of externally AI-prepared files — 2026-10-08

The user requested evaluation and validation of `ai_prepared/`. The detailed
[audit report](../reports/06_ai_prepared_audit.md) distinguishes technical
reproduction from scientific validation. The supplied files were not modified.
The provided joblib was not loaded; the inspected notebook logic was reproduced
independently to compare cleaned and processed CSVs.

- The cleaned CSV (1,534 rows) and train/test CSVs (1,206/328 rows, 48 predictors)
  match the notebook's transformations. Labels are not imputed, and outer-split
  preprocessing is fitted on training rows rather than the test rows.
- The notebook uses median SimpleImputer, contrary to the chosen iterative
  method. No iterative reconstruction or convergence audit is present there.
- All four raw duplicate excess records are retained. Its duplicate assertion
  includes the identifier; therefore it misses equal records under different IDs.
- Its 606 composition/parameter groups are disjoint, but the 39 identifier-derived
  series represented in test also occur in train; all 328 test rows are from
  shared series. One repeated ID, RC81033, is also split. This does not establish
  generalization to new series or validated publication groups.
- The suggested GroupKFold on already processed train features would include
  inner validation data in the preprocessing fit. Actual outer preprocessing
  does not directly fit on test; no CV has yet been run in the supplied folder.
- Source-unit corrections and nitrogen-total comparability are not supported
  by references in the notebook. These assumptions are not newly adopted.
  Temperature Charpy must be task-specific, and fixed-energy Charpy records
  require protocol classification before claiming a common energy target.
- The removal of 105 wholly unlabeled rows is suitable for a supervised cohort
  but should not discard the master pool for future inductive semi-supervision.
  Raw row IDs, per-cell provenance and exclusion/conversion logs are required.

Outcome: technically reproducible baseline preparation, not approved as the
final scientific dataset or evaluation protocol. The audit does not adopt new
unit corrections, category mergers, target definitions or trained-model results.

### Review of corrected externally prepared notebook — 2026-10-08

The follow-up audit covers `ai_prepared/02_data_preparation.ipynb`,
`ai_prepared/weld_prep.py` and `ai_prepared/modeling.zip`. See
[the detailed review](../reports/07_corrected_ai_preparation_audit.md).
All supplied files remain unchanged. The raw/module/CSV hashes in the manifest
are verified; all eight CSVs, including the 75 benchmark result rows, are
independently reproduced. Checks are stored under ignored
`data/processed/ai_prepared_corrected_audit/`.

- This corrected preparation is accepted as a basis for supervised tensile
  benchmarks using the 13-variable candidate plus categorical welding process.
  It does not adopt unresolved unit conversions, annotated nitrogen semantics,
  Charpy protocols or final models.
- All four exact duplicate excess records are excluded from folds/cohort, with
  aliases retained in a 1,652-row master. There are 1,648 deduplicated records,
  47 identifier-derived groups, and 1,555 strict-cohort rows in 44 groups.
  Eligible strict-cohort labels are 706 YS, 677 UTS, 631 elongation and 635
  reduction-area measurements. Charpy's 861 labels are not yet an adopted task.
- Provenance covers 66,080 numeric cells; 322 unit-ambiguous cells and 59 nitrogen
  annotations are unavailable in primary numeric representation, with original
  tokens preserved. No target is imputed or changed.
- External five-fold and internal three-fold group isolation is verified.
  All 15 iterative fits for three tensile tasks converge in 4–7 iterations.
  Learned transformations use training rows only and preserve observed inputs.
- Fixed-parameter benchmarking is reproduced: RF/iterative mean MAE is 66.13 MPa
  (YS), 56.71 MPa (UTS), and 3.55 percentage points (elongation), with mean R²
  0.0765, 0.1899 and 0.1136. Iterative is not uniformly better than median;
  YS/RF slightly favors median and YS/Ridge fold 4 is 14.58 MPa worse under
  iterative imputation. These findings do not isolate the causes of low scores.
- Preserve 105 entirely unlabeled deduplicated records (99 in strict cohort).
  The notebook prepares an inductive pool but does not train a semi-supervised
  method. For each external/inner fit, unlabeled observations must be restricted
  to the corresponding training groups.
- Before integration, fix notebook paths and output location, place reusable
  code under `src/weld_quality/`, and distinguish corrected archive exports from
  the unchanged old processed CSVs/joblib. Nuance claims of uniformly improved
  prediction and of confirmed publication-level generalization.
- A focused synthetic check finds a partial-PWHT edge case: an unmatched observed
  component can yield a pair absent from training. Add an explicit policy/flag
  for no compatible pair. It does not affect the reproduced data, whose missing
  PWHT cases have both components unavailable. Final training must also enforce
  an explicit non-convergence policy; the class currently records but does not
  reject non-converged fits.

The 13-variable reconstruction advantage is not newly demonstrated by this
notebook: its cited reconstruction figures concern the earlier 11-variable
EDA benchmark. Feature-space/cohort comparisons, source-confirmed grouping,
Charpy assignment and tuned final-model evaluation remain to be completed.
