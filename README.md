# Welding Quality Prediction

Machine learning project investigating the quality of steel welds. The original assignment is preserved in [sujet.md](sujet.md); implementation decisions belong in [specs/spec.md](specs/spec.md).

## Project structure

```text
.
├── README.md
├── AGENTS.md
├── pyproject.toml
├── sujet.md
├── specs/
│   └── spec.md
├── scripts/
│   └── download_data.py
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_modeling.ipynb
├── src/
│   └── weld_quality/
│       ├── __init__.py
│       ├── download.py
│       ├── preprocessing.py
│       ├── train.py
│       ├── metrics.py
│       └── evaluation.py
├── data/
│   ├── README.md
│   ├── raw/
│   └── processed/
├── models/
├── reports/
│   └── figures/
└── tests/
    ├── README.md
    └── test_download.py
```

## Setup

Use Python 3.10 or newer. From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m ipykernel install --user --name weld-quality --display-name "Welding Quality"
python -m jupyterlab
```

Select the **Welding Quality** kernel for the notebooks. Installing the package lets notebooks import `weld_quality` without modifying `sys.path`.

## Download the data

From the project root, run:

```bash
python scripts/download_data.py
```

This command uses only Python's standard library, so it also works before installing dependencies. It downloads the Cambridge archive, verifies its pinned SHA-256 checksum, and saves these files in `data/raw/`:

- `welddb.tar`: original downloaded archive.
- `welddb.data`: original whitespace-separated dataset.
- `welddb.info` and `welddb.tex`: source documentation.
- `manifest.json`: source URLs, preparation timestamp, and file checksums.

Repeat runs verify the cached archive and extracted files without downloading again. Missing extracted files are restored; modified raw files are reported and preserved. A changed upstream archive is rejected so both students use the same dataset version.

Dataset files and the local manifest are ignored by Git. Commit the script and documentation so each collaborator can reproduce the download. See [data/README.md](data/README.md) for loading details.

## Workflow

For two-person collaboration, see [the task backlog and GitHub workflow](specs/tasks.md).
It includes independent EDA for both teammates, shared protocol design, separate
method experiments, and joint interpretation and writing. Issue and PR templates
are in `.github/`; record actual task time in `specs/time_log.csv` for the report's Gantt.

1. Run `python scripts/download_data.py` to obtain the original data and local provenance manifest.
2. Explore missing values, variable meanings, units, and potential targets in `notebooks/01_eda.ipynb`.
3. Document the prediction task and validation protocol in `specs/spec.md`.
4. Implement reusable preprocessing, training, metrics, and evaluation in `src/weld_quality/`.
5. Compare supervised and semi-supervised approaches in `notebooks/02_modeling.ipynb`.
6. Save figures in `reports/figures/`, trained artifacts in `models/`, and the final report in `reports/`.

Fit learned preprocessing and semi-supervised steps only on the permitted training data within each validation fold. Record random seeds, split definitions, and model parameters with experiment results.

The downloader and preprocessing investigation are implemented. Run
`notebooks/01_eda.ipynb` from top to bottom to reproduce measurement audits,
grouped imputation checks, distribution diagnostics and exploratory PCA.
Reusable code is in `schema.py`, `preprocessing.py`, `exploration.py` and
`plotting.py`. Scientific choices and unresolved unit/annotation questions are
recorded in `specs/spec.md` and `reports/02_preprocessing_plan.md`.

The notebook exports local derived matrices, per-cell provenance, benchmark
metrics, split definitions and a reproducibility manifest to
`data/processed/preprocessing/` (ignored by Git). Figures are saved in
`reports/figures/`. These full-data exploratory matrices are not suitable as
precomputed inputs for predictive cross-validation: fit `WeldInputImputer`,
scaling and PCA inside each training fold. The modeling notebook remains an
outline; no quality target, predictive model or semi-supervised protocol has
been adopted.

## Tests

Add focused tests for meaningful data and evaluation behavior as it is implemented, then run:

```bash
python -m pytest
```

The tests run offline. Download checks cover checksums, cached runs, preservation
of raw files and rejection of unsafe archives. Preprocessing checks cover
measurement provenance, bounds, annotation parsing, input/target separation,
process support by groups, paired PWHT, shared masks and grouped verification.
They also run with the project dependencies and Python's standard test runner:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Generated data, model artifacts, and local environments are excluded from Git.
