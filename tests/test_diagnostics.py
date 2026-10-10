"""Scientific invariants for retrospective diagnostics defined in notebook 04."""
import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def load_definitions():
    n=json.loads((ROOT/'notebooks/04_diagnostics.ipynb').read_text())
    ns={'__name__':'__main__'}
    for cell in n['cells']:
        if set(cell.get('metadata',{}).get('tags',[])) & {'definitions','diagnostic_definitions'}:
            exec(''.join(cell['source']),ns)
    return ns


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.ns=load_definitions()

    def test_group_bias_and_variance_decompositions(self):
        frame=pd.DataFrame({'group':['a','a','b','b'],
                            'y_true':[0.,2.,4.,6.], 'y_pred':[2.,4.,3.,5.]})
        d=self.ns['error_decomposition'](frame)
        self.assertAlmostEqual(d['SSE'],10.)
        self.assertAlmostEqual(d['SST'],20.)
        self.assertAlmostEqual(d['between_group_SST_fraction'],.8)
        self.assertAlmostEqual(d['group_bias_SSE_fraction'],1.)
        self.assertAlmostEqual(d['R2'],.5)
        self.assertAlmostEqual(d['RMSE'],d['RMSE_required_for_pooled_R2_05'])

    def test_joint_permutation_preserves_relationships_inside_block(self):
        class Recorder:
            def __init__(self): self.seen=[]
            def predict(self,X):
                self.seen.append(X.copy())
                return X.a.to_numpy()
        X=pd.DataFrame({'a':[1.,2.,3.,4.],'b':[10.,20.,30.,40.],
                        'unchanged':[8.,9.,10.,11.]},index=[30,40,70,90])
        original=X.copy(deep=True); model=Recorder()
        values=self.ns['joint_permutation'](model,X,X.a,['a','b'],np.random.default_rng(42),3)
        self.assertEqual(len(values),3)
        for observed in model.seen:
            np.testing.assert_allclose(observed.b,10*observed.a)
            np.testing.assert_array_equal(observed.unchanged,X.unchanged)
        pd.testing.assert_frame_equal(X,original)

    def test_group_bootstrap_uses_clusters_and_is_reproducible(self):
        frame=pd.DataFrame({'group':['a']*50+['b']*2,'gain':[1.]*50+[-3.]*2})
        first=self.ns['paired_group_bootstrap'](frame,2000,42)
        second=self.ns['paired_group_bootstrap'](pd.concat([frame,frame]),2000,42)
        self.assertEqual(first['groups'],2)
        self.assertAlmostEqual(first['group_bootstrap_low'],-3.)
        self.assertAlmostEqual(first['group_bootstrap_high'],1.)
        for key in first: self.assertAlmostEqual(first[key],second[key])

    def test_extra_features_do_not_change_target_eligibility(self):
        frame=pd.DataFrame({'in_strict13':[True,True,False],
                            'yield_strength':[10.,20.,30.],
                            'Ni':[np.nan,np.nan,1.],'Cr':[np.nan]*3,'Mo':[np.nan]*3})
        eligible=self.ns['eligible_rows'](frame,'yield_strength')
        self.assertEqual(list(eligible.index),[0,1])
        for schema in ['A0_11','A1_13','A1b_16']:
            features=self.ns['case_features']('charpy_J',schema)
            self.assertIn('charpy_temp_C',features)
            self.assertFalse(set(features)&{'yield_strength','uts','elongation','charpy_J','group'})
        model=self.ns['make_case']('ridge','yield_strength','A1b_16','median')
        self.assertEqual(model.named_steps['preprocess'].num_cols,self.ns['CORE16'])
        self.assertEqual(model.named_steps['preprocess'].method,'median')

    def test_local_tree_contributions_reconstruct_predictions(self):
        # Independent numerical invariant for the attribution shown to the reader.
        from sklearn.ensemble import RandomForestRegressor
        X=np.random.default_rng(7).normal(size=(30,4))
        y=3*X[:,0]**2-2*X[:,1]+X[:,2]*X[:,3]
        forest=RandomForestRegressor(n_estimators=9,max_depth=4,
                                     min_samples_leaf=2,random_state=42).fit(X,y)
        base,contributions=self.ns['forest_path_contributions'](forest,X)
        self.assertEqual(contributions.shape,X.shape)
        np.testing.assert_allclose(base+contributions.sum(axis=1),forest.predict(X),
                                   rtol=1e-10,atol=1e-8)


if __name__=='__main__': unittest.main()
