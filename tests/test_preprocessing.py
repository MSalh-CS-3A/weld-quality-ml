"""Focused checks for provenance, constraints and training/verification isolation."""

import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from weld_quality.preprocessing import (
    audit_measurements, prepare_matrix, identifier_groups, WeldInputImputer,
)
from weld_quality.exploration import (
    artificial_mask, benchmark_imputation, fit_exploratory_pca, compare_pca,
)
from weld_quality.schema import COLUMNS


class MeasurementTests(unittest.TestCase):
    def test_status_bounds_annotations_and_raw_preservation(self):
        raw = pd.DataFrame({
            "carbon": ["1e-2", "<0.02", "N", "-1"],
            "interpass_temperature": ["150-200", "-20--10", "N", "200-150"],
            "nitrogen": ["67tot33res", "66totndres", "20", "N"],
            "hardness": ["203(Hv30)", "226Hv5", "N", "200"],
            "weld_id": ["a", "b", "c", "d"],
        })
        original = raw.copy(deep=True)
        audit = audit_measurements(raw)
        assert_frame_equal(raw, original)
        self.assertEqual(audit.status.at[1, "carbon"], "censored")
        self.assertEqual(audit.status.at[2, "carbon"], "missing")
        self.assertEqual(audit.exact.at[0, "carbon"], .01)
        self.assertEqual(audit.lower.at[1, "carbon"], 0)
        self.assertEqual(audit.upper.at[1, "carbon"], .02)
        self.assertTrue(audit.review.at[3, "carbon"])
        self.assertTrue(audit.review.at[3, "interpass_temperature"])
        values, provenance = prepare_matrix(audit, ["carbon", "interpass_temperature"])
        self.assertEqual(values.at[1, "carbon"], .01)
        self.assertEqual(values.at[0, "interpass_temperature"], 175)
        self.assertEqual(values.at[1, "interpass_temperature"], -15)
        self.assertEqual(provenance.at[1, "carbon"], "censor_approximation")
        self.assertTrue(np.isnan(values.at[3, "carbon"]))
        nd = audit.annotations.loc[audit.annotations.raw_value.eq("66totndres")].iloc[0]
        self.assertEqual(nd.res_token, "nd")
        hv = audit.annotations.loc[audit.annotations.raw_value.eq("203(Hv30)")].iloc[0]
        self.assertEqual(hv.extracted_number, 203)
        self.assertEqual(hv.protocol, "Hv30")
        self.assertTrue(audit.exact.at[0, "nitrogen"] is np.nan or pd.isna(audit.exact.at[0, "nitrogen"]))

    def test_suspect_units_are_unresolved_not_original_missing(self):
        raw = pd.DataFrame({"aluminium": ["0.004", "<0.01", "<5", "N"],
                            "vanadium": ["<5", "<0.01", "0.1", "0"],
                            "weld_id": ["a", "b", "c", "d"]})
        audit = audit_measurements(raw)
        values, provenance = prepare_matrix(audit, ["aluminium", "vanadium"])
        self.assertTrue(values.aluminium.iloc[:2].isna().all())
        self.assertEqual(audit.status.at[0, "aluminium"], "numeric")
        self.assertEqual(provenance.at[0, "aluminium"], "unresolved_review")
        self.assertEqual(values.at[2, "aluminium"], 2.5)
        self.assertTrue(np.isnan(values.at[0, "vanadium"]))
        self.assertEqual(values.at[3, "vanadium"], 0)
        for scenario in ["zero", "half", "sqrt2"]:
            matrix, _ = prepare_matrix(audit, ["aluminium"], censor=scenario)
            self.assertGreaterEqual(matrix.at[2, "aluminium"], 0)
            self.assertLess(matrix.at[2, "aluminium"], 5)

    def test_groups_combine_known_variants_and_do_not_guess_unknown_suffix(self):
        raw = pd.DataFrame({"weld_id": ["Evans-Ni/CMn-1990/1991-0Aaw",
             "Evans-Ni/CMn-1990/1991-0Bhtch2", "p9-RR82011", "p10-RR82011",
             "EvansLetterCo+ch1", "EvansLetterC+1Ni", "unknown-a", "unknown-b"]})
        groups = identifier_groups(raw)
        self.assertEqual(groups.group.iloc[0], groups.group.iloc[1])
        self.assertEqual(groups.group.iloc[2], groups.group.iloc[3])
        self.assertEqual(groups.group.iloc[4], groups.group.iloc[5])
        self.assertNotEqual(groups.group.iloc[6], groups.group.iloc[7])

    def test_exact_raw_duplicate_connects_different_series(self):
        raw = pd.DataFrame("N", index=range(3), columns=COLUMNS)
        raw["weld_id"] = ["Evans-V/Mn-1991-A3aw", "Evans-Nb/Mn-1991-A<5aw", "other-series"]
        raw["carbon"] = [".074", ".074", ".08"]
        grouped = identifier_groups(raw)
        self.assertEqual(grouped.group.iloc[0], grouped.group.iloc[1])
        self.assertNotEqual(grouped.group.iloc[0], grouped.group.iloc[2])
        self.assertIn("exact_duplicate_link", grouped.group_rule.iloc[0])


