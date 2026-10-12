"""Validation rule of notebook 09: guard bands, Charpy reading, aggregation and fold choice."""
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = {'__name__': '__main__'}
        notebook = json.loads((ROOT / 'notebooks/09_validation.ipynb').read_text())
        for i, cell in enumerate(notebook['cells']):
            if 'definitions' in cell.get('metadata', {}).get('tags', []):
                exec(compile(''.join(cell['source']), f'validation:cell{i}', 'exec'), cls.code)

    def statuses(self, values, limit, kind, w):
        return list(self.code['criterion_status'](values, limit, kind, w))

    def test_guard_band_statuses_on_both_sides(self):
        values = [431., 430., 429., 410., 409.9, np.nan]
        self.assertEqual(self.statuses(values, 420., 'min', 10.), ['C', 'C', 'I', 'I', 'NC', 'I'])
        values = [629., 630., 631., 650., 650.1]
        self.assertEqual(self.statuses(values, 640., 'max', 10.), ['C', 'C', 'I', 'I', 'NC'])
        self.assertEqual(self.statuses([420., 419.9, np.nan], 420., 'min', 0.), ['C', 'NC', 'I'])
        with self.assertRaises(ValueError):
            self.code['criterion_status']([1.], 0., 'min', -1.)
        with self.assertRaises(ValueError):
            self.code['criterion_status']([1.], 0., 'between', 0.)

    def test_charpy_measurement_uses_monotone_transition(self):
        temp = [-30., -20., 0., -20., -40., 0., np.nan]
        energy = [50., 47., 40., 46., 30., 60., 80.]
        status = self.code['charpy_measured_status'](temp, energy, -20., 47.)
        self.assertEqual(list(status), ['C', 'C', 'NC', 'NC', 'I', 'I', 'I'])

    def test_aggregation_separates_critical_and_informative_criteria(self):
        rows = [
            ['C', 'C', 'C', 'C', 'C'],
            ['C', 'C', 'NC', 'C', 'C'],
            ['NC', 'C', 'C', 'C', 'C'],
            ['C', 'C', 'C', 'I', 'C'],
            ['C', 'C', 'C', 'I', 'NC'],
        ]
        frame = pd.DataFrame(rows, columns=self.code['CRITERIA'])
        decision = list(self.code['aggregate'](frame))
        self.assertEqual(decision, ['VALIDÉ', 'PARTIEL', 'NON VALIDÉ', 'PARTIEL', 'NON VALIDÉ'])
        self.assertEqual(self.code['PROFILE']['charpy_temp_C'], -20.)
        self.assertEqual(self.code['K'], 2.)

    def test_predictions_use_k_times_rmse_per_target(self):
        rmse = {'yield_strength': 10., 'uts': 5., 'elongation': 1., 'charpy_J': 4.}
        values = pd.DataFrame({'yield_strength': [440., 439.9], 'uts': [570., 570.],
                               'elongation': [22., 22.], 'charpy_J': [55., 55.]})
        result = self.code['validate_predictions'](values, rmse)
        self.assertEqual(list(result.ys_min), ['C', 'I'])
        self.assertEqual(list(result.uts_max), ['C', 'C'])
        self.assertEqual(list(result.decision), ['VALIDÉ', 'PARTIEL'])
        measured = pd.DataFrame({'ys_min': ['NC', 'C', 'I'], 'decision': ['x', 'x', 'x']})
        predicted = pd.DataFrame({'ys_min': ['C', 'C', 'C'], 'decision': ['x', 'x', 'x']})
        row = self.code['compare_statuses'](predicted, measured, ['ys_min']).iloc[0]
        self.assertEqual((row.n_measure_decided, row.pred_C_measure_NC), (2, 1))
        self.assertAlmostEqual(row.false_acceptance_share, .5)

    def test_prediction_folds_never_use_a_model_trained_on_the_row(self):
        random_assign = pd.DataFrame({
            'raw_row_id': [1, 2, 3, 1, 2],
            'target': ['yield_strength'] * 3 + ['charpy_J'] * 2,
            'outer_fold': [0, 1, 2, 4, 3],
        })
        grouped_assign = pd.DataFrame({'raw_row_id': [1, 2, 3], 'outer_fold': [2, 2, 0]})
        folds = self.code['prediction_folds']([1, 2, 3], 'random', 'charpy_J', random_assign,
                                              grouped_assign, labeled=[True, True, False])
        self.assertEqual(list(folds), [4, 3, 2])
        with self.assertRaises(ValueError):
            self.code['prediction_folds']([1, 2, 3], 'random', 'charpy_J', random_assign,
                                          grouped_assign, labeled=[True, True, True])
        folds = self.code['prediction_folds']([1, 2, 3], 'grouped', 'charpy_J', random_assign,
                                              grouped_assign, labeled=[True, True, False])
        self.assertEqual(list(folds), [2, 2, 0])

    def test_out_of_fold_prediction_forces_required_charpy_temperature(self):
        class FoldModel:
            def __init__(self, fold):
                self.fold = fold

            def predict(self, X):
                return X['charpy_temp_C'].to_numpy() + 1000 * self.fold

        frame = pd.DataFrame({'charpy_temp_C': [20., -60., 0.], 'C': [.1, .1, .1]}, index=[7, 8, 9])
        folds = pd.Series([0, 1, 0], index=frame.index)
        load = lambda fold: (FoldModel(fold), ['C', 'charpy_temp_C'])
        prediction = self.code['predict_out_of_fold'](frame, folds, load, charpy_temp_C=-20.)
        self.assertEqual(list(prediction), [-20., 980., -20.])
        self.assertEqual(list(frame.charpy_temp_C), [20., -60., 0.])
        with self.assertRaises(ValueError):
            self.code['predict_out_of_fold'](frame, folds, lambda fold: (FoldModel(fold), ['C']), charpy_temp_C=-20.)


if __name__ == '__main__':
    unittest.main()
