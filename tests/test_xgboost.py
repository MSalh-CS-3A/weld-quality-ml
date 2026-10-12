"""XGBoost-specific fold-local fitting, family selection and portable exports."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class XGBoostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = {'__name__': '__main__'}
        notebook = json.loads((ROOT / 'notebooks/08_xgboost.ipynb').read_text())
        for i, cell in enumerate(notebook['cells']):
            if 'definitions' in cell.get('metadata', {}).get('tags', []):
                exec(compile(''.join(cell['source']), f'xgboost:cell{i}', 'exec'), cls.code)

    def frame(self):
        n = 60
        frame = pd.DataFrame({c: np.linspace(.1, .8, n) for c in self.code['CORE16']})
        frame['Ni'] = np.where(np.arange(n) % 4 == 0, np.nan, frame.Ni)
        frame['pwht_temp_C'] = np.tile([0., 600., 650.], 20)
        frame['pwht_time_h'] = np.tile([0., 2., 3.], 20)
        frame['weld_process'] = np.tile(['MMA', 'SA', 'MMA'], 20)
        frame['charpy_temp_C'] = np.linspace(-100., 20., n)
        frame['raw_row_id'] = np.arange(n)
        frame['group'] = np.repeat(['a', 'b', 'c', 'd', 'e'], 12)
        frame['in_strict13'] = True
        frame['is_duplicate_excess'] = False
        for target in self.code['TARGETS']:
            frame[target] = 100 + 100 * frame.C ** 2
        return frame

    def test_xgboost_search_fits_preprocessing_only_on_each_inner_train(self):
        frame = self.frame()
        plan = self.code['build_random_plan'](frame, 'yield_strength')
        train, _ = self.code['random_partitions'](frame, plan, 0)
        cv = self.code['random_inner_splits'](train, plan, 0)
        preprocessor = self.code['FoldPreprocessor']
        original = preprocessor.fit
        seen = []

        def track(pre, X, y=None):
            seen.append(set(X.index))
            return original(pre, X, y)

        small_grid = {'model__n_estimators': [3, 5], 'model__max_depth': [2]}
        with patch.object(preprocessor, 'fit', track), patch.dict(self.code['PARAM_GRIDS'], {'xgboost': small_grid}), patch.dict(self.code, {'N_JOBS': 1}):
            search = self.code['search_pipeline'](train, 'yield_strength', 'xgboost', cv)
        self.assertEqual(len(seen), 7)
        for tr, _ in cv:
            self.assertEqual(seen[:-1].count(set(train.iloc[tr].index)), 2)
        self.assertEqual(seen[-1], set(train.index))
        pre = search.best_estimator_.named_steps['preprocess']
        np.testing.assert_allclose(pre.mu_, train[self.code['CORE16']].mean())
        expected = (train[self.code['CORE16']].median().to_numpy() - pre.mu_) / pre.sd_
        np.testing.assert_allclose(pre.imp_.statistics_[:16], expected)
        self.assertIsNone(search.best_estimator_.named_steps['model'].get_params()['early_stopping_rounds'])

    def test_selection_uses_inner_mae_even_when_outer_results_prefer_another_family(self):
        rows = pd.DataFrame([
            {'model': 'xgboost', 'inner_MAE': 3., 'MAE': 1., 'R2': .9},
            {'model': 'ridge', 'inner_MAE': 2., 'MAE': 100., 'R2': -9.},
        ])
        choose = self.code['choose_inner_family']
        self.assertEqual(choose(rows)['model'], 'ridge')
        rows.loc[0, 'inner_MAE'] = 2.
        self.assertEqual(choose(rows)['model'], 'ridge')
        with self.assertRaises(ValueError):
            choose(pd.concat([rows, rows]))

    def test_export_preserves_xgboost_predictions_and_rejects_unknown_charpy_temperature(self):
        frame = self.frame()
        features = self.code['task_features']('charpy_J')
        pipeline = self.code['make_pipeline']('xgboost', 'charpy_J').set_params(model__n_estimators=5)
        pipeline.fit(frame[features], frame.charpy_J)
        self.assertTrue(set(features).isdisjoint(self.code['TARGETS']))
        with tempfile.TemporaryDirectory() as temp, patch.dict(self.code, {'VERSIONS': {'test': True}}):
            path = Path(temp) / 'xgboost.pkl'
            meta = self.code['dump_pipeline'](pipeline, path, {'features': features}, frame[features])
            with path.open('rb') as stream:
                loaded = self.code['cloudpickle'].load(stream)
            np.testing.assert_allclose(loaded.predict(frame[features]), pipeline.predict(frame[features]))
            self.assertIsNone(loaded.memory)
            self.assertEqual(meta['artifact_sha256'], json.loads(path.with_suffix('.json').read_text())['artifact_sha256'])
            unknown = frame[features].head(1).copy()
            unknown['charpy_temp_C'] = np.nan
            with self.assertRaisesRegex(ValueError, 'Température Charpy requise'):
                loaded.predict(unknown)

    def test_summary_distinguishes_fold_mean_from_pooled_oof(self):
        metrics = self.code['regression_metrics']
        preds = pd.DataFrame({'protocol': 'random', 'target': 'uts', 'model': 'xgboost',
            'outer_fold': [0, 0, 1, 1, 1], 'y_true': [0., 2., 10., 20., 30.],
            'y_pred': [1., 1., 10., 20., 30.]})
        scores = pd.DataFrame([{'protocol': 'random', 'target': 'uts', 'model': 'xgboost',
            'outer_fold': fold, **metrics(p.y_true, p.y_pred)} for fold, p in preds.groupby('outer_fold')])
        summary = self.code['benchmark_summary'](scores, preds).iloc[0]
        self.assertAlmostEqual(summary.MAE_mean, .5)
        self.assertAlmostEqual(summary.OOF_MAE, .4)
        self.assertNotAlmostEqual(summary.R2_mean, summary.OOF_R2)


if __name__ == '__main__':
    unittest.main()
