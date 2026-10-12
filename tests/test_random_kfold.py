"""Random/inductive boundaries and portable pipelines from notebook 05."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class RandomKFoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = {'__name__': '__main__'}
        notebook = json.loads((ROOT / 'notebooks/05_random_kfold.ipynb').read_text())
        for i, cell in enumerate(notebook['cells']):
            if 'definitions' in cell.get('metadata', {}).get('tags', []):
                exec(compile(''.join(cell['source']), f'random:cell{i}', 'exec'), cls.code)

    def frame(self):
        n = 75
        frame = pd.DataFrame({c: np.linspace(.1, .8, n) for c in self.code['CORE16']})
        frame['pwht_temp_C'] = np.tile([0., 600., 650.], 25)
        frame['pwht_time_h'] = np.tile([0., 2., 3.], 25)
        frame['weld_process'] = np.tile(['MMA', 'SA', 'MMA'], 25)
        frame['charpy_temp_C'] = np.linspace(-100., 20., n)
        frame['raw_row_id'] = np.arange(n)
        frame['group'] = np.repeat(['a', 'b', 'c'], 25)
        frame['in_strict13'] = True
        frame['is_duplicate_excess'] = False
        for target in self.code['TARGETS']:
            frame[target] = np.linspace(100., 200., n)
            frame.loc[60:, target] = np.nan
        return frame

    def test_split_is_reproducible_and_does_not_consult_label_values(self):
        frame = self.frame()
        build = self.code['build_random_plan']
        first = build(frame, 'yield_strength')
        altered = frame.sample(frac=1, random_state=9).copy()
        altered.loc[altered.yield_strength.notna(), 'yield_strength'] *= -1000
        pd.testing.assert_frame_equal(first, build(altered, 'yield_strength'))
        for _, g in first.groupby('label_state'):
            self.assertLessEqual(g.outer_fold.value_counts().max() - g.outer_fold.value_counts().min(), 1)

    def test_inductive_pool_excludes_outer_and_inner_validation_inputs(self):
        plan = self.code['build_random_plan'](self.frame(), 'uts')
        for outer in range(5):
            held_outer = set(plan.loc[plan.outer_fold == outer, 'raw_row_id'])
            for inner in [None, 0, 1, 2]:
                access = self.code['permitted_ids'](plan, outer, inner)
                labeled, pool, valid = (set(access[k]) for k in ['labeled_train', 'unlabeled_train', 'labeled_valid'])
                self.assertTrue(labeled.isdisjoint(pool | valid | held_outer))
                self.assertTrue(pool.isdisjoint(valid | held_outer))
                self.assertTrue(pool <= set(range(60, 75)))
                if inner is not None:
                    held_inner = set(plan.loc[plan[f'inner_fold_when_outer{outer}'] == inner, 'raw_row_id'])
                    self.assertTrue((labeled | pool).isdisjoint(held_inner))

    def test_charpy_requires_known_temperature_in_pool_and_inference(self):
        frame = self.frame()
        frame.loc[60:, 'charpy_temp_C'] = np.nan
        plan = self.code['build_random_plan'](frame, 'charpy_J')
        self.assertFalse((plan.label_state == 'unlabeled').any())
        features = self.code['task_features']('charpy_J')
        pipeline = self.code['make_pipeline']('ridge', 'charpy_J')
        pipeline.fit(frame.loc[:59, features], frame.loc[:59, 'charpy_J'])
        with self.assertRaisesRegex(ValueError, 'Température Charpy requise'):
            pipeline.predict(frame.loc[60:, features])
        self.assertFalse(set(features) & set(self.code['TARGETS']))
        self.assertEqual(len(self.code['numeric_features']('uts')), 16)

    def test_inner_search_relearns_medians_only_in_current_training_rows(self):
        frame = self.frame()
        frame.loc[::4, 'Ni'] = np.nan
        plan = self.code['build_random_plan'](frame, 'yield_strength')
        train, _ = self.code['random_partitions'](frame, plan, 0)
        cv = self.code['random_inner_splits'](train, plan, 0)
        seen = []
        cls = self.code['FoldPreprocessor']
        original = cls.fit

        def track(pre, X, y=None):
            seen.append(set(X.index))
            return original(pre, X, y)

        with patch.object(cls, 'fit', track), patch.dict(self.code['PARAM_GRIDS'], {'ridge': {'model__alpha': [.1, 1]}}), patch.dict(self.code, {'N_JOBS': 1}):
            search = self.code['search_pipeline'](train, 'yield_strength', 'ridge', cv)
        self.assertEqual(len(seen), 7)
        for tr, _ in cv:
            self.assertEqual(seen[:-1].count(set(train.iloc[tr].index)), 2)
        self.assertEqual(seen[-1], set(train.index))
        pre = search.best_estimator_.named_steps['preprocess']
        expected = (train[self.code['CORE16']].median().to_numpy() - pre.mu_) / pre.sd_
        np.testing.assert_allclose(pre.imp_.statistics_[:16], expected)

    def test_export_detaches_cache_and_keeps_predictions_and_metadata(self):
        frame = self.frame().iloc[:60]
        features = self.code['task_features']('uts')
        pipeline = self.code['make_pipeline']('ridge', 'uts').fit(frame[features], frame.uts)
        with tempfile.TemporaryDirectory() as temp, patch.dict(self.code, {'VERSIONS': {'test': True}}):
            pipeline.memory = str(Path(temp) / 'cache')
            path = Path(temp) / 'ridge.pkl'
            metadata = self.code['dump_pipeline'](pipeline, path, {'features': features}, frame[features].head())
            with path.open('rb') as stream:
                loaded = self.code['cloudpickle'].load(stream)
            self.assertIsNone(loaded.memory)
            self.assertIsNotNone(pipeline.memory)
            np.testing.assert_allclose(loaded.predict(frame[features]), pipeline.predict(frame[features]))
            self.assertEqual(json.loads(path.with_suffix('.json').read_text())['artifact_sha256'], metadata['artifact_sha256'])


if __name__ == '__main__':
    unittest.main()
