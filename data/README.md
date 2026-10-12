# Data provenance

Dataset source supplied by the assignment:

https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html

Download and extract the original dataset from the project root:

```bash
python scripts/download_data.py
```

The script uses only Python's standard library. It verifies the archive against the following pinned SHA-256 checksum before saving it:

```text
493b2ec7c2e46e93260040194d86ae35fb8579802c048f94f89539d466b7e6ca
```

Archive URL: https://www.phase-trans.msm.cam.ac.uk/map/data/tar/welddb.tar

The original archive contains `welddb.data`, `welddb.info`, and `welddb.tex`. The script preserves these bytes in `raw/` and writes `raw/manifest.json` containing the source URLs, UTC preparation timestamp, archive checksum, and extracted file sizes and checksums. The timestamp describes when the local dataset was prepared; a cached archive may have been downloaded earlier.

- `raw/`: unchanged source files.
- `processed/`: derived files produced by documented preprocessing.

## Format and loading

The verified archive contains 1,652 data rows, each with 44 whitespace-separated columns and no header. The source documentation defines the column order and measurement units. `N` means that a value was not reported; it must be treated as missing rather than zero. Some columns contain categories or weld identifiers.

From a Python session in the project root, load the raw table with:

```python
import pandas as pd

df = pd.read_csv(
    "data/raw/welddb.data",
    sep=r"\s+",
    header=None,
    dtype=str,
    keep_default_na=False,
)
```

The columns initially have integer names from 0 to 43. Keep original tokens for provenance; the notebooks assign the documented names and distinguish `N`, exact numbers, censoring, intervals and annotations. This read does not impute or normalize values.

The linked source page does not state explicit usage terms; do not assume a redistribution license. Keep source attribution in the report.

## Repeated downloads

When the verified archive is cached, the script needs no network access. Existing extracted files are checked against that archive and missing files are restored. If an existing raw file differs, the script stops without replacing it. Move the conflicting file aside and rerun if restoring the source is intended.

If the remote archive changes, checksum validation fails. Review and document any dataset-version change before updating the pinned checksum.

Record the script or notebook and parameters used to produce each processed dataset. Raw files, the archive, the local manifest, and processed datasets are ignored by Git; the downloader and this documentation are committed.

## Active preparation and variable units

Run `notebooks/02_data_preparation.ipynb` after the EDA. Its code is directly in
the notebook; it needs no local package. `raw_row_id` is the original 0-based
row index. Column positions below are 1-based, as in the source documentation.

| Positions | Notebook names | Meaning / source unit |
| --- | --- | --- |
| 1–12 | C, Si, Mn, S, P, Ni, Cr, Mo, V, Cu, Co, W | Chemical composition, wt% |
| 13–21 | O_ppm, Ti_ppm, N_ppm, Al_ppm, B_ppm, Nb_ppm, Sn_ppm, As_ppm, Sb_ppm | Trace composition, ppm by weight; flagged cells remain unit-uncertain |
| 22–23 | current_A, voltage_V | Welding current (A), voltage (V) |
| 24–25 | ac_dc, polarity | Current type and electrode polarity, categorical |
| 26–27 | heat_input_kJmm, interpass_C | Heat input (kJ/mm), interpass temperature (°C) |
| 28 | weld_type | Welding process code |
| 29–30 | pwht_temp_C, pwht_time_h | Post-weld heat-treatment temperature (°C), time (h) |
| 31–34 | yield_strength, uts, elongation, reduction_area | Yield/ultimate strength (MPa), elongation/reduction of area (%) |
| 35–36 | charpy_temp_C, charpy_J | Charpy test temperature (°C), energy (J); protocols unresolved |
| 37–38 | hardness, fatt50 | Hardness kg/mm² with Vickers protocols tracked separately; fatt50 unit unresolved |
| 39–43 | prim_ferrite, ferrite_2nd_phase, acicular_ferrite, martensite, ferrite_carbide | Microstructure fractions (%) |
| 44 | weld_id | Source identifier; not a predictor |

The master uses `weld_type_raw` / `weld_process`, `ac_dc_raw` and `polarity_raw`;
categorical `N` for current/polarity becomes `missing`. Hardness is represented
by `hardness_value` and `hardness_protocol`. Only documented process synonyms
ShMA→MMA and SMA→SA are pooled. Numerical units also appear in the manifest.

### Local exports under `processed/modeling/`

