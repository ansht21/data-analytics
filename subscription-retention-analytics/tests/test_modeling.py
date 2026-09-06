"""
Modeling, threshold, revenue-at-risk, and risk-band tests.
"""
import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import modeling as mdl
from data_processing import load_and_clean
from feature_engineering import build_features


@pytest.fixture(scope="session")
def df():
    return load_and_clean(ROOT / "data" / "Telco_Customer_Churn.csv")


@pytest.fixture(scope="session")
def splits(df):
    return mdl.make_splits(df)


def test_split_shapes(splits):
    assert len(splits["y_train"]) + len(splits["y_test"]) == 7032


def test_cross_validation_reports_mean_and_std(splits):
    cv = mdl.cross_validate(splits, cv_folds=3)
    assert {"cv_mean_roc_auc", "cv_std", "folds"}.issubset(cv.columns)
    assert cv["cv_std"].between(0, 0.2).all()


def test_risk_band_boundaries():
    assert mdl.risk_band(0.75) == "High"
    assert mdl.risk_band(0.70) == "High"
    assert mdl.risk_band(0.50) == "Medium"
    assert mdl.risk_band(0.40) == "Medium"
    assert mdl.risk_band(0.10) == "Low"


def test_threshold_is_input_range(splits):
    model = mdl.fit_models(splits)["Random Forest"]
    prob = model.predict_proba(splits["X_test"])[:, 1]
    thr = mdl.optimize_threshold(splits["y_test"].values, prob)
    assert 0 <= thr["cost_optimal"] <= 1
    assert thr["min_cost"] >= 0


def test_revenue_at_risk_expectation(df):
    df2 = df.copy()
    df2["churn_probability"] = 1.0  # all churn -> expected = actual monthly revenue of flagged
    df2["risk_level"] = "High"
    rav = mdl.revenue_at_risk(df2)
    assert rav["flagged_customers"] == len(df2)
    # expected at risk = sum(1.0 * MonthlyCharges)
    assert rid(rav["expected_monthly_revenue_at_risk"]) == rid(df2["MonthlyCharges"].sum())


def rid(x):
    return round(float(x), 2)


def test_revenue_at_risk_zero_probability():
    r = mdl.revenue_at_risk(pd.DataFrame({"churn_probability": [0.0, 0.0],
                                          "risk_level": ["Low", "Low"],
                                          "MonthlyCharges": [50, 60]}))
    assert r["expected_monthly_revenue_at_risk"] == 0.0