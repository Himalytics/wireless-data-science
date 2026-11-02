"""Checks mathematical and temporal properties, using the committed snapshot."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from study import features, interval, load_data, score


class ScientificIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pred = pd.read_csv(ROOT/'results/backtest_predictions.csv')
        cls.test = cls.pred[cls.pred.split=='test']
        cls.plan = json.loads((ROOT/'experiment_plan.json').read_text())
        cls.selection = json.loads((ROOT/'results/selection_locked_before_test.json').read_text())

    def test_audited_source_snapshot(self):
        w,d,a,_,_=load_data(snapshot=True)
        self.assertEqual(int(w.all_wireless.sum()),a['observed_complaints'])
        self.assertEqual(len(w),460)
        self.assertEqual(a['duplicate_ids_in_scope'],0)
        self.assertTrue((w.excluding_unwanted_calls<=w.all_wireless).all())

    def test_features_do_not_see_future(self):
        # Changing all values from origin onward cannot change the origin features.
        y=np.arange(200,dtype=float)+10
        dates=pd.date_range('2020-01-06',periods=200,freq='W-MON')
        alt=y.copy();alt[150:]=999999
        for h in [1,2,3,4]:
            np.testing.assert_array_equal(features(y,dates,h)[150-52],features(alt,dates,h)[150-52])

    def test_training_and_residual_boundaries(self):
        trace=pd.read_csv(ROOT/'results/training_trace.csv')
        self.assertTrue((trace.latest_training_target<trace.origin).all())
        self.assertTrue((trace.latest_feature_observation<trace.origin).all())
        valid=self.pred.dropna(subset=['latest_calibration_target'])
        self.assertTrue((valid.latest_calibration_target<valid.origin).all())
        for _,g in self.pred.groupby(['model','horizon']):
            for row in g.itertuples():
                n=min(int((g.target_index<row.target_index-row.horizon+1).sum()),26)
                self.assertEqual(row.calibration_n,n)

    def test_disjoint_final_forecast_targets(self):
        for _,g in self.test.groupby('model'):
            self.assertEqual(len(g),52)
            self.assertEqual(g.target_week.nunique(),52)
            self.assertEqual(g.origin.nunique(),13)
            self.assertEqual(g.groupby('horizon').size().tolist(),[13]*4)
            self.assertTrue((g.target_week>='2025-10-27').all())
        self.assertFalse(self.test[['prediction','lower80','upper80']].isna().any().any())

    def test_selection_uses_development_only(self):
        dev=score(self.pred[self.pred.split=='development'])
        self.assertEqual(dev.iloc[0].model,self.selection['selected_model'])
        ml=dev[~dev.model.isin(['recent_mean_4','seasonal_naive_52'])]
        self.assertEqual(ml.iloc[0].model,self.selection['selected_ml_candidate'])
        self.assertLess(self.selection['last_development_target'],self.selection['first_test_origin'])
        self.assertEqual(hashlib.sha256((ROOT/'experiment_plan.json').read_bytes()).hexdigest(),self.selection['protocol_sha256'])

    def test_metrics_independently_recomputed(self):
        recorded=pd.read_csv(ROOT/'results/test_metrics.csv').set_index('model')
        for name,g in self.test.groupby('model'):
            e=np.abs(g.actual-g.prediction)
            self.assertAlmostEqual(e.mean(),recorded.loc[name,'mae'],places=7)
            self.assertAlmostEqual(e.sum()/g.actual.sum(),recorded.loc[name,'wape'],places=9)
            coverage=((g.actual>=g.lower80)&(g.actual<=g.upper80)).mean()
            self.assertAlmostEqual(coverage,recorded.loc[name,'coverage80'],places=9)
            s=(g.upper80-g.lower80)+10*np.maximum(g.lower80-g.actual,0)+10*np.maximum(g.actual-g.upper80,0)
            self.assertAlmostEqual(s.mean(),recorded.loc[name,'interval_score80'],places=7)

    def test_interval_estimator_and_order(self):
        self.assertEqual(interval(100,list(range(12))),(None,None))
        lo,hi=interval(100,list(range(26)))
        self.assertEqual((lo,hi),(102.5,122.5))
        self.assertTrue((self.test.lower80<=self.test.upper80).all())
        self.assertTrue((self.test.lower80>=0).all())

    def test_figures_match_data(self):
        p=json.loads((ROOT/'figures/provenance.json').read_text())
        for name,digest in p['figures'].items():
            self.assertEqual(hashlib.sha256((ROOT/'figures'/name).read_bytes()).hexdigest(),digest)


if __name__=='__main__': unittest.main()
