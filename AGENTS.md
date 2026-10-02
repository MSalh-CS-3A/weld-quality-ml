# Project guidance

- Treat `sujet.md` as the original assignment; preserve its content.
- Keep scientific choices and their justifications in `specs/spec.md`.
- Put reusable code in `src/weld_quality/`; keep notebooks focused on exploration and interpretation.
- Preserve files in `data/raw/`. Write derived datasets to `data/processed/`.
- Document variable units, missing-value encodings, target definitions, and preprocessing decisions.
- Fit imputation, scaling, PCA, feature selection, and other learned transformations within training folds.
- Keep validation labels out of training and semi-supervised pseudo-label generation. Document whether a semi-supervised protocol is inductive or transductive.
- Choose any grouping strategy after inspecting repeated welds or related observations; document the justification.
- Record seeds, split definitions, model parameters, and metrics for reproducible comparisons.
- Do not invent results, assume target definitions, or claim domain recommendations without evidence.
- Add focused tests when implementation warrants them; run checks appropriate to the change.
- Do not commit generated datasets, trained models, credentials, or local environments.
