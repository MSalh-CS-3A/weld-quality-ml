"""Training boundaries and target-specific pipelines defined in notebook 03."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_modeling_definitions():
    notebook = json.loads((ROOT / 'notebooks/03_modeling.ipynb').read_text())
    namespace = {'__name__': '__main__'}
    for index, cell in enumerate(notebook['cells']):
        if 'definitions' in cell.get('metadata', {}).get('tags', []):
            exec(compile(''.join(cell['source']), f'modeling:cell-{index}', 'exec'), namespace)
    return namespace


class ModelingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = load_modeling_definitions()

    def frame(self):
        n = 60
        group_index = np.repeat(np.arange(10), 6)
        frame = pd.DataFrame({name: np.linspace(0.1, 0.8, n)
                              for name in self.code['CORE13']})
        frame['pwht_temp_C'] = np.tile([0., 600., 650.], 20)
        frame['pwht_time_h'] = np.tile([0., 2., 3.], 20)
        frame['weld_process'] = np.tile(['MMA', 'SA'], 30)
        frame['charpy_temp_C'] = np.linspace(-100., 20., n)
        for i, target in enumerate(self.code['TARGETS']):
            frame[target] = np.linspace(100. + i, 200. + i, n)
        frame['in_strict13'] = True
        frame['raw_row_id'] = np.arange(n)
        frame['group'] = [f'g{i}' for i in group_index]
        frame['outer_fold'] = group_index % 5
        for k in range(5):
            frame[f'inner_fold_when_outer{k}'] = np.where(
                frame.outer_fold == k, -1, group_index % 3)
        return frame

    def test_target_specific_inputs_and_label_eligibility(self):
        frame = self.frame()
        frame.loc[0, 'charpy_temp_C'] = np.nan
        frame.loc[1, 'yield_strength'] = np.nan
        frame.loc[2, 'in_strict13'] = False
        for target in self.code['TARGETS']:
            features = self.code['task_features'](target)
            self.assertFalse(set(features).intersection(self.code['TARGETS']))
            self.assertFalse(set(features).intersection({'group', 'outer_fold', 'raw_row_id'}))
            self.assertEqual('charpy_temp_C' in features, target == 'charpy_J')
        ys = self.code['eligible_rows'](frame, 'yield_strength')
        charpy = self.code['eligible_rows'](frame, 'charpy_J')
        self.assertIn(0, ys.index)  # Charpy missing does not remove a traction label.
        self.assertNotIn(1, ys.index)
        self.assertNotIn(0, charpy.index)
        self.assertIn(1, charpy.index)  # Another output is not required.
        self.assertNotIn(2, ys.index)
        self.assertNotIn(2, charpy.index)

    def test_invalid_inner_membership_and_shared_groups_are_rejected(self):
        frame = self.frame()
        train, valid = self.code['outer_partitions'](frame, 'yield_strength', 0)
        self.assertTrue(set(train.group).isdisjoint(valid.group))
        train.loc[0, 'inner_fold_when_outer0'] = -1
        with self.assertRaisesRegex(AssertionError, 'externes'):
            self.code['inner_splits'](train, 0)
        frame.loc[0, 'group'] = frame.loc[6, 'group']
        with self.assertRaisesRegex(AssertionError, 'partagé'):
            self.code['outer_partitions'](frame, 'yield_strength', 0)

    def test_search_refits_preprocessing_on_each_inner_train_then_outer_train(self):
        train, _ = self.code['outer_partitions'](self.frame(), 'yield_strength', 0)
        splits = self.code['inner_splits'](train, 0)
        fits = []
        cls = self.code['FoldPreprocessor']
        original_fit = cls.fit

        def tracked_fit(transformer, X, y=None):
            fits.append(set(X.index))
            return original_fit(transformer, X, y)

        with patch.object(cls, 'fit', tracked_fit):
            with patch.dict(self.code['PARAM_GRIDS'], {'ridge': {'model__alpha': [0.1, 1]}}):
                search = self.code['tune_pipeline'](
                    train, 'yield_strength', 'ridge', 0, n_jobs=1)
        expected_trains = [set(train.iloc[tr].index) for tr, _ in splits]
        self.assertEqual(len(fits), 7)  # 2 candidates × 3 splits + one outer refit.
        for expected in expected_trains:
            self.assertEqual(fits[:-1].count(expected), 2)
        self.assertEqual(fits[-1], set(train.index))
        pre = search.best_estimator_.named_steps['preprocess']
        np.testing.assert_allclose(pre.mu_, train[self.code['CORE13']].mean())

    def test_svr_target_scaling_and_feature_statistics_are_train_only(self):
        train, valid = self.code['outer_partitions'](self.frame(), 'charpy_J', 0)
        features = self.code['task_features']('charpy_J')
        pipeline = self.code['make_pipeline']('svr_rbf', 'charpy_J')
        pipeline.fit(train[features], train.charpy_J)
        pre = pipeline.named_steps['preprocess']
        target_transformer = pipeline.named_steps['model'].transformer_
        np.testing.assert_allclose(pre.mu_, train[self.code['numeric_features']('charpy_J')].mean())
        self.assertAlmostEqual(target_transformer.mean_[0], train.charpy_J.mean())
        original_mean = pre.mu_.copy()
        valid.loc[:, 'C'] = 1000.
        valid.loc[:, 'charpy_J'] = 100000.
        prediction = pipeline.predict(valid[features])
        self.assertTrue(np.isfinite(prediction).all())
        np.testing.assert_array_equal(pre.mu_, original_mean)
        self.assertAlmostEqual(target_transformer.mean_[0], train.charpy_J.mean())
        # predict() returns the original J scale, rather than standardized targets.
        transformed = pre.transform(valid[features])
        scaled = pipeline.named_steps['model'].regressor_.predict(transformed)
        restored = target_transformer.inverse_transform(scaled.reshape(-1, 1)).ravel()
        np.testing.assert_allclose(prediction, restored)

    def test_baseline_ignores_missing_features_and_uses_only_training_labels(self):
        train, valid = self.code['outer_partitions'](self.frame(), 'yield_strength', 0)
        features = self.code['task_features']('yield_strength')
        train.loc[:, self.code['CORE13']] = np.nan
        pipeline = self.code['make_pipeline']('median_y', 'yield_strength')
        pipeline.fit(train[features], train.yield_strength)
        self.assertNotIn('preprocess', pipeline.named_steps)
        np.testing.assert_allclose(pipeline.predict(valid[features]), train.yield_strength.median())


if __name__ == '__main__':
    unittest.main()
