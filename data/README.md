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
For inductive semi-supervision, use target-unlabeled rows only from the training
groups. Never treat imputed labels as measurements.

The old full-data PCA/imputation outputs under `processed/preprocessing/` and
the supplied artifacts under `ai_prepared/` are historical references, not the
inputs of the active modeling protocol. No generated dataset is committed.