class ImputationTests(unittest.TestCase):
    def test_verification_values_cannot_change_training_median(self):
        train = pd.DataFrame({"carbon": [.1, .2, .3], "weld_type": ["MMA"] * 3})
        model = WeldInputImputer().fit(train)
        test = pd.DataFrame({"carbon": [np.nan, 99.0], "weld_type": ["unseen", "MMA"]})
        result = model.transform(test)
        self.assertEqual(result.carbon.iloc[0], .2)
        self.assertEqual(result.carbon.iloc[1], 99)
        self.assertEqual(model.medians_["carbon"], .2)

    def test_process_support_counts_groups_not_repeated_rows(self):
        train = pd.DataFrame({"carbon": [.1] * 20 + [.4, .5, .6],
                              "weld_type": ["MMA"] * 20 + ["SA"] * 3})
        model = WeldInputImputer(method="process_median", min_groups=3).fit(
            train, groups=["same_weld"] * 20 + ["a", "b", "c"])
        self.assertTrue(pd.isna(model.process_medians_.at["MMA", "carbon"]))
        test = pd.DataFrame({"carbon": [np.nan] * 3, "weld_type": ["MMA", "SA", "new"]})
        result = model.transform(test)
        self.assertEqual(result.carbon.iloc[0], .1)
        self.assertEqual(result.carbon.iloc[1], .5)
        self.assertEqual(result.carbon.iloc[2], .1)

    def test_joint_pwht_and_observed_preservation_all_methods(self):
        train = pd.DataFrame({"carbon": [.1, .2, .3, .4, .5, .6],
            "pwht_temperature": [0, 0, 250, 250, 580, 580],
            "pwht_time": [0, 0, 2, 2, 10, 10], "weld_type": ["MMA"] * 6})
        test = pd.DataFrame({"carbon": [.7, np.nan], "pwht_temperature": [np.nan, 0],
                              "pwht_time": [np.nan, np.nan], "weld_type": ["MMA", "MMA"]})
        pairs = set(map(tuple, train[["pwht_temperature", "pwht_time"]].to_numpy()))
        for method in ["median", "process_median", "iterative"]:
            model = WeldInputImputer(method=method).fit(train, groups=list("abcdef"))
            result = model.transform(test)
            self.assertIn(tuple(result.loc[0, ["pwht_temperature", "pwht_time"]]), pairs)
            self.assertEqual(result.at[1, "pwht_time"], 0)
            self.assertEqual(result.at[0, "carbon"], .7)
            self.assertFalse(result.isna().any().any())

    def test_targets_and_empty_training_columns_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "no targets"):
            WeldInputImputer().fit(pd.DataFrame({"yield_strength": [500], "weld_type": ["MMA"]}))
        with self.assertRaisesRegex(ValueError, "No observed training"):
            WeldInputImputer().fit(pd.DataFrame({"carbon": [np.nan], "weld_type": ["MMA"]}))
        with self.assertRaisesRegex(ValueError, "training groups"):
            WeldInputImputer(method="process_median").fit(
                pd.DataFrame({"carbon": [.1], "weld_type": ["MMA"]}))

    def test_clone_and_pipeline(self):
        train = pd.DataFrame({"carbon": [.1, .2, np.nan], "weld_type": ["MMA"] * 3})
        estimator = WeldInputImputer(random_state=7)
        self.assertEqual(clone(estimator).random_state, 7)
        result = Pipeline([("impute", estimator), ("scale", StandardScaler())]).fit_transform(train)
        self.assertTrue(np.isfinite(result).all())


class VerificationTests(unittest.TestCase):
    def test_mask_only_exact_eligible_values_and_training_blocks(self):
        eligible = pd.DataFrame(True, index=range(100), columns=["carbon", "current", "voltage"])
        eligible.loc[0, "carbon"] = False
        patterns = pd.DataFrame([[False, True, True]], columns=eligible.columns)
        mask = artificial_mask(eligible, patterns, .4, np.random.default_rng(42), "blocks")
        self.assertFalse(mask.at[0, "carbon"])
        self.assertFalse(mask.carbon.any())
        self.assertTrue(mask.current.equals(mask.voltage))

    def test_grouped_benchmark_reproducible_and_shared_masks(self):
        values = pd.DataFrame({"carbon": np.linspace(.03, .15, 30),
                               "silicon": np.linspace(.1, .8, 30)})
        process = pd.Series(["MMA"] * 15 + ["SA"] * 15)
        groups = pd.Series(np.repeat(np.arange(10), 3))
        kwargs = dict(n_splits=3, seeds=(42,), rates=(.2,), patterns=("cells",))
        result = benchmark_imputation(values, values.notna(), process, groups, **kwargs)
        repeated = benchmark_imputation(values, values.notna(), process, groups, **kwargs)
        assert_frame_equal(result.metrics, repeated.metrics)
        for _, split in result.splits.groupby("fold"):
            self.assertFalse(set(split.loc[split.role.eq("train"), "group"]) &
                             set(split.loc[split.role.eq("test"), "group"]))
        self.assertTrue(result.metrics.groupby(["fold", "seed", "rate", "pattern"]).mask_sha256.nunique().eq(1).all())
        self.assertTrue(result.metrics.outside_bounds.eq(0).all())

    def test_pca_contributions_and_subspace_sign_invariance(self):
        rng = np.random.default_rng(42)
        values = pd.DataFrame(rng.normal(size=(30, 4)), columns=list("abcd"))
        reference = fit_exploratory_pca(values)
        altered = fit_exploratory_pca(values)
        altered.pca.components_[:2] *= -1
        altered.directions.iloc[:, :2] *= -1
        self.assertAlmostEqual(compare_pca(reference, altered)["max_angle_degrees"], 0, places=5)
        np.testing.assert_allclose(reference.contributions.sum(), 100)


if __name__ == "__main__":
    unittest.main()
