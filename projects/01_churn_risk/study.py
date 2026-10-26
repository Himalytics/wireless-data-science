"""A reproducible supervised-ML study on observed UCI telecom records.

Training is genuinely nested: outer evaluation -> calibration training ->
hyperparameter search. Identical conservative feature profiles remain grouped.
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

import hashlib
import io
import json
import math
import platform
import re
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
                             log_loss, precision_recall_curve, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
SOURCE_URL = "https://archive.ics.uci.edu/static/public/563/iranian+churn+dataset.zip"
SOURCE_PAGE = "https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset"
EXPECTED_SHA = "696c3a1812267980751f30d19193a1b430ac4ad76172bb089e664c96813ead66"
FEATURES = ["call_failure", "complains", "subscription_length", "charge_amount", "seconds_of_use",
            "frequency_of_use", "frequency_of_sms", "distinct_called_numbers", "age_group",
            "tariff_plan", "status", "age", "customer_value"]
CONSERVATIVE = [f for f in FEATURES if f not in ("status", "customer_value")]
SPECS = [("conservative", "logistic"), ("conservative", "gradient_boosting"),
         ("all", "logistic"), ("all", "gradient_boosting")]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=lambda x: x.item() if isinstance(x, np.generic) else str(x)) + "\n")


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def load_data():
    path = HERE / "data/raw/iranian_churn_uci563.zip"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
            path.write_bytes(response.read())
    raw = path.read_bytes()
    if checksum(raw) != EXPECTED_SHA:
        raise ValueError("Publisher bytes differ from the locked study input; investigate before reproducing this study")
    with zipfile.ZipFile(io.BytesIO(raw)) as source:
        df = pd.read_csv(source.open("Customer Churn.csv"))
    df.columns = [re.sub(r"\W+", "_", c.strip().lower()).strip("_") for c in df.columns]
    if list(df.columns) != FEATURES + ["churn"] or len(df) != 3150:
        raise ValueError("Unexpected source schema or row count")
    if df.isna().any().any() or not set(df.churn.unique()) <= {0, 1}:
        raise ValueError("Unexpected missing values or target classes")
    # A profile group is not a verified customer identifier.
    group_vectors = pd.Series(list(df[CONSERVATIVE].itertuples(index=False, name=None)))
    group_ids, _ = pd.factorize(group_vectors, sort=True)
    X = df[FEATURES].copy()
    X["__group"] = group_ids
    X["__row_id"] = np.arange(len(df))
    y = df.churn.astype(int).to_numpy()
    audit = {"source": SOURCE_PAGE, "download": SOURCE_URL, "license": "CC BY 4.0",
             "source_zip_sha256": checksum(raw), "rows": len(df), "predictors": len(FEATURES),
             "churn_labels": int(y.sum()), "nonchurn_labels": int((y == 0).sum()),
             "churn_prevalence": float(y.mean()), "exact_repeated_rows": int(df.duplicated().sum()),
             "repeated_full_predictor_rows": int(df[FEATURES].duplicated().sum()),
             "conservative_profile_groups": int(X.__group.nunique()),
             "conflicting_full_profile_groups": int(df.groupby(FEATURES, dropna=False).churn.nunique().gt(1).sum()),
             "conflicting_conservative_profile_groups": int(df.groupby(CONSERVATIVE, dropna=False).churn.nunique().gt(1).sum()),
             "row_policy": "All observations retained; no unverified duplicate-customer claim",
             "feature_policy": "Primary excludes status/customer_value as a conservative availability/construction sensitivity choice, not proof of leakage",
             "missing_cells": 0}
    return X, y, audit


def grouped_splits(X, y, folds=3, seed=42):
    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    splits = list(splitter.split(X, y, X["__group"].to_numpy()))
    for train, valid in splits:
        if set(X.iloc[train]["__group"]) & set(X.iloc[valid]["__group"]):
            raise AssertionError("Profile group crosses a validation boundary")
        if len(np.unique(np.asarray(y)[train])) != 2 or len(np.unique(np.asarray(y)[valid])) != 2:
            raise ValueError("A fold lacks one target class")
    return splits


def make_pipeline(feature_set, kind, seed=42):
    columns = CONSERVATIVE if feature_set == "conservative" else FEATURES
    categorical = [c for c in ("charge_amount", "age_group", "tariff_plan", "status") if c in columns]
    numeric = [c for c in columns if c not in categorical]
    preprocessing = ColumnTransformer([
        ("numeric", StandardScaler(), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ], remainder="drop")
    if kind == "logistic":
        estimator = LogisticRegression(max_iter=1500, solver="lbfgs", random_state=seed)
        grid = {"model__C": [0.1, 1.0, 10.0]}
    elif kind == "gradient_boosting":
        estimator = HistGradientBoostingClassifier(max_iter=120, learning_rate=0.08,
                       min_samples_leaf=20, early_stopping=False, random_state=seed)
        grid = {"model__max_leaf_nodes": [7, 15], "model__l2_regularization": [0.0, 2.0]}
    else:
        raise ValueError(kind)
    return Pipeline([("preprocessing", preprocessing), ("model", estimator)]), grid


class GroupTunedClassifier(ClassifierMixin, BaseEstimator):
    """Tune only within the data supplied by the enclosing calibration fold."""
    def __init__(self, feature_set="conservative", kind="logistic", random_state=42):
        self.feature_set = feature_set
        self.kind = kind
        self.random_state = random_state

    def fit(self, X, y):
        pipeline, grid = make_pipeline(self.feature_set, self.kind, self.random_state)
        splits = grouped_splits(X, y, 3, self.random_state)
        self.search_ = GridSearchCV(pipeline, grid, cv=splits, scoring="neg_brier_score",
                                    refit=True, n_jobs=1, error_score="raise")
        self.search_.fit(X, y)
        self.classes_ = np.array([0, 1])
        self.training_row_ids_ = X["__row_id"].to_numpy().copy()
        self.trace_ = {"training_rows": len(X), "training_profile_groups": int(X["__group"].nunique()),
                       "training_row_id_sha256": checksum(self.training_row_ids_.tobytes()),
                       "inner_splits": len(splits), "best_params": self.search_.best_params_,
                       "best_inner_brier": float(-self.search_.best_score_)}
        return self

    def predict_proba(self, X):
        return self.search_.predict_proba(X)

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


def fit_calibrated(X, y, feature_set, kind, seed=42):
    cv = grouped_splits(X, y, 3, seed)
    model = CalibratedClassifierCV(GroupTunedClassifier(feature_set, kind, seed),
                                  method="sigmoid", cv=cv, ensemble=True, n_jobs=1)
    model.fit(X, y)
    return model


def raw_ensemble_probability(model, X):
    # Matched base learners isolate recalibration from a change in ensemble composition.
    return np.mean([c.estimator.predict_proba(X)[:, 1] for c in model.calibrated_classifiers_], axis=0)


def metrics(y, p):
    p = np.asarray(p)
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Invalid probability output")
    return {"average_precision": float(average_precision_score(y, p)),
            "roc_auc": float(roc_auc_score(y, p)), "brier": float(brier_score_loss(y, p)),
            "log_loss": float(log_loss(y, p, labels=[0, 1])),
            "accuracy_at_0_5": float(((p >= 0.5).astype(int) == y).mean())}


def rank_indices(probability, row_ids, seed=42):
    # Ties cannot depend on observed target labels or source ordering.
    tie_keys = [checksum(f"{seed}:{int(i)}".encode()) for i in row_ids]
    return np.lexsort((np.asarray(tie_keys), -np.asarray(probability)))


def queue_result(y, p, row_ids, capacity):
    budget = max(1, int(math.ceil(len(y) * capacity)))
    chosen = rank_indices(p, row_ids)[:budget]
    positive = int(np.asarray(y)[chosen].sum())
    return {"requested_capacity": capacity, "reviewed": budget, "test_rows": len(y),
            "churn_labels_in_queue": positive, "total_churn_labels": int(np.sum(y)),
            "precision": positive / budget, "recall": positive / int(np.sum(y)),
            "random_expected_recall": budget / len(y),
            "risk_concentration_lift": (positive / budget) / float(np.mean(y)),
            "interpretation": "Observed label concentration, not prevented churn or causal retention uplift"}


def cluster_resamples(groups, repetitions=500, seed=20261026):
    groups = np.asarray(groups)
    unique = np.unique(groups)
    index = {g: np.flatnonzero(groups == g) for g in unique}
    rng = np.random.default_rng(seed)
    for _ in range(repetitions):
        yield np.concatenate([index[g] for g in rng.choice(unique, len(unique), replace=True)])


def bootstrap_intervals(y, probabilities, groups, repetitions=500):
    values = {name: {m: [] for m in ("average_precision", "brier", "roc_auc")} for name in probabilities}
    differences = []
    for idx in cluster_resamples(groups, repetitions):
        if len(np.unique(y[idx])) < 2:
            continue
        for name, p in probabilities.items():
            for metric, value in metrics(y[idx], p[idx]).items():
                if metric in values[name]:
                    values[name][metric].append(value)
        differences.append(brier_score_loss(y[idx], probabilities["conservative_gradient_boosting"][idx]) -
                           brier_score_loss(y[idx], probabilities["conservative_logistic"][idx]))
    intervals = {name: {metric: {"low": float(np.quantile(v, 0.025)), "high": float(np.quantile(v, 0.975))}
                        for metric, v in entry.items()} for name, entry in values.items()}
    paired = {"comparison": "Conservative gradient boosting minus conservative logistic Brier",
              "low": float(np.quantile(differences, 0.025)), "high": float(np.quantile(differences, 0.975)),
              "interpretation": "Negative favors boosting; interval conditional on fitted models and the held-out source sample"}
    return intervals, paired


def calibration_bins(y, p, n_bins=8):
    frame = pd.DataFrame({"y": y, "p": p})
    frame["bin"] = pd.cut(frame.p, np.linspace(0, 1, n_bins + 1), include_lowest=True, labels=False)
    table = frame.groupby("bin", observed=True).agg(n=("y", "size"), mean_probability=("p", "mean"), observed_fraction=("y", "mean"))
    return table.reset_index().to_dict("records")


def run():
    start = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    plan = json.loads((HERE / "experiment_plan.json").read_text())
    X, y, audit = load_data()
    development, test = grouped_splits(X, y, 5, plan["seed"])[0]
    Xdev, Xtest, ydev, ytest = X.iloc[development], X.iloc[test], y[development], y[test]
    outer = grouped_splits(Xdev, ydev, plan["outer_development_folds"], plan["seed"])
    oof = {"prior": np.full(len(development), np.nan)}
    raw_oof = {}
    trace = []
    assignments = pd.DataFrame({"row_id": X.__row_id, "profile_group": X.__group, "target": y,
                                 "split": "development", "outer_fold": -1})
    assignments.loc[test, "split"] = "test"
    for fold, (train, valid) in enumerate(outer):
        assignments.loc[development[valid], "outer_fold"] = fold
        oof["prior"][valid] = ydev[train].mean()
        for feature_set, kind in SPECS:
            name = f"{feature_set}_{kind}"
            oof.setdefault(name, np.full(len(development), np.nan))
            raw_oof.setdefault(name, np.full(len(development), np.nan))
            model = fit_calibrated(Xdev.iloc[train], ydev[train], feature_set, kind, plan["seed"])
            oof[name][valid] = model.predict_proba(Xdev.iloc[valid])[:, 1]
            raw_oof[name][valid] = raw_ensemble_probability(model, Xdev.iloc[valid])
            for submodel in model.calibrated_classifiers_:
                if set(submodel.estimator.training_row_ids_) & set(Xdev.iloc[valid].__row_id):
                    raise AssertionError("Outer validation rows entered model fitting")
                trace.append({"phase": "outer", "outer_fold": fold, "model": name, **submodel.estimator.trace_})
            print(f"Completed outer fold {fold + 1}/3: {name}", flush=True)
    dev_scores = {name: metrics(ydev, p) for name, p in oof.items()}
    eligible = ["prior", "conservative_logistic", "conservative_gradient_boosting"]
    selected = min(eligible, key=lambda name: dev_scores[name]["brier"])
    write_json(OUT / "selection_locked_before_test.json", {"eligible": eligible, "selected": selected,
               "selection_metric": "pooled development OOF Brier", "development_scores": dev_scores,
               "timestamp_utc": datetime.now(timezone.utc).isoformat()})
    probabilities = {"prior": np.full(len(test), ydev.mean())}
    raw_probabilities, fitted = {}, {}
    for feature_set, kind in SPECS:
        name = f"{feature_set}_{kind}"
        model = fit_calibrated(Xdev, ydev, feature_set, kind, plan["seed"])
        fitted[name] = model
        probabilities[name] = model.predict_proba(Xtest)[:, 1]
        raw_probabilities[name] = raw_ensemble_probability(model, Xtest)
        for submodel in model.calibrated_classifiers_:
            if set(submodel.estimator.training_row_ids_) & set(Xtest.__row_id):
                raise AssertionError("Final test rows entered model fitting")
            trace.append({"phase": "final", "model": name, **submodel.estimator.trace_})
        print(f"Fitted final development-only model: {name}", flush=True)
    test_scores = {name: metrics(ytest, p) for name, p in probabilities.items()}
    raw_scores = {name: metrics(ytest, p) for name, p in raw_probabilities.items()}
    intervals, paired = bootstrap_intervals(ytest, probabilities, Xtest.__group.to_numpy(), plan["bootstrap_iterations"])
    queues = {name: [queue_result(ytest, p, Xtest.__row_id, capacity) for capacity in plan["review_capacities"]]
              for name, p in probabilities.items()}
    cost_scenarios = []
    for fn_cost in (5, 10, 20):
        thresholds = np.linspace(0, 1, 101)
        costs = [np.sum((oof[selected] >= t) & (ydev == 0)) + fn_cost * np.sum((oof[selected] < t) & (ydev == 1)) for t in thresholds]
        threshold = float(thresholds[int(np.argmin(costs))])
        predicted = probabilities[selected] >= threshold
        fp, fn = int(np.sum(predicted & (ytest == 0))), int(np.sum(~predicted & (ytest == 1)))
        cost_scenarios.append({"false_positive_cost": 1, "false_negative_cost": fn_cost,
                               "development_selected_threshold": threshold, "test_false_positives": fp,
                               "test_false_negatives": fn, "test_normalized_cost": fp + fn_cost * fn,
                               "units": "Hypothetical normalized classification-cost units; not retention ROI"})
    slices = []
    for field in ("age_group", "tariff_plan"):
        for value in sorted(Xtest[field].unique()):
            mask = Xtest[field].to_numpy() == value
            yy, pp = ytest[mask], probabilities[selected][mask]
            slices.append({"field": field, "value": int(value), "n": int(mask.sum()), "churn_labels": int(yy.sum()),
                           "observed_prevalence": float(yy.mean()), "mean_probability": float(pp.mean()),
                           "brier": float(brier_score_loss(yy, pp)),
                           "adequate_support_for_comparison": bool(len(yy) >= 50 and yy.sum() >= 10 and (yy == 0).sum() >= 10)})
    curve_data = {}
    for name, p in probabilities.items():
        precision, recall, _ = precision_recall_curve(ytest, p)
        curve_data[name] = {"precision": precision.tolist(), "recall": recall.tolist(),
                            "calibration": calibration_bins(ytest, p)}
    if selected in raw_probabilities:
        curve_data["selected_uncalibrated"] = {"calibration": calibration_bins(ytest, raw_probabilities[selected])}
    order = rank_indices(probabilities[selected], Xtest.__row_id)
    cumulative = np.cumsum(ytest[order]) / ytest.sum()
    concentration = {"review_fraction": (np.arange(1, len(test) + 1) / len(test)).tolist(),
                     "fraction_of_churn_labels": cumulative.tolist()}
    predictions = pd.DataFrame({"row_id": Xtest.__row_id.to_numpy(), "profile_group": Xtest.__group.to_numpy(), "target": ytest,
                                 **probabilities, **{name + "_uncalibrated": p for name, p in raw_probabilities.items()}})
    predictions.to_csv(OUT / "test_predictions.csv", index=False, float_format="%.12g")
    pd.DataFrame({"row_id": Xdev.__row_id.to_numpy(), "target": ydev, **oof}).to_csv(OUT / "development_oof.csv", index=False, float_format="%.12g")
    assignments.to_csv(OUT / "split_assignments.csv", index=False)
    pd.DataFrame(slices).to_csv(OUT / "error_slices.csv", index=False)
    write_json(OUT / "data_audit.json", audit)
    write_json(OUT / "fit_trace.json", trace)
    write_json(OUT / "chart_data.json", {"model_curves": curve_data, "concentration": concentration})
    result = {"executed_at_utc": datetime.now(timezone.utc).isoformat(),
              "environment": {"python": platform.python_version(), "platform": platform.platform(),
                              "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__,
                              "scipy": scipy.__version__},
              "protocol_sha256": checksum((HERE / "experiment_plan.json").read_bytes()), "audit": audit,
              "split": {"development_rows": len(development), "test_rows": len(test), "development_churn_labels": int(ydev.sum()),
                        "test_churn_labels": int(ytest.sum()), "test_profile_groups": int(Xtest.__group.nunique()),
                        "profile_group_overlap": len(set(Xdev.__group) & set(Xtest.__group))},
              "selected_model": selected, "development_oof_metrics": dev_scores, "test_metrics": test_scores,
              "test_metric_intervals": intervals, "paired_brier_difference": paired,
              "matched_uncalibrated_test_metrics": raw_scores, "review_queues": queues,
              "hypothetical_cost_scenarios": cost_scenarios, "error_slices": slices,
              "fit_trace_entries": len(trace), "elapsed_seconds": round(time.monotonic() - start, 3),
              "interpretation_limits": ["Conditional bootstrap intervals do not capture all training or source-selection uncertainty",
                  "A lower Brier score is not by itself proof of better calibration",
                  "Review capture is not prevented churn or treatment uplift",
                  "No chronological, U.S. carrier, or employer performance claim",
                  "All-feature models are sensitivity analyses and did not select the primary model"]}
    write_json(OUT / "metrics.json", result)
    if selected in fitted:
        model_path = HERE / "artifacts/models/selected_model.joblib"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(fitted[selected], model_path, compress=3)
    print(json.dumps({"selected_model": selected, "test_metrics": test_scores, "elapsed_seconds": result["elapsed_seconds"]}), flush=True)
    return result
