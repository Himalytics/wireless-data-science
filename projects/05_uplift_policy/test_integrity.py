"""Frozen-output integrity tests, runnable without the large source download."""
import json
import unittest
import numpy as np
import pandas as pd
from source import ROOT, FEATURES, sha
from run import top, ipw, dr, interval

class Integrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=ROOT/'results'
        cls.p=pd.read_csv(cls.r/'predictions.csv.gz')
        cls.e=json.loads((cls.r/'experiment.json').read_text())

    def test_group_boundaries(self):
        s=pd.read_csv(self.r/'splits.csv.gz')
        self.assertFalse(s.row_id.duplicated().any())
        self.assertEqual(s.groupby('profile').split.nunique().max(),1)
        self.assertEqual(len(s),self.e['sample_rows'])
        np.testing.assert_array_equal(s.loc[s.split=='test','row_id'],self.p.row_id)

    def test_allowed_predictors_and_protocol_identity(self):
        protocol=json.loads((ROOT/'protocol.json').read_text())
        self.assertEqual(protocol['predictors'],FEATURES)
        self.assertTrue({'conversion','exposure','treatment'}.isdisjoint(FEATURES))
        self.assertEqual(sha(ROOT/'protocol.json'),self.e['protocol_sha256'])

    def test_source_identity(self):
        s=json.loads((self.r/'source.json').read_text())
        self.assertEqual(s['source_rows'],13979592)
        self.assertEqual(s['sha256'],'2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc')

    def test_selection_is_validation_only(self):
        s=pd.read_csv(self.r/'selection.csv')
        self.assertEqual(len(s),4)
        self.assertEqual(s.sort_values('validation_ipw_per_1000',ascending=False).iloc[0].model,self.e['selected_model'])

    def test_ipw_and_dr_algebra(self):
        np.testing.assert_allclose(ipw(np.array([1.,1.]),np.array([0.,1.]),.8),[-5,1.25])
        np.testing.assert_allclose(dr(np.array([1.,1.]),np.array([0.,1.]),.8,np.zeros(2),np.zeros(2)),[-5,1.25])
        w=ipw(self.p.visit,self.p.treatment,self.e['train_assignment_share'])
        np.testing.assert_allclose(w,self.p.ipw,atol=1e-8)

    def test_capacity_and_outcome_blind_ranking(self):
        self.assertEqual(int(self.p.policy_uplift_20.sum()),int(np.ceil(.2*len(self.p))))
        np.testing.assert_array_equal(top([.2,.5,.1,.4,.3],.4),[0,1,0,1,0])
        self.assertEqual(len(top([1,1,1],1)),3)

    def test_policy_values_and_paired_difference(self):
        table=pd.read_csv(self.r/'policies.csv').set_index('policy')
        v=self.p.policy_uplift_20*self.p.ipw*1000
        self.assertAlmostEqual(v.mean(),table.loc['uplift_20','incremental_per_1000'],places=6)
        pairs=pd.read_csv(self.r/'paired_comparisons.csv').set_index('comparator')
        for name,a in [('random_20',.2),('response_20',self.p.policy_response_20)]:
            self.assertAlmostEqual(((self.p.policy_uplift_20-a)*self.p.ipw*1000).mean(),pairs.loc[name,'difference_per_1000'],places=6)

    def test_profile_multiplier_reproducibility(self):
        x=np.array([1,2,4,8.]);g=np.array([0,0,1,2])
        # Small-group all-zero draws possible; real data has >200k clusters.
        a=interval(x,np.arange(4),reps=10)
        b=interval(x,np.arange(4),reps=10)
        np.testing.assert_array_equal(a,b)
        self.assertTrue(np.isfinite(a).all())
        c=interval(np.ones(100),np.arange(100),reps=20)
        np.testing.assert_allclose(c,1)

    def test_support_and_intervals(self):
        a=pd.read_csv(self.r/'audit.csv');self.assertTrue((a.visits<=a.n).all())
        self.assertEqual(int(a[a.split=='test'].n.sum()),len(self.p))
        for name in ['policies.csv','paired_comparisons.csv','capacity.csv','deciles.csv','sensitivity.csv']:
            t=pd.read_csv(self.r/name);self.assertTrue(np.isfinite(t[['low','high']]).all().all());self.assertTrue((t.low<=t.high).all())

    def test_executed_notebook(self):
        import nbformat
        notebook=nbformat.read(ROOT/'analysis.ipynb',as_version=4)
        cells=[c for c in notebook.cells if c.cell_type=='code']
        self.assertEqual(len(cells),7)
        self.assertEqual([c.execution_count for c in cells],list(range(1,8)))
        self.assertFalse(any(o.output_type=='error' for c in cells for o in c.outputs))

    def test_estimator_sensitivity_recomputed(self):
        score=dr(self.p.visit,self.p.treatment,self.e['train_assignment_share'],self.p.m0,self.p.m1)
        expected=((self.p.policy_uplift_20-.2)*score*1000).mean()
        actual=pd.read_csv(self.r/'sensitivity.csv').set_index('estimator').loc['DR','advantage_over_random']
        self.assertAlmostEqual(expected,actual,places=6)

if __name__=='__main__':unittest.main()
