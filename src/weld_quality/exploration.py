"""Reproducible grouped reconstruction checks and exploratory PCA diagnostics.

All benchmark fits use training groups only. Full-data PCA runs are explicitly
descriptive and must not be used to score a future predictive model.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
import sklearn
from sklearn.decomposition import PCA
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from .preprocessing import WeldInputImputer, prepare_matrix, normalized_process
from .schema import CORE_INPUTS, EXTENDED_INPUTS, INPUT_COLUMNS, MICROSTRUCTURE, UNITS, physical_bounds

METHODS = ["median", "process_median", "iterative"]


def availability_table(audit, groups):
    """Measured coverage, original status and group support before any filling."""
    counts = pd.DataFrame({s: audit.status.eq(s).sum() for s in [
        "numeric", "censored", "interval", "annotation / other", "missing"
    ]})
    counts.insert(0, "unit", pd.Series(UNITS))
    counts.insert(0, "role", [
        "input" if c in INPUT_COLUMNS else "microstructure" if c in MICROSTRUCTURE
        else "test_condition" if c == "charpy_temperature" else "candidate_property"
        for c in counts.index
    ])
    counts["review_cells"] = audit.review.sum()
    counts["reported_pct"] = 100 * (1 - counts["missing"] / len(audit.raw))
    counts["reported_groups"] = [
        groups.loc[~audit.status[c].eq("missing")].nunique() for c in counts.index
    ]
    counts["exact_usable_groups"] = [
        groups.loc[audit.status[c].eq("numeric") & ~audit.review[c]].nunique()
        for c in counts.index
    ]
    return counts


def observed_pair_counts(values):
    observed = values.notna().astype(int)
    return observed.T @ observed


def training_scale(values):
    """IQR, with training standard deviation fallback; undefined if constant."""
    iqr = values.quantile(0.75) - values.quantile(0.25)
    return iqr.where(iqr > 0, values.std()).where(lambda s: s > 0)


def artificial_mask(eligible, training_unavailable, rate, rng, pattern):
    """Random cells or empirical joint patterns, drawn from training only.

    Block draws sample nonempty original/unusable training patterns. A mixture
    of resampled patterns and independent cells reaches the requested expected
    per-cell rate. PWHT is always masked jointly for the paired estimator.
    """
    if not 0 < rate < 1:
        raise ValueError("Mask rate must be between zero and one.")
    if pattern == "cells":
        proposed = rng.random(eligible.shape) < rate
    elif pattern == "blocks":
        patterns = training_unavailable.to_numpy(dtype=bool)
        patterns = patterns[patterns.any(axis=1)]
        if len(patterns) == 0:
            raise ValueError("No empirical training block patterns.")
        sampled = patterns[rng.integers(len(patterns), size=len(eligible))]
        prevalence = patterns.mean()
        activation = min(1.0, rate / prevalence)
        proposed = sampled & (rng.random(len(eligible))[:, None] < activation)
        current_rate = prevalence * activation
        extra = max(0.0, (rate - current_rate) / (1 - current_rate))
        proposed |= rng.random(eligible.shape) < extra
    else:
        raise ValueError("Unknown mask pattern.")
    mask = pd.DataFrame(proposed, index=eligible.index, columns=eligible.columns) & eligible
    pair = ["pwht_temperature", "pwht_time"]
    if set(pair).issubset(mask):
        both_eligible = eligible[pair].all(axis=1)
        # Same draw for the pair, without doubling the requested probability.
        joint = mask[pair[0]] & both_eligible
        mask.loc[:, pair[0]] = joint
        mask.loc[:, pair[1]] = joint
    return mask


@dataclass
class BenchmarkResult:
    metrics: pd.DataFrame
    splits: pd.DataFrame
    fits: pd.DataFrame
    relations: pd.DataFrame
    config: dict


def benchmark_imputation(values, exact_eligible, process, groups, *, n_splits=3,
                         seeds=(42, 43), rates=(0.1, 0.2, 0.4),
                         patterns=("cells", "blocks"), max_iter=100, progress=None):
    """Hold out series, hide exact test cells, fit only unmasked training groups.

    Scores exclude censored/interval substitutes, ambiguous units and annotation
    extraction. Reports include per-process and per-series metrics and support.
    """
    for item in [exact_eligible, process, groups]:
        if not values.index.equals(item.index):
            raise ValueError("Benchmark row indices must align.")
    if list(exact_eligible) != list(values):
        raise ValueError("Eligibility columns must match the numeric matrix.")
    eligible = exact_eligible & values.notna()
    scores, assignments, fit_records, relations = [], [], [], []
    splitter = GroupKFold(n_splits=n_splits)
    for fold, (train_pos, test_pos) in enumerate(splitter.split(values, groups=groups)):
        train, test = values.iloc[train_pos], values.iloc[test_pos]
        if set(groups.iloc[train_pos]) & set(groups.iloc[test_pos]):
            raise AssertionError("Train and verification groups overlap.")
        for role, positions in [("train", train_pos), ("test", test_pos)]:
            assignments.extend({"fold": fold, "row": values.index[i],
                                "group": groups.iloc[i], "role": role} for i in positions)
        scale = training_scale(train)
        truth_observed = test.where(eligible.iloc[test_pos])
        truth_corr = truth_observed.corr()
        pair_counts = observed_pair_counts(truth_observed)
        pair_support = np.triu(pair_counts.to_numpy() >= 20, k=1)
        complete_truth = truth_observed.dropna()
        # A diagnostic PCA is fitted only on complete EXACT training inputs.
        # Held-out exact values are transformed solely to score reconstruction.
        train_exact = train.where(eligible.iloc[train_pos]).dropna()
        training_pca = None
        if len(train_exact) > len(values.columns) and train_exact.std().gt(0).all():
            training_pca = fit_exploratory_pca(train_exact)
        train_X = train.assign(weld_type=process.iloc[train_pos])
        models = {}
        for method in METHODS:
            model = WeldInputImputer(method=method, random_state=seeds[0], max_iter=max_iter)
            try:
                model.fit(train_X, groups=groups.iloc[train_pos])
                models[method] = model
                state, error = "ok", ""
            except ValueError as exc:
                state, error = "unsupported", str(exc)
            fit_records.append({"fold": fold, "method": method, "state": state,
                                "error": error, "converged": getattr(model, "converged_", False),
                                "iterations": getattr(model, "n_iter_", 0)})
        for seed in seeds:
            for rate_index, rate in enumerate(rates):
                for pattern_index, pattern in enumerate(patterns):
                    rng = np.random.default_rng(np.random.SeedSequence(
                        [seed, fold, rate_index, pattern_index]
                    ))
                    mask = artificial_mask(eligible.iloc[test_pos], train.isna(), rate, rng, pattern)
                    mask_hash = hashlib.sha256(mask.to_numpy().tobytes()).hexdigest()
                    hidden = test.mask(mask)
                    query = hidden.assign(weld_type=process.iloc[test_pos])
                    for method, model in models.items():
                        reconstructed = model.transform(query)
                        retained = test.notna() & ~mask
                        if not reconstructed.where(retained).equals(test.where(retained)):
                            raise AssertionError("A nonhidden measured value changed.")
                        after_corr = reconstructed.where(eligible.iloc[test_pos]).corr()
                        deltas = np.abs(after_corr.to_numpy() - truth_corr.to_numpy())[pair_support]
                        finite = deltas[np.isfinite(deltas)]
                        relation = {"fold": fold, "seed": seed, "rate": rate,
                                    "pattern": pattern, "method": method, "mask_sha256": mask_hash,
                                    "n_supported_pairs": len(finite),
                                    "mean_abs_correlation_delta": finite.mean() if len(finite) else np.nan,
                                    "max_abs_correlation_delta": finite.max() if len(finite) else np.nan,
                                    "n_complete_reference": len(complete_truth),
                                    "n_complete_training": len(train_exact),
                                    "pca_score_rmse": np.nan}
                        if training_pca is not None and len(complete_truth):
                            true_scores = training_pca.pca.transform(training_pca.scaler.transform(complete_truth))[:, :2]
                            estimated_scores = training_pca.pca.transform(training_pca.scaler.transform(
                                reconstructed.loc[complete_truth.index]))[:, :2]
                            relation["pca_score_rmse"] = float(np.sqrt(np.mean((true_scores - estimated_scores) ** 2)))
                        relations.append(relation)
                        for col in values:
                            idx = mask.index[mask[col]]
                            if len(idx) == 0:
                                continue
                            error = reconstructed.loc[idx, col] - test.loc[idx, col]
                            strata = [("all", "all", idx)]
                            for scope, labels in [("process", process), ("series", groups)]:
                                for label, members in labels.loc[idx].groupby(labels.loc[idx]):
                                    strata.append((scope, str(label), members.index))
                            for scope, label, members in strata:
                                e = error.loc[members].to_numpy()
                                truth = test.loc[members, col].to_numpy()
                                prediction = reconstructed.loc[members, col].to_numpy()
                                lo, hi = physical_bounds(col)
                                scores.append({
                                    "fold": fold, "seed": seed, "rate": rate, "pattern": pattern,
                                    "mask_sha256": mask_hash,
                                    "method": method, "variable": col, "scope": scope, "stratum": label,
                                    "n": len(e), "mae": np.abs(e).mean(), "rmse": np.sqrt(np.mean(e ** 2)),
                                    "normalized_mae": np.abs(e).mean() / scale[col]
                                    if pd.notna(scale[col]) else np.nan,
                                    "normalizing_scale": scale[col], "train_observed": int(train[col].count()),
                                    "train_groups": groups.iloc[train_pos][train[col].notna()].nunique(),
                                    "realized_mask_rate": mask[col].sum() / max(1, eligible.iloc[test_pos][col].sum()),
                                    "bias": e.mean(), "truth_std": truth.std(), "prediction_std": prediction.std(),
                                    "outside_bounds": int(((prediction < lo) | (prediction > hi)).sum()),
                                })
        if progress:
            progress(f"Fold {fold + 1}/{n_splits} completed ({len(train)} train, {len(test)} verification).")
    config = {"n_splits": n_splits, "seeds": list(seeds), "rates": list(rates),
              "patterns": list(patterns), "max_iter": max_iter,
              "min_groups_process_median": 3, "iterative_tol": 1e-3,
              "iterative_estimator": "BayesianRidge (sklearn default)",
              "mask_truth": "exact values without unresolved review",
              "pwht_mask": "joint, using temperature draw only; requires both exact",
              "relation_min_pairs": 20,
              "pca_diagnostic_fit": "complete exact training inputs only",
              "grouping": "identifier-derived series", "columns": list(values)}
    return BenchmarkResult(pd.DataFrame(scores), pd.DataFrame(assignments),
                           pd.DataFrame(fit_records), pd.DataFrame(relations), config)


def benchmark_summary(metrics):
    """Macro feature/fold/seed normalized MAE; no majority-feature weighting."""
    all_scores = metrics.loc[metrics.scope.eq("all")]
    return all_scores.groupby(["method", "pattern", "rate"]).agg(
        normalized_mae=("normalized_mae", "mean"),
        normalized_mae_std=("normalized_mae", "std"),
        n_masked=("n", "sum"), evaluated_rows=("n", "size"),
    )


@dataclass
class PCAResult:
    scaler: StandardScaler
    pca: PCA
    scores: pd.DataFrame
    directions: pd.DataFrame
    contributions: pd.DataFrame
    explained: pd.DataFrame


def fit_exploratory_pca(values):
    """Center/scale complete numeric values; no whitening, no target inference."""
    if values.empty or values.isna().any().any() or not np.isfinite(values.to_numpy()).all():
        raise ValueError("PCA requires a nonempty complete finite matrix.")
    if len(values) < 2:
        raise ValueError("PCA requires at least two observations.")
    constant = values.columns[values.std().eq(0)].tolist()
    if constant:
        raise ValueError(f"Constant PCA variables need explicit exclusion: {constant}.")
    scaler = StandardScaler().fit(values)
    pca = PCA(svd_solver="full").fit(scaler.transform(values))
    pcs = [f"PC{i + 1}" for i in range(pca.n_components_)]
    directions = pd.DataFrame(pca.components_.T, index=values.columns, columns=pcs)
    explained = pd.DataFrame({"variance_ratio": pca.explained_variance_ratio_,
                              "cumulative_ratio": pca.explained_variance_ratio_.cumsum()}, index=pcs)
    return PCAResult(scaler, pca,
                     pd.DataFrame(pca.transform(scaler.transform(values)), index=values.index, columns=pcs),
                     directions, directions.pow(2).mul(100), explained)


def compare_pca(reference, other, n_components=2):
    """Principal angles and projector distance handle sign changes and rotations."""
    if not reference.directions.index.equals(other.directions.index):
        raise ValueError("PCA stability requires the same feature space.")
    k = min(n_components, reference.pca.n_components_, other.pca.n_components_)
    a, b = reference.pca.components_[:k], other.pca.components_[:k]
    angles = np.degrees(np.arccos(np.clip(np.linalg.svd(a @ b.T, compute_uv=False), 0, 1)))
    aligned = other.directions.iloc[:, :k].copy()
    for i in range(k):
        if np.dot(a[i], b[i]) < 0:
            aligned.iloc[:, i] *= -1
    return {"max_angle_degrees": float(angles.max()),
            "projector_distance": float(np.linalg.norm(a.T @ a - b.T @ b)),
            "first_two_variance": float(other.pca.explained_variance_ratio_[:k].sum()),
            "aligned_direction_delta": float(np.abs(reference.directions.iloc[:, :k] - aligned).to_numpy().max())}


def fill_exploratory(values, process, groups, method="median", max_iter=100):
    """Descriptive full-data fitting; returned estimator is not an evaluation fit."""
    X = values.assign(weld_type=process)
    model = WeldInputImputer(method=method, random_state=42, max_iter=max_iter)
    model.fit(X, groups=groups)
    return model.transform(X), model


def reconstruction_diagnostics(before, filled, exact_observed):
    """Summaries keep measured values, approximations and estimates separate."""
    rows = []
    for col in before:
        measured = before.loc[exact_observed[col], col].dropna()
        estimates = filled.loc[before[col].isna(), col]
        lo, hi = physical_bounds(col)
        rows.append({
            "variable": col, "unit": UNITS[col], "n_exact": len(measured),
            "n_approximated": int((before[col].notna() & ~exact_observed[col]).sum()),
            "n_estimated": len(estimates), "estimated_pct": 100 * len(estimates) / len(before),
            "exact_median": measured.median(), "estimated_median": estimates.median(),
            "exact_std": measured.std(), "estimated_std": estimates.std(),
            "estimated_at_global_median_pct": 100 * estimates.eq(before[col].median()).mean(),
            "estimated_outside_bounds": int((~estimates.between(lo, hi)).sum()),
        })
    return pd.DataFrame(rows).set_index("variable")


def pca_sensitivity(audit, process, groups, *, max_iter=100):
    """Methods, censor/interval bounds, PWHT exclusion, complete-case selection.

    Core and extended axes are compared only within each shared feature space.
    """
    matrices, pcas, rows, diagnostics = {}, {}, [], {}
    scenarios = [(m, "half", "midpoint") for m in METHODS] + [
        ("median", "zero", "midpoint"), ("median", "sqrt2", "midpoint"),
        ("median", "half", "lower"), ("median", "half", "upper"),
    ]
    for family, columns in [("core", CORE_INPUTS), ("extended", EXTENDED_INPUTS)]:
        for method, censor, interval in scenarios:
            name = f"{family}_{method}_{censor}_{interval}"
            before, provenance = prepare_matrix(audit, columns, censor=censor, interval=interval)
            filled, model = fill_exploratory(before, process, groups, method, max_iter)
            matrices[name] = filled
            pcas[name] = fit_exploratory_pca(filled)
            measured = provenance.eq("numeric")
            diagnostics[name] = reconstruction_diagnostics(before, filled, measured)
            reference = pcas[f"{family}_median_half_midpoint"]
            row = {"family": family, "scenario": name, "n_rows": len(filled),
                   "converged": model.converged_, "iterations": model.n_iter_,
                   **compare_pca(reference, pcas[name])}
            rows.append(row)
        exact = audit.exact[columns].mask(audit.review[columns]).dropna()
        if len(exact) >= 2:
            name = f"{family}_complete_exact"
            pcas[name] = fit_exploratory_pca(exact)
            rows.append({"family": family, "scenario": name, "n_rows": len(exact),
                         "converged": True, "iterations": 0,
                         **compare_pca(reference, pcas[name])})
        without_pwht = [c for c in columns if not c.startswith("pwht_")]
        name = f"{family}_without_pwht"
        pcas[name] = fit_exploratory_pca(matrices[f"{family}_median_half_midpoint"][without_pwht])
        rows.append({"family": family, "scenario": name, "n_rows": len(audit.raw),
                     "converged": True, "iterations": 0,
                     "max_angle_degrees": np.nan, "projector_distance": np.nan,
                     "aligned_direction_delta": np.nan,
                     "first_two_variance": pcas[name].explained.variance_ratio.iloc[:2].sum()})
    return matrices, pcas, pd.DataFrame(rows), diagnostics


def export_analysis(directory, audit, group_table, benchmarks, matrices, pcas,
                    sensitivity, diagnostics, raw_path):
    """Write local derived data and reproducibility manifest, never models/raw."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    group_table.to_csv(directory / "groups.csv", index_label="row")
    for name, table in [("exact", audit.exact), ("status", audit.status),
                        ("lower", audit.lower), ("upper", audit.upper),
                        ("review", audit.review), ("operators", audit.operator)]:
        table.to_csv(directory / f"audit_{name}.csv", index_label="row")
    audit.issues.to_csv(directory / "unresolved_issues.csv", index=False)
    audit.annotations.to_csv(directory / "annotation_tokens.csv", index=False)
    for name, result in benchmarks.items():
        result.metrics.to_csv(directory / f"benchmark_{name}.csv", index=False)
        result.splits.to_csv(directory / f"splits_{name}.csv", index=False)
        result.fits.to_csv(directory / f"fits_{name}.csv", index=False)
        result.relations.to_csv(directory / f"relations_{name}.csv", index=False)
    for name, matrix in matrices.items():
        matrix.to_csv(directory / f"matrix_{name}.csv", index_label="row")
        columns = list(matrix)
        censor = "sqrt2" if "_sqrt2_" in name else "zero" if "_zero_" in name else "half"
        interval = "lower" if name.endswith("_lower") else "upper" if name.endswith("_upper") else "midpoint"
        before, provenance = prepare_matrix(audit, columns, censor=censor, interval=interval)
        provenance = provenance.where(before.notna(), "estimated_from_" + provenance)
        provenance.to_csv(directory / f"provenance_{name}.csv", index_label="row")
        diagnostics[name].to_csv(directory / f"diagnostics_{name}.csv")
    for name, pca in pcas.items():
        pca.scores.to_csv(directory / f"scores_{name}.csv", index_label="row")
        pca.contributions.to_csv(directory / f"contributions_{name}.csv")
        pca.explained.to_csv(directory / f"variance_{name}.csv")
    sensitivity.to_csv(directory / "pca_sensitivity.csv", index=False)
    manifest = {
        "raw_sha256": hashlib.sha256(Path(raw_path).read_bytes()).hexdigest(),
        "python": platform.python_version(), "pandas": pd.__version__,
        "numpy": np.__version__, "sklearn": sklearn.__version__,
        "units": UNITS, "benchmark_config": {k: v.config for k, v in benchmarks.items()},
        "pca": {"scope": "descriptive full dataset; not predictive evaluation", "scaling": "StandardScaler",
                "solver": "full", "whiten": False, "reference": "median_half_midpoint"},
        "unresolved_policy": "No automatic unit correction; mask reviewed cells; preserve original status",
        "estimated_provenance": "Each matrix has a per-cell provenance table; original status is separate",
        "source_sha256": {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ["schema.py", "preprocessing.py", "exploration.py"]
        },
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest
