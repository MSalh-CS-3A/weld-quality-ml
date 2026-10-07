"""Measurement provenance and fold-fitted, input-only welding imputers."""

from dataclasses import dataclass
from pathlib import Path
import re
import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.exceptions import ConvergenceWarning
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted

from .schema import COLUMNS, UNITS, NUMBER, MISSING_TOKENS, INPUT_COLUMNS, physical_bounds


@dataclass
class MeasurementAudit:
    raw: pd.DataFrame
    exact: pd.DataFrame
    status: pd.DataFrame
    lower: pd.DataFrame
    upper: pd.DataFrame
    operator: pd.DataFrame
    review: pd.DataFrame
    annotations: pd.DataFrame
    issues: pd.DataFrame


def load_raw(path: str | Path) -> pd.DataFrame:
    """Load tokens as strings, preserving measured zero and annotations."""
    raw = pd.read_csv(path, sep=r"\s+", header=None, dtype="string", keep_default_na=False)
    if raw.shape[1] != len(COLUMNS):
        raise ValueError(f"Expected {len(COLUMNS)} columns, found {raw.shape[1]}.")
    raw.columns = COLUMNS
    return raw


def audit_measurements(raw: pd.DataFrame) -> MeasurementAudit:
    """Classify complete tokens without interpreting ambiguous annotations."""
    numeric_cols = [c for c in UNITS if c in raw]
    exact = pd.DataFrame(np.nan, index=raw.index, columns=numeric_cols)
    lower, upper = exact.copy(), exact.copy()
    status = pd.DataFrame("annotation / other", index=raw.index, columns=numeric_cols)
    operator = pd.DataFrame("", index=raw.index, columns=numeric_cols)
    review = pd.DataFrame(False, index=raw.index, columns=numeric_cols)
    issues, annotations = [], []

    def flag(col, mask, reason):
        review.loc[mask, col] = True
        for idx in raw.index[mask]:
            issues.append({"row": idx, "weld_id": raw.at[idx, "weld_id"]
                           if "weld_id" in raw else "", "variable": col,
                           "raw_value": raw.at[idx, col], "reason": reason})

    for col in numeric_cols:
        text = raw[col].astype("string").str.strip()
        missing = text.isna() | text.isin(MISSING_TOKENS)
        numeric = text.str.fullmatch(NUMBER, na=False)
        censor = text.str.extract(rf"^([<>]=?)\s*({NUMBER})$")
        interval = text.str.extract(rf"^({NUMBER})\s*[-–]\s*({NUMBER})$")
        status.loc[missing, col] = "missing"
        status.loc[numeric, col] = "numeric"
        exact[col] = pd.to_numeric(text.where(numeric), errors="coerce").astype(float)
        lower.loc[numeric, col] = exact.loc[numeric, col]
        upper.loc[numeric, col] = exact.loc[numeric, col]
        censored = censor[0].notna()
        status.loc[censored, col] = "censored"
        operator.loc[censored, col] = censor.loc[censored, 0]
        limits = pd.to_numeric(censor[1], errors="coerce")
        below = censor[0].str.startswith("<", na=False)
        above = censor[0].str.startswith(">", na=False)
        lower.loc[below, col] = physical_bounds(col)[0]
        upper.loc[below, col] = limits[below]
        lower.loc[above, col] = limits[above]
        upper.loc[above, col] = physical_bounds(col)[1]
        ranged = interval[0].notna()
        status.loc[ranged, col] = "interval"
        lower.loc[ranged, col] = pd.to_numeric(interval.loc[ranged, 0])
        upper.loc[ranged, col] = pd.to_numeric(interval.loc[ranged, 1])
        lo, hi = physical_bounds(col)
        flag(col, numeric & (~np.isfinite(exact[col]) | ~exact[col].between(lo, hi)),
             "outside_broad_physical_bounds")
        flag(col, ranged & lower[col].gt(upper[col]), "reversed_interval")
        flag(col, ranged & (~lower[col].between(lo, hi) | ~upper[col].between(lo, hi)),
             "interval_outside_broad_physical_bounds")
        flag(col, censored & lower[col].gt(upper[col]), "inconsistent_censor_bound")
        if col in ["aluminium", "titanium", "tin", "arsenic", "antimony"]:
            flag(col, numeric & exact[col].gt(0) & exact[col].lt(1), "unit_review_below_1_ppm")
        if col in ["aluminium", "titanium"]:
            flag(col, text.eq("<0.01").fillna(False), "unit_review_limit_0.01_ppm")
        if col == "vanadium":
            flag(col, text.eq("<5").fillna(False), "unit_review_limit_5_wt_percent")
        for idx in raw.index[status[col].eq("annotation / other")]:
            token = str(text.at[idx])
            record = {"row": idx, "variable": col, "raw_value": token,
                      "weld_id": raw.at[idx, "weld_id"] if "weld_id" in raw else ""}
            if col == "hardness":
                match = re.fullmatch(rf"({NUMBER})\(?Hv(5|10|30)\)?", token)
                if match:
                    record.update(extracted_number=float(match[1]), protocol=f"Hv{match[2]}")
            if col == "nitrogen":
                match = re.fullmatch(rf"({NUMBER})tot({NUMBER}|nd)res", token)
                if match:
                    record.update(tot_token=match[1], res_token=match[2])
            annotations.append(record)
    return MeasurementAudit(
        raw.copy(deep=True), exact, status, lower, upper, operator, review,
        pd.DataFrame(annotations),
        pd.DataFrame(issues, columns=["row", "weld_id", "variable", "raw_value", "reason"]),
    )


def prepare_matrix(audit, columns, *, censor="half", interval="midpoint"):
    """Deterministic scenario, with original status and estimated provenance.

    Reviewed cells stay unavailable. Annotation numbers are not used until
    semantics are confirmed. No conversion of suspect units is performed.
    """
    fractions = {"zero": 0.0, "half": 0.5, "sqrt2": 1 / np.sqrt(2)}
    positions = {"lower": 0.0, "midpoint": 0.5, "upper": 1.0}
    if censor not in fractions or interval not in positions:
        raise ValueError("Unknown censor or interval scenario.")
    columns = list(columns)
    values = audit.exact[columns].copy()
    provenance = audit.status[columns].copy()
    for col in columns:
        below = audit.operator[col].str.startswith("<") & ~audit.review[col]
        if physical_bounds(col)[0] == 0:
            values.loc[below, col] = audit.upper.loc[below, col] * fractions[censor]
            provenance.loc[below, col] = "censor_approximation"
        ranged = audit.status[col].eq("interval") & ~audit.review[col]
        values.loc[ranged, col] = (
            audit.lower.loc[ranged, col] * (1 - positions[interval])
            + audit.upper.loc[ranged, col] * positions[interval]
        )
        provenance.loc[ranged, col] = "interval_approximation"
        values.loc[audit.review[col], col] = np.nan
        provenance.loc[audit.review[col], col] = "unresolved_review"
    return values, provenance


def normalized_process(raw):
    """Only documented synonyms; undocumented modalities stay unchanged."""
    return raw["weld_type"].astype("string").fillna("unknown").replace(
        {"ShMA": "MMA", "SMA": "SA"}
    )


def identifier_groups(raw):
    """Identifier-derived conservative series, not verified publication IDs.

    Prefix/year combines variants, temperatures and treatments. Specific letter,
    report and undated families have explicit rules; unknown IDs use exact IDs.
    """
    def key(token):
        if pd.isna(token) or token in MISSING_TOKENS:
            raise ValueError("Missing weld identifier: grouping requires a decision.")
        token = str(token)
        if token.startswith("EvansLetter"):
            return "EvansLetter", "letter_family"
        if re.fullmatch(r"p\d+-RR82011", token):
            return "RR82011", "report_family"
        for prefix in ["EPRI-TR-101394s", "Mart-", "Ditt-", "Birmingham-", "Kik-"]:
            if token.startswith(prefix):
                return prefix.rstrip("-"), "explicit_undated_family"
        match = re.match(r"^(.+?-(?:19|20)\d{2}(?:/\d{4})?)", token)
        if match:
            return match[1], "prefix_and_year"
        if token.startswith("EvHtIp1979-"):
            return "EvHtIp1979", "explicit_year_family"
        return token, "exact_id_fallback"

    table = pd.DataFrame([key(s) for s in raw["weld_id"]], index=raw.index,
                         columns=["group", "group_rule"])
    table.insert(0, "weld_id", raw["weld_id"])
    table["identifier_group"] = table["group"]
    if set(COLUMNS).issubset(raw.columns):
        # Identical complete raw records (excluding ID) connect two apparent
        # series. A deterministic duplicate audit is done before any split.
        parents = {g: g for g in table.group.unique()}

        def root(g):
            while parents[g] != g:
                g = parents[g]
            return g

        records = raw[COLUMNS[:-1]].fillna("<UNREPORTED>")
        duplicates = records.duplicated(keep=False)
        for _, rows in records.loc[duplicates].groupby(list(records.columns), dropna=False):
            keys = sorted(set(table.loc[rows.index, "group"]))
            for g in keys[1:]:
                a, b = sorted([root(keys[0]), root(g)])
                parents[b] = a
        members = {}
        for g in parents:
            members.setdefault(root(g), []).append(g)
        merged = {g: " + ".join(sorted(members[root(g)])) for g in parents}
        table["group"] = table.group.map(merged)
        linked = table.group.ne(table.identifier_group)
        table.loc[linked, "group_rule"] = table.loc[linked, "group_rule"] + "+exact_duplicate_link"
    return table


