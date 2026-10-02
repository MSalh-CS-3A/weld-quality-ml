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
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_modeling.ipynb
├── src/
│   └── weld_quality/
│       ├── __init__.py
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
    └── README.md
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

## Workflow

1. Obtain the dataset linked in `sujet.md`, place the unchanged files in `data/raw/`, and record provenance in `data/README.md`.
2. Explore missing values, variable meanings, units, and potential targets in `notebooks/01_eda.ipynb`.
3. Document the prediction task and validation protocol in `specs/spec.md`.
4. Implement reusable preprocessing, training, metrics, and evaluation in `src/weld_quality/`.
5. Compare supervised and semi-supervised approaches in `notebooks/02_modeling.ipynb`.
6. Save figures in `reports/figures/`, trained artifacts in `models/`, and the final report in `reports/`.

Fit learned preprocessing and semi-supervised steps only on the permitted training data within each validation fold. Record random seeds, split definitions, and model parameters with experiment results.

This repository starts as a scaffold: the notebooks contain outlines and the Python modules contain purpose statements. No data has been downloaded and no models have been trained.

## Tests

Add focused tests for meaningful data and evaluation behavior as it is implemented, then run:

```bash
python -m pytest
```

There are no tests yet. Generated data, model artifacts, and local environments are excluded from Git.
