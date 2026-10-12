"""Group boundaries of supervised exports and inductive pools in notebook 06."""
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


class GroupedExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code={'__name__':'__main__'}
        n=json.loads((ROOT/'notebooks/06_grouped_exports.ipynb').read_text())
        for i,c in enumerate(n['cells']):
            if 'definitions' in c.get('metadata',{}).get('tags',[]):
                exec(compile(''.join(c['source']),f'grouped:cell{i}','exec'),cls.code)

    def frame(self):
        n=120; g=np.repeat(np.arange(20),6)
        frame=pd.DataFrame({'raw_row_id':np.arange(n),'group':[f'g{i}' for i in g],
            'in_strict13':True,'is_duplicate_excess':False,'outer_fold':g%5,
            'uts':np.linspace(400.,800.,n),'charpy_J':np.linspace(20.,100.,n),
            'charpy_temp_C':np.linspace(-100.,20.,n)})
        frame.loc[3::6,['uts','charpy_J','charpy_temp_C']]=np.nan
        for outer in range(5):
            frame[f'inner_fold_when_outer{outer}']=np.where(g%5==outer,-1,g%3)
        return frame

    def test_inductive_pools_exclude_all_groups_held_out_at_either_level(self):
        frame=self.frame()
        for outer in range(5):
            for inner in [None,0,1,2]:
                tr,pool,va=self.code['grouped_access'](frame,'uts',outer,inner)
                held=set(frame.loc[frame.outer_fold==outer,'group'])
                if inner is not None:
                    held.update(frame.loc[frame[f'inner_fold_when_outer{outer}']==inner,'group'])
                self.assertTrue(set(tr.group).isdisjoint(held))
                self.assertTrue(set(pool.group).isdisjoint(held))
                self.assertTrue(pool.uts.isna().all())
                self.assertTrue(tr.uts.notna().all() and va.uts.notna().all())
        broken=frame.copy()
        broken.loc[9,'group']=broken.loc[0,'group']  # Unlabeled train member of held-out group.
        with self.assertRaises(AssertionError):
            self.code['grouped_access'](broken,'uts',0)
        _,pool,_=self.code['grouped_access'](frame,'charpy_J',0)
        self.assertTrue(pool.empty)  # Unknown test conditions never create a pool.

    def test_full_refit_cv_uses_disjoint_groups_and_every_label_once(self):
        train=self.code['eligible_rows'](self.frame(),'uts')
        cv=self.code['grouped_full_splits'](train)
        seen=[]
        for tr,va in cv:
            self.assertTrue(set(train.iloc[tr].group).isdisjoint(train.iloc[va].group))
            seen.extend(va)
        self.assertEqual(sorted(seen),list(range(len(train))))


if __name__=='__main__':
    unittest.main()