class WeldInputImputer(TransformerMixin, BaseEstimator):
    """Input-only sklearn transformer; fit inside training folds.

    X contains numeric inputs and weld_type. Empty training columns raise.
    Physical bounds constrain estimates; measured values are never modified.
    """
    def __init__(self, method="median", min_groups=3, random_state=42, max_iter=100):
        self.method = method
        self.min_groups = min_groups
        self.random_state = random_state
        self.max_iter = max_iter

    def _inputs(self, X):
        if not isinstance(X, pd.DataFrame) or "weld_type" not in X:
            raise ValueError("X must be a DataFrame containing weld_type.")
        columns = [c for c in X if c != "weld_type"]
        if not columns or set(columns) - set(INPUT_COLUMNS):
            raise ValueError("Only documented numeric inputs may enter the imputer; no targets.")
        if hasattr(self, "columns_") and columns != self.columns_:
            raise ValueError("Input columns/order differ from training.")
        values = X[columns].astype(float)
        if np.isinf(values.to_numpy()).any():
            raise ValueError("Infinite input values are not admissible.")
        return values, X["weld_type"].astype("string").fillna("unknown")

    def fit(self, X, y=None, *, groups=None):
        if self.method not in ["median", "process_median", "iterative"]:
            raise ValueError("Unknown imputation method.")
        values, process = self._inputs(X)
        empty = values.columns[values.notna().sum().eq(0)].tolist()
        if empty:
            raise ValueError(f"No observed training values for {empty}.")
        if self.method == "process_median" and groups is None:
            raise ValueError("Process medians require training groups to measure support.")
        self.columns_ = list(values)
        self.feature_names_in_ = np.array(list(X), dtype=object)
        self.n_features_in_ = X.shape[1]
        self.medians_ = values.median()
        self.process_medians_ = values.groupby(process).median()
        if groups is not None:
            group_s = pd.Series(np.asarray(groups), index=X.index)
            if group_s.isna().any():
                raise ValueError("Missing training group.")
            for col in values:
                observed = values[col].notna()
                support = group_s[observed].groupby(process[observed]).nunique()
                unsupported = self.process_medians_.index[
                    support.reindex(self.process_medians_.index, fill_value=0) < self.min_groups
                ]
                self.process_medians_.loc[unsupported, col] = np.nan
        self.converged_ = True
        self.n_iter_ = 0
        if self.method == "iterative":
            self.scale_ = StandardScaler().fit(values)
            self.encoder_ = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            categories = self.encoder_.fit_transform(process.to_numpy().reshape(-1, 1))
            bounds = np.array([physical_bounds(c) for c in self.columns_])
            lower = (bounds[:, 0] - self.scale_.mean_) / self.scale_.scale_
            upper = (bounds[:, 1] - self.scale_.mean_) / self.scale_.scale_
            self.iterative_ = IterativeImputer(
                initial_strategy="median", max_iter=self.max_iter, tol=1e-3,
                random_state=self.random_state, skip_complete=False,
                min_value=np.r_[lower, np.zeros(categories.shape[1])],
                max_value=np.r_[upper, np.ones(categories.shape[1])],
            )
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                self.iterative_.fit(np.c_[self.scale_.transform(values), categories])
            self.converged_ = not any(issubclass(w.category, ConvergenceWarning) for w in caught)
            self.n_iter_ = self.iterative_.n_iter_
        self.pwht_columns_ = ["pwht_temperature", "pwht_time"]
        self.pwht_pairs_ = None
        if set(self.pwht_columns_).issubset(values.columns):
            self.pwht_pairs_ = values[self.pwht_columns_].dropna().drop_duplicates().to_numpy()
            self.pwht_scale_ = values[self.pwht_columns_].std().fillna(1).replace(0, 1).to_numpy()
            if len(self.pwht_pairs_) == 0:
                raise ValueError("No joint training PWHT pair; pair imputation is unsupported.")
        return self

    def transform(self, X):
        check_is_fitted(self, "medians_")
        values, process = self._inputs(X)
        if self.method == "iterative":
            categories = self.encoder_.transform(process.to_numpy().reshape(-1, 1))
            scaled = self.iterative_.transform(np.c_[self.scale_.transform(values), categories])
            filled = pd.DataFrame(
                self.scale_.inverse_transform(scaled[:, :len(self.columns_)]),
                index=values.index, columns=self.columns_,
            )
        elif self.method == "process_median":
            local = self.process_medians_.reindex(process.to_numpy()).set_axis(values.index)
            filled = values.fillna(local).fillna(self.medians_)
        else:
            filled = values.fillna(self.medians_)
        for col in values:
            lo, hi = physical_bounds(col)
            filled[col] = filled[col].clip(lo, hi)
        # Project missing PWHT pairs onto actual joint training observations.
        # This preserves the empirical zero/nonzero pairing without interpreting it.
        if self.pwht_pairs_ is not None:
            pair_missing = values[self.pwht_columns_].isna()
            both_missing = pair_missing.all(axis=1)
            if both_missing.any():
                predictions = filled.loc[both_missing, self.pwht_columns_].to_numpy()
                distances = np.sum(((predictions[:, None, :] - self.pwht_pairs_[None, :, :])
                                    / self.pwht_scale_) ** 2, axis=2)
                filled.loc[both_missing, self.pwht_columns_] = self.pwht_pairs_[np.argmin(distances, axis=1)]
            for row in values.index[pair_missing.any(axis=1) & ~both_missing]:
                known = ~pair_missing.loc[row].to_numpy()
                candidates = self.pwht_pairs_
                if known.any():
                    compatible = np.isclose(
                        candidates[:, known], values.loc[row, self.pwht_columns_].to_numpy()[known]
                    ).all(axis=1)
                    if not compatible.any():
                        raise ValueError("No compatible training PWHT pair for partial observation.")
                    candidates = candidates[compatible]
                prediction = filled.loc[row, self.pwht_columns_].to_numpy()
                distance = np.sum(((candidates - prediction) / self.pwht_scale_) ** 2, axis=1)
                donor = candidates[np.argmin(distance)]
                for j, col in enumerate(self.pwht_columns_):
                    if pair_missing.at[row, col]:
                        filled.at[row, col] = donor[j]
        return filled.where(values.isna(), values)

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, "columns_")
        return np.array(self.columns_, dtype=object)
