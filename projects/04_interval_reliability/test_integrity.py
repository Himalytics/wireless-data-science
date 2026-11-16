import hashlib
import json
import unittest

import numpy as np
import pandas as pd

from run import ROOT, PLAN, evaluate, load_weekly, radius, stream


class Integrity(unittest.TestCase):
    def test_finite_rank_and_boundaries(self):
        self.assertEqual(radius(np.arange(52), .2), 42)
        weekly = load_weekly()
        self.assertEqual(len(weekly), 462)
        self.assertEqual(weekly.sum(), 1280589)

    def test_no_future_features_or_feedback(self):
        weekly = load_weekly()
        for lag in (0, 2):
            frame = evaluate(weekly, .01, lag=lag)
            self.assertTrue((frame.latest_score_available <= frame.origin).all())
            self.assertTrue((frame.latest_feature_week + pd.Timedelta(weeks=lag+1) == frame.origin).all())
            self.assertTrue((frame.target-frame.origin == pd.to_timedelta(frame.horizon-1, unit="W")).all())

    def test_future_perturbation(self):
        weekly = load_weekly()
        issue = pd.Timestamp("2026-04-06")
        changed = weekly.copy()
        changed.loc[issue:] += 999999
        for horizon in PLAN["horizons"]:
            columns = ["origin", "point", "lower", "upper", "alpha_used"]
            left = stream(weekly, horizon, "adaptive", .01)
            right = stream(changed, horizon, "adaptive", .01)
            pd.testing.assert_frame_equal(left.loc[left.origin <= issue, columns], right.loc[right.origin <= issue, columns])

    def test_score_and_pairing(self):
        results = pd.read_csv(ROOT / "results/predictions.csv")
        self.assertFalse(results.duplicated(["target", "horizon", "method"]).any())
        self.assertTrue(results.groupby(["target", "horizon"]).size().eq(3).all())
        self.assertTrue(results.groupby(["horizon", "method"]).size().eq(54).all())
        error = np.maximum(results.lower-results.actual, 0) + np.maximum(results.actual-results.upper, 0)
        np.testing.assert_allclose(results.score, results.upper-results.lower+10*error)
        self.assertTrue((results.covered == results.actual.between(results.lower, results.upper)).all())

    def test_selection_and_figures(self):
        selected = json.loads((ROOT / "results/selection.json").read_text())
        self.assertEqual(selected["gain"], pd.read_csv(ROOT / "results/development.csv").iloc[0].gain)
        self.assertEqual(selected["latest_development_target_exclusive"], "2025-10-06")
        manifest = json.loads((ROOT / "results/execution.json").read_text())
        for name, expected in manifest["figure_hashes"].items():
            self.assertEqual(hashlib.sha256((ROOT/"results"/name).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
