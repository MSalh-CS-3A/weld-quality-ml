"""Focused scientific safeguards exercised directly from notebook definitions."""

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_definitions():
    notebook = json.loads((ROOT / 'notebooks/02_data_preparation.ipynb').read_text())
    namespace = {'__name__': '__main__'}
    for index, cell in enumerate(notebook['cells']):
        if 'definitions' in cell.get('metadata', {}).get('tags', []):
            exec(compile(''.join(cell['source']), f'preparation:cell-{index}', 'exec'), namespace)
    return namespace


class NotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = load_definitions()

    def test_all_notebook_code_compiles(self):
        for path in (ROOT / 'notebooks').glob('*.ipynb'):
            notebook = json.loads(path.read_text())
            for index, cell in enumerate(notebook['cells']):
                if cell['cell_type'] == 'code':
                    compile(''.join(cell['source']), f'{path.name}:cell-{index}', 'exec')

    def test_censoring_annotations_and_unit_review_remain_distinct(self):
        classify = self.code['classify_token']
        rows = []
        for column, token in [('S','0'), ('S','<0.002'), ('interpass_C','150-200'),
                              ('N_ppm','67tot33res'), ('Ti_ppm','0.5'), ('S','N')]:
            info = classify(column, token)
            rows.append(dict(column=column, raw_token=token, **info,
                             review_flag=self.code['unit_review_flag'](column, token, info)))
        prov = pd.DataFrame(rows)
        values = self.code['primary_value'](prov)
        self.assertEqual(values.iloc[0], 0)
        self.assertEqual(values.iloc[1], .001)
        self.assertEqual(prov.iloc[1]['upper'], .002)
        self.assertEqual(values.iloc[2], 175)
        self.assertEqual(prov.iloc[3]['annotation'], 'tot=67;res=33')
        self.assertTrue(values.iloc[3:].isna().all())

    def test_duplicate_aliases_connect_different_identifier_series(self):
        columns = self.code['RAW_COLS']
        frame = pd.DataFrame('1', index=range(3), columns=columns)
        frame['weld_id'] = ['Alpha-1990-A', 'Beta-1991-B', 'Gamma-1992-C']
        frame.loc[2, 'C'] = '2'
        frame.insert(0,'raw_row_id',np.arange(3))
        aliases = self.code['find_duplicates'](frame)
        self.assertEqual(aliases.raw_row_id.tolist(), [1])
        self.assertEqual(aliases.kept_raw_row_id.tolist(), [0])
        groups = self.code['build_groups'](frame, aliases)
        self.assertEqual(groups.group.iloc[0], groups.group.iloc[1])
        self.assertNotEqual(groups.group.iloc[0], groups.group.iloc[2])

    def test_invalid_raw_width_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.data'
            path.write_text('1 2 3\n')
            with self.assertRaisesRegex(ValueError, '44 champs'):
                self.code['read_raw'](path)

    def test_tensile_schemas_exclude_outputs_and_charpy_temperature(self):
        for task in self.code['TENSILE'] + self.code['COMPLEMENTARY']:
            schema = self.code['task_schema'](task)
            self.assertFalse(set(schema['num']).intersection(
                self.code['ALL_TARGETS'] + ['charpy_temp_C']))
        self.assertIn('charpy_temp_C', self.code['task_schema']('charpy_E_of_T')['num'])
        self.assertEqual(self.code['task_schema']('T100J')['target'], 'charpy_temp_C')

    def test_external_and_internal_groups_are_disjoint(self):
        master = pd.DataFrame({'raw_row_id': range(50),
                               'group': np.repeat([f'g{i}' for i in range(10)],5),
                               'is_duplicate_excess': False})
        folds = self.code['assign_folds'](master)
        self.assertEqual(folds.groupby('group').outer_fold.nunique().max(),1)
        for k in range(5):
            train, valid = folds[folds.outer_fold != k], folds[folds.outer_fold == k]
            self.assertTrue(set(train.group).isdisjoint(valid.group))
            column = f'inner_fold_when_outer{k}'
            self.assertTrue(valid[column].eq(-1).all())
            for j in range(3):
                self.assertTrue(set(train.loc[train[column] != j,'group']).isdisjoint(
                    train.loc[train[column] == j,'group']))

    def frame(self):
        return pd.DataFrame({'C':[.1,.2,.3,.4,.5,.6],
                             'pwht_temp_C':[0.,600.,650.,0.,600.,650.],
                             'pwht_time_h':[0.,2.,3.,0.,2.,3.],
                             'weld_process':['MMA','MMA','SA','SA','MMA','SA']})

    def test_fit_statistics_are_train_only_and_observations_preserved(self):
        train = self.frame()
        numeric = ['C','pwht_temp_C','pwht_time_h']
        cls = self.code['FoldPreprocessor']
        for method in ['median','iterative']:
            pre = cls(numeric,method=method).fit(train)
            mean = pre.mu_.copy()
            test = pd.DataFrame({'C':[50.,np.nan], 'pwht_temp_C':[650.,np.nan],
                                 'pwht_time_h':[np.nan,np.nan], 'weld_process':['unseen','MMA']})
            transformed = pre.transform(test)
            restored = transformed[:,:3] * pre.sd_ + pre.mu_
            original = test[numeric].to_numpy(float)
            observed = np.isfinite(original)
            self.assertTrue(np.allclose(restored[observed],original[observed]))
            self.assertTrue(np.array_equal(mean,pre.mu_))
            self.assertTrue(np.allclose(mean,train[numeric].mean()))
            self.assertTrue(np.isfinite(transformed).all())
            self.assertTrue(np.allclose(transformed[0,3:],0))
            self.assertAlmostEqual(restored[0,2],3)
            actual = train[['pwht_temp_C','pwht_time_h']].to_numpy(float)
            self.assertTrue(np.isclose(actual,restored[1,1:3]).all(axis=1).any())

    def test_incompatible_partial_pwht_is_rejected(self):
        pre = self.code['FoldPreprocessor'](['C','pwht_temp_C','pwht_time_h'],method='median').fit(self.frame())
        test = pd.DataFrame({'C':[.2],'pwht_temp_C':[700.], 'pwht_time_h':[np.nan], 'weld_process':['MMA']})
        with self.assertRaisesRegex(ValueError,'Aucun couple PWHT compatible'):
            pre.transform(test)

    def test_empty_training_column_is_rejected(self):
        train = self.frame()
        train['C'] = np.nan
        with self.assertRaisesRegex(ValueError,'entièrement absentes'):
            self.code['FoldPreprocessor'](['C','pwht_temp_C','pwht_time_h']).fit(train)

    def test_nonconverged_fit_is_rejected(self):
        train = self.frame()
        train.loc[1,'C'] = np.nan
        with self.assertRaisesRegex(RuntimeError,'non convergée'):
            self.code['FoldPreprocessor'](['C','pwht_temp_C','pwht_time_h'],max_iter=1).fit(train)


if __name__ == '__main__':
    unittest.main()
