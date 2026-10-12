"""COREG local update, transfer, leakage boundaries and serialization."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

ROOT=Path(__file__).resolve().parents[1]


class COREGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code={'__name__':'__main__'}
        n=json.loads((ROOT/'notebooks/07_coreg.ipynb').read_text())
        for i,c in enumerate(n['cells']):
            if 'definitions' in c.get('metadata',{}).get('tags',[]):
                exec(compile(''.join(c['source']),f'coreg:cell{i}','exec'),cls.code)

    def test_vectorized_local_gains_equal_explicit_temporary_refits_with_ties(self):
        rng=np.random.default_rng(19)
        for metric in ['cityblock','euclidean']:
            points=rng.integers(-3,4,size=(14,3)).astype(float)
            D=cdist(points,points,metric)
            active=np.arange(len(points))<8
            active[10]=True  # An already-added pseudo-label belongs to current Lj.
            labels=rng.normal(size=14);candidates=np.array([8,9,11,12,13]);k=3
            gains,estimates,omega=self.code['local_candidate_gains'](D,active,labels,candidates,k)
            refs=np.flatnonzero(active).tolist()

            def prediction(query,references,values):
                neighbors=sorted(references,key=lambda r:(D[query,r],r))[:k]
                return np.mean([values[r] for r in neighbors])

            for j,u in enumerate(candidates):
                expected_neighbors=sorted(refs,key=lambda r:(D[u,r],r))[:k]
                self.assertEqual(omega[j].tolist(),expected_neighbors)
                estimate=prediction(u,refs,labels)
                revised=labels.copy();revised[u]=estimate
                gain=sum((labels[q]-prediction(q,refs,labels))**2-
                    (labels[q]-prediction(q,refs+[int(u)],revised))**2 for q in expected_neighbors)
                self.assertAlmostEqual(estimates[j],estimate)
                self.assertAlmostEqual(gains[j],gain,places=12)

    def test_pseudo_labels_cross_to_other_regressor_once_with_positive_gain(self):
        rng=np.random.default_rng(7)
        X=rng.normal(size=(20,3));y=rng.normal(size=20);U=rng.normal(size=(15,3))
        m=self.code['COREGRegressor'](3,max_iter=10,pool_size=15,random_state=42).fit(X,y,U)
        self.assertGreater(m.n_pseudo_,0)
        self.assertLessEqual(m.n_pseudo_,20)
        ids=[r['raw_row_id'] for r in m.pseudo_labels_]
        self.assertEqual(len(ids),len(set(ids)))
        for row in m.pseudo_labels_:
            destination=row['destination']-1;source=row['source']-1
            self.assertNotEqual(source,destination)
            self.assertGreater(row['local_gain'],m.gain_threshold_)
            self.assertIn(row['raw_row_id'],m.model_raw_ids_[destination])
            self.assertNotIn(row['raw_row_id'],m.model_raw_ids_[source])
            j=np.flatnonzero(m.model_raw_ids_[destination]==row['raw_row_id'])[0]
            self.assertAlmostEqual(m.y_models_[destination][j],row['pseudo_y'])
        again=self.code['COREGRegressor'](3,max_iter=10,pool_size=15,random_state=42).fit(X,y,U)
        self.assertEqual(m.pseudo_labels_,again.pseudo_labels_)
        np.testing.assert_allclose(m.predict(U),again.predict(U))

    def test_no_pool_and_constant_labels_stop_and_unique_pool_keeps_lowest_raw_id(self):
        cls=self.code['COREGRegressor']
        X=np.arange(12.).reshape(6,2);y=np.ones(6)
        empty=cls(3).fit(X,y)
        self.assertEqual(empty.n_pseudo_,0)
        self.assertEqual(empty.stop_reason_,'no_eligible_pool')
        U=np.array([[.1,.2],[.1,.2],X[0],[20.,21.]])
        m=cls(3).fit(X,y,U,train_ids=np.arange(6),pool_ids=[101,100,102,103])
        self.assertEqual(m.pool_usable_n_,2)
        self.assertEqual(set(m.dropped_pool_ids_),{101,102})
        self.assertEqual(m.stop_reason_,'no_positive_gain_in_active_pool')
        np.testing.assert_allclose(m.predict(U),1.)
        with self.assertRaisesRegex(ValueError,'overlap'):
            cls(3).fit(X,y,U,train_ids=np.arange(6),pool_ids=[0,100,102,103])

    def test_context_preprocessing_learns_only_true_training_rows_and_exports(self):
        code=self.code;n=20
        frame=pd.DataFrame({c:np.linspace(.1,.9,n) for c in code['CORE16']})
        frame['pwht_temp_C']=0.;frame['pwht_time_h']=0.;frame['weld_process']='MMA'
        frame['raw_row_id']=np.arange(n);frame['uts']=np.linspace(400.,600.,n)
        train=frame.iloc[:10].copy();pool=frame.iloc[10:15].copy();valid=frame.iloc[15:].copy()
        pool['uts']=np.nan
        pool.loc[:,'Ni']=1000.;valid.loc[:,'Ni']=2000.
        ctx=code['prepare_context'](train,pool,valid,'uts')
        np.testing.assert_allclose(ctx['pre'].mu_,train[code['CORE16']].mean())
        altered=pool.copy();altered['uts']=1e9  # prepare_context only receives U inputs.
        again=code['prepare_context'](train,altered,valid,'uts')
        np.testing.assert_array_equal(ctx['U'],again['U'])
        model=code['fit_coreg'](ctx,3,42)
        pipeline=code['as_pipeline'](ctx['pre'],model)
        original=ctx['pre'].mu_.copy()
        pipeline.predict(valid[code['task_features']('uts')])
        np.testing.assert_array_equal(ctx['pre'].mu_,original)
        with tempfile.TemporaryDirectory() as tmp,patch.dict(code,{'VERSIONS':{'test':True}}):
            path=Path(tmp)/'coreg.pkl'
            code['dump_pipeline'](pipeline,path,{},valid[code['task_features']('uts')])
            with path.open('rb') as stream:loaded=code['cloudpickle'].load(stream)
            np.testing.assert_allclose(loaded.predict(valid),pipeline.predict(valid))

    def test_random_and_grouped_inner_access_exclude_outer_and_inner_validation(self):
        code=self.code;n=120;groups=np.repeat(np.arange(20),6)
        frame=pd.DataFrame({'raw_row_id':np.arange(n),'group':[f'g{i}' for i in groups],
            'in_strict13':True,'is_duplicate_excess':False,'outer_fold':groups%5,
            'uts':np.linspace(400.,800.,n)})
        frame.loc[3::6,'uts']=np.nan
        for o in range(5):frame[f'inner_fold_when_outer{o}']=np.where(groups%5==o,-1,groups%3)
        plan=code['build_random_plan'](frame,'uts')
        with patch.dict(code,{'data':frame,'random_plans':{'uts':plan}}):
            for protocol in ['random','grouped']:
                for outer in range(5):
                    for inner in range(3):
                        tr,u,va=code['access_frames'](protocol,'uts',outer,inner)
                        if protocol=='random':
                            held=set(plan.loc[(plan.outer_fold==outer)|
                                (plan[f'inner_fold_when_outer{outer}']==inner),'raw_row_id'])
                            self.assertTrue((set(tr.raw_row_id)|set(u.raw_row_id)).isdisjoint(held))
                        else:
                            held=set(frame.loc[(frame.outer_fold==outer)|
                                (frame[f'inner_fold_when_outer{outer}']==inner),'group'])
                            self.assertTrue((set(tr.group)|set(u.group)).isdisjoint(held))


if __name__=='__main__':unittest.main()
