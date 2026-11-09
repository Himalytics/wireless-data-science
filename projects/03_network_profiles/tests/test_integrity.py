from pathlib import Path
import sys
import unittest
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from study import load_snapshot,aggregate,align,matrix
R=ROOT/'results'


class Integrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tiles,cls.context=load_snapshot()
        cls.p=pd.read_csv(R/'county_profiles.csv',dtype={'GEOID':str})
        cls.m=json.loads((R/'metrics.json').read_text())

    def test_source_identity_and_join(self):
        self.assertEqual(len(self.context),64)
        for f in self.tiles.values():
            self.assertTrue(f.quadkey.is_unique)
            self.assertTrue(f.GEOID.str.len().eq(5).all())
            self.assertTrue(f.GEOID.isin(self.context.GEOID).all())

    def test_aggregation_conservation_and_units(self):
        f=self.tiles['2025Q4'];a=aggregate(f)
        self.assertEqual(a.tests.sum(),f.tests.sum())
        geoid=a.index[0];g=f[f.GEOID==geoid]
        self.assertAlmostEqual(a.loc[geoid,'download_mbps'],np.sum(g.avg_d_kbps*g.tests)/g.tests.sum()/1000)
        self.assertTrue(a.loc[a.eligible].tiles.ge(5).all())

    def test_development_only_scaler(self):
        s=json.loads((R/'selection_locked_before_replication.json').read_text())
        d=aggregate(self.tiles['2025Q4']).query('eligible')
        np.testing.assert_allclose(matrix(d).mean(axis=0),s['scaler_mean'],rtol=1e-12)
        self.assertFalse(s['replication_used_for_selection'])
        self.assertEqual(s['protocol_sha256'],hashlib.sha256((ROOT/'experiment_plan.json').read_bytes()).hexdigest())

    def test_label_permutation_alignment(self):
        ref=np.array([0,0,1,1]);other=1-ref
        np.testing.assert_array_equal(align(ref,other,2),ref)
        self.assertEqual(adjusted_rand_score(ref,other),1.)

    def test_membership_and_support(self):
        cols=[c for c in self.p if c.startswith('bootstrap_profile_')]
        np.testing.assert_allclose(self.p[cols].sum(axis=1),1.)
        self.assertTrue(self.p.bootstrap_membership_frequency.between(0,1).all())
        self.assertEqual(len(pd.read_csv(R/'bootstrap_stability.csv')),200)
        self.assertEqual(int((self.p.bootstrap_membership_frequency>=.8).sum()),self.m['counties_membership_frequency_ge_0_8'])

    def test_temporal_metrics_recomputed(self):
        t=pd.read_csv(R/'temporal_assignments.csv')
        self.assertEqual(len(t),self.m['replication_common_counties'])
        self.assertAlmostEqual((t.profile==t.next_profile).mean(),self.m['replication_same_profile_fraction'])
        self.assertAlmostEqual(adjusted_rand_score(t.profile,t.next_profile),self.m['replication_ari'])
        match=pd.read_csv(R/'matched_tile_assignments.csv')
        self.assertAlmostEqual((match.matched_dev_profile==match.matched_next_profile).mean(),self.m['matched_tile_same_profile_fraction'])

    def test_selection_gate(self):
        s=pd.read_csv(R/'k_selection.csv');allowed=s[s.allowed].sort_values('silhouette',ascending=False)
        self.assertEqual(int(allowed.iloc[0].k),self.m['selected_k'])
        self.assertGreaterEqual(self.p.groupby('profile').size().min(),5)

    def test_figure_table_identity(self):
        d=json.loads((ROOT/'figures/provenance.json').read_text())
        for name,h in d['csv_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/'figures'/name).read_bytes()).hexdigest(),h)


if __name__=='__main__':unittest.main()
