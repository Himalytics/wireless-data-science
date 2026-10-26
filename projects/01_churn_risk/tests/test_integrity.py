"""Audit the released experiment against source records and saved predictions."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from study import (CONSERVATIVE, checksum, grouped_splits, load_data,
                   fit_calibrated, queue_result, rank_indices)


class ScientificIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.X, cls.y, cls.audit = load_data()
        cls.result = json.loads((HERE / "results/metrics.json").read_text())
        cls.assignments = pd.read_csv(HERE / "results/split_assignments.csv")
        cls.pred = pd.read_csv(HERE / "results/test_predictions.csv")
        cls.oof = pd.read_csv(HERE / "results/development_oof.csv")

    def test_input_and_protocol_identity(self):
        self.assertEqual(self.audit, self.result["audit"])
        self.assertEqual(checksum((HERE / "experiment_plan.json").read_bytes()), self.result["protocol_sha256"])
        np.testing.assert_array_equal(self.pred.target, self.y[self.pred.row_id])
        self.assertEqual(len(set(self.assignments.row_id)), 3150)

    def test_all_nested_group_boundaries(self):
        dev, holdout = grouped_splits(self.X, self.y, 5)[0]
        self.assertEqual(set(self.pred.row_id), set(holdout))
        self.assertFalse(set(self.X.iloc[dev]["__group"]) & set(self.X.iloc[holdout]["__group"]))
        Xdev, ydev = self.X.iloc[dev], self.y[dev]
        for train, valid in grouped_splits(Xdev, ydev):
            self.assertFalse(set(Xdev.iloc[train]["__group"]) & set(Xdev.iloc[valid]["__group"]))
            Xtrain, ytrain = Xdev.iloc[train], ydev[train]
            for fit, calibrate in grouped_splits(Xtrain, ytrain):
                self.assertFalse(set(Xtrain.iloc[fit]["__group"]) & set(Xtrain.iloc[calibrate]["__group"]))
                for inner_train, inner_valid in grouped_splits(Xtrain.iloc[fit], ytrain[fit]):
                    a, b = Xtrain.iloc[fit].iloc[inner_train], Xtrain.iloc[fit].iloc[inner_valid]
                    self.assertFalse(set(a["__group"]) & set(b["__group"]))

    def test_metrics_reproduce_from_predictions(self):
        for name, result in self.result["test_metrics"].items():
            p = self.pred[name].to_numpy()
            self.assertTrue(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all())
            self.assertAlmostEqual(float(np.mean((p - self.pred.target) ** 2)), result["brier"], places=10)
            self.assertAlmostEqual(average_precision_score(self.pred.target, p), result["average_precision"], places=10)
        for name, result in self.result["matched_uncalibrated_test_metrics"].items():
            self.assertAlmostEqual(brier_score_loss(self.pred.target, self.pred[name + "_uncalibrated"]), result["brier"], places=10)

    def test_selection_and_cost_thresholds_use_development_only(self):
        lock = json.loads((HERE / "results/selection_locked_before_test.json").read_text())
        briers = {name: brier_score_loss(self.oof.target, self.oof[name]) for name in lock["eligible"]}
        self.assertEqual(min(briers, key=briers.get), self.result["selected_model"])
        self.assertEqual(lock["selected"], self.result["selected_model"])
        selected = self.result["selected_model"]
        for row in self.result["hypothetical_cost_scenarios"]:
            thresholds = np.linspace(0, 1, 101)
            costs = [np.sum((self.oof[selected] >= t) & (self.oof.target == 0)) + row["false_negative_cost"] * np.sum((self.oof[selected] < t) & (self.oof.target == 1)) for t in thresholds]
            self.assertEqual(float(thresholds[int(np.argmin(costs))]), row["development_selected_threshold"])
            self.assertEqual(row["test_normalized_cost"], row["test_false_positives"] + row["false_negative_cost"] * row["test_false_negatives"])

    def test_queue_counts_and_label_independent_ties(self):
        for name, rows in self.result["review_queues"].items():
            for row in rows:
                actual = queue_result(self.pred.target.to_numpy(), self.pred[name].to_numpy(), self.pred.row_id, row["requested_capacity"])
                self.assertEqual(actual["churn_labels_in_queue"], row["churn_labels_in_queue"])
                self.assertEqual(actual["reviewed"], row["reviewed"])
        ids = self.pred.row_id.to_numpy()
        a = rank_indices(np.ones(len(ids)), ids)
        permutation = np.random.default_rng(17).permutation(len(ids))
        b = rank_indices(np.ones(len(ids)), ids[permutation])
        np.testing.assert_array_equal(ids[a], ids[permutation][b])

    def test_estimator_never_uses_tracking_columns_as_features(self):
        dev = self.assignments.query("split == 'development'").row_id.to_numpy()
        model = fit_calibrated(self.X.iloc[dev], self.y[dev], "conservative", "logistic")
        sample = self.X.iloc[dev[:20]].copy()
        original = model.predict_proba(sample)
        sample["__row_id"] = -999
        sample["__group"] = -333
        np.testing.assert_array_equal(original, model.predict_proba(sample))
        for calibrated in model.calibrated_classifiers_:
            columns = calibrated.estimator.search_.best_estimator_.named_steps["preprocessing"].transformers_
            used = set(columns[0][2]) | set(columns[1][2])
            self.assertEqual(used, set(CONSERVATIVE))


if __name__ == "__main__":
    unittest.main(verbosity=2)