| File | Content |
| --- | --- |
| `master.csv` | 1,652 rows; numeric representation, metadata and eligibility, including four marked duplicate aliases |
| `cell_provenance.csv` | 66,080 numeric cells: raw tokens, statuses, bounds, annotations, unit flags, primary values |
| `duplicate_aliases.csv` | Four duplicate excess rows mapped to their retained records |
| `groups.csv` | Identifier-derived series and conservative group per original row |
| `folds.csv` | Five outer folds and three inner folds per outer train, on 1,648 deduplicated rows |
| `unit_review_cells.csv` | 322 cells unavailable because source units need review |
| `charpy_protocol_candidates.csv` | Group signatures, hypotheses only |
| `imputer_benchmark.csv` | 75 fixed-parameter sensitivity results, not final model selection |
| `manifest.json` | Source hashes, notebook source identity, CSV hashes, versions, units, parameters and counts |

`N` remains missing; `<L` is approximated by L/2 and intervals by their midpoint,
with provenance retained. Reviewed units and annotated nitrogen are NaN in the
primary numeric representation. No conjectural unit conversion is made.

For supervised traction, select `in_strict13` and `has_<target>`: the strict
cohort has 1,555 rows/44 groups, with 706 YS, 677 UTS and 631 elongation labels.
There is no common requirement that all target properties be filled.
Join folds by `raw_row_id` and `group`; keep only the task's declared inputs.
Fit imputation and scaling within each internal/external training partition.
For the grouped inductive protocol, use target-unlabeled rows only from the
training groups. The random-row protocol in notebook 05 has separate row-level
pool access rules described below. Never treat imputed labels as measurements.

The old full-data PCA/imputation outputs under `processed/preprocessing/` and
the supplied artifacts under `ai_prepared/` are historical references, not the
inputs of the active modeling protocol. No generated dataset is committed.

### Supervised experiment exports

`notebooks/03_modeling.ipynb` trains separate target-specific pipelines with
five exported outer group folds and three inner group folds. The first experiment
uses A1_13 plus process for traction; reported Charpy energy additionally uses
the known test temperature. Charpy results are exploratory until source protocols
are verified; the notebook does not infer a protocol from 28/100 J alone.

Generated exports under `processed/experiments/salh_supervised_v1/` include:

| File | Content |
| --- | --- |
| `target_statistics.csv` | Target units, eligibility, group counts and distributions |
| `partition_counts.csv`, `inner_partition_counts.csv` | Labeled train/validation and group counts |
| `preprocessing_checks.csv` | Convergence of the 80 internal/external train preprocessors |
| `inner_search_results.csv` | All configurations, three inner MAEs and selected configurations |
| `outer_metrics.csv` | Per-target/model/fold external metrics, parameters and training diagnostics |
| `outer_predictions.csv` | One held-out prediction per eligible raw ID/model/target |
| `metrics_summary.csv` | Unweighted outer-fold means/std and pooled OOF metrics |
| `charpy_signature_diagnostics.csv` | Exploratory errors by unvalidated series signature |
| `model_comparison.png` | Mean external MAE with fold standard deviations |
| `manifest.json` | Versions, seeds, protocol, input/source hashes and export hashes |

`pipeline_cache/` is a local training cache, ignored together with the other
derived data. It does not replace fold-local fits. No target is imputed and no
global final model is selected using the external metric ranking.

### Performance diagnostics

`notebooks/04_diagnostics.ipynb` writes ignored exports under
`processed/experiments/salh_diagnostics_v1/`: group errors and SSE/SST
components, paired group bootstrap gains, per-row domain diagnostics,
learning curves by training groups, permutation importances, primary-source
Charpy audit and composition matches, and controlled 11/13/16-feature ×
median/iterative sensitivity searches. Outer predictions retain raw IDs,
groups and target-specific eligibility. Inner MAE selects parameters; a
secondary MSE comparison and joint inner-only schema/imputer/family selection
have separate outputs. Failed preprocessing is recorded without fallback.
The source PDFs under `sources/` are derived audit cache, not raw dataset edits.
The experiment manifest records parameters, versions and file hashes.

Additional explanatory controls have separate exports:

| Files | Purpose |
| --- | --- |
| `split_strategy_fixed_rf_*` | Same fixed RF under grouped vs shuffled row validation; group overlap is measured |
| `local_error_cases.csv`, `local_path_contributions.csv` | Largest reference errors and exact additive tree-path accounting; order-dependent, not SHAP |
| `extension16_masked_imputation_*` | Reconstruction of artificially masked observed Ni/Cr/Mo; aggregate methods on common successful contexts |
| `extension16_missingness_gains.csv`, `extension16_group_gains.csv` | Paired 13-to-16 RF gains by missingness and group, with coverage flags |

The sensitivity summary records the number of successful outer folds. Incomplete
scenarios cannot be fairly ranked against complete five-fold evaluations.

### Random KFold and portable model exports

Notebook 05 keeps the strict13 cohort and adds Ni/Cr/Mo as predictors without
filtering additional rows: 16 numeric inputs plus process, median imputation;
Charpy additionally requires known test temperature. Labels remain 706/677/631/861.
Derived files are under `processed/experiments/salh_random_kfold_v1/`:

| Files | Purpose |
| --- | --- |
| `random_fold_assignments.csv` | Target-specific labeled/unlabeled raw IDs, 5 outer and 3 inner assignments |
| `group_structure.csv`, `repeated_conditions.csv`, `confirmed_repeated_charpy_curves.csv` | Group diversity and repeated conditions/verified curves |
| `group_target_association.csv`, `random_group_overlap.csv` | Association diagnostics and actual shared series/conditions under random folds |
| `grouping_fixed_rf_*` | Same fixed RF under row, condition-proxy and series splits |
| `inner_search.csv`, `outer_metrics.csv`, `outer_predictions.csv` | Nested random-CV search, evaluation and complete OOF predictions |
| `inner_selected_*`, `metrics_summary.csv`, `random_vs_grouped16.csv` | Inner-only family choice and comparison with matched grouped 16/median results |
| `full_refit_*`, `selected_final_models.csv`, `model_artifacts.csv` | Full-label refit selection and model inventory |
| `fresh_reload_checks.csv`, `reload_probe_*.csv` | Fresh-process verification of the four selected exports |
| `semi_supervised_access_counts.csv`, `semi_supervised_readiness.csv` | Allowed inductive pools, no pseudo-labels generated yet |
| `manifest.json` | Source, dataset, model and CSV hashes; versions, seeds and grids |

Random folds may share series, but never rows: only target-unlabeled rows assigned
to the current outer/inner training partitions are allowed in the inductive pool.
There are 849/878/924 candidates for the traction tasks and **zero** for Charpy
energy with known test temperature. No temperature is imputed to create a pool.
All supervised transformations are learned solely on labeled training rows.

Pipelines and sidecar metadata are under `models/salh_random_kfold_v1/`, ignored
by Git, separately for outer-train-only exports and full-label refits. See
[the model loader and scope](../models/README.md). Full-label exports cannot be
used for fold evaluation in a subsequent semi-supervised experiment.

### Grouped pipeline persistence

Notebook 06 recreates the grouped 16/median models using their previously
selected inner parameters and verifies all 80 reference evaluations/11,500 OOF
predictions. It adds the baseline and exports the 20 models selected by inner
MAE, then tunes/refits all five families using GroupKFold5 on labeled source
groups. The 40 pipelines are under `models/salh_group_kfold_v1/`, separate from
the 40 random-CV pipelines. Both folders remain ignored by Git.

Scores, predictions, model inventory, selected full refits, fresh-process reload
checks and source/model/CSV hashes are under
`processed/experiments/salh_group_kfold_v1/`. Its
`grouped_semi_supervised_access_counts.csv` verifies that both labeled train
and unlabeled pool groups exclude external/internal validation groups. Full-label
refits must not be used for future fold evaluation. COREG is implemented separately
in notebook 07.

### Inductive COREG experiments

Notebook 07 uses the same three traction targets, strict13 cohort, 16 numeric
inputs plus process, and median preprocessing learned solely on true training
labels. Five outer/three inner random and grouped partitions are reused. Neither
validation X nor labels enter the pool; grouped validation also excludes their
entire source groups. U are target-unlabeled rows only. The transformed pool is
deduplicated and representations already present among true training labels are
removed, with the smallest raw ID as representative.

Ignored exports under `processed/experiments/salh_coreg_v1/` include:

| Files | Purpose |
| --- | --- |
| `target_counts.csv`, `input_missingness.csv`, `split_assignments.csv` | Cohort, units, missingness and exact nested/full-CV access assignments |
| `inner_scores.csv`, `inner_candidate_means.csv` | k3/5/9/15 inner-only selection for COREG and supervised kNN controls |
| `outer_metrics.csv`, `outer_predictions.csv`, `metrics_summary.csv` | Six methods, both CV protocols, same true-label OOF coverage |
| `fit_audit.csv`, `pseudo_labels.csv`, `iteration_history.csv` | Counts, stops, IDs, crossed values/gains and current-source neighborhoods |
| `paired_gains.csv`, `seed_sensitivity*.csv` | Paired MAE changes and base43/44 sensitivity at fixed k |
| `full_cv_scores.csv`, `full_model_selection.csv`, `model_artifacts.csv` | Full-label tuning/refits and pipeline inventory |
| `fresh_reload_checks.csv`, `independent_audit.json` | Independent-process prediction checks and scientific audit counts |
| `manifest.json` | Parent/source hashes, versions, protocol, CSV/model hashes and source identity |

The 108 local pipelines are under `models/salh_coreg_v1/`, separated by protocol
and outer/full-fit role. They include COREG and its two mean-kNN controls;
the prior supervised exports remain available. Charpy has no natural U with
known temperature and receives no semi-supervised fit in this experiment.
See [the measured results and limitations](../reports/14_coreg_training.md).
