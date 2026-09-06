"""
Preprocessing / feature-engineering tests. Reproducible, deterministic.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_processing import load_and_clean, add_tenure_band, UNAVAILABLE_CUSTOMER_FIELDS
from feature_engineering import build_features, build_target, customer_profile


@pytest.fixture(scope="session")
def df():
    d = load_and_clean(ROOT / "data" / "Telco_Customer_Churn.csv")
    return d


def test_cleaning_shape_and_unique_ids(df):
    assert df["customerID"].is_unique
    assert df["TotalCharges"].notna().all()
    assert set(df["ChurnFlag"].unique()) <= {0, 1}


def test_dropped_rows_only_those_with_missing_totalcharges(df):
    # Original dataset is 7043 rows; 11 have blank TotalCharges -> 7032 survive.
    raw = pd.read_csv(ROOT / "data" / "Telco_Customer_Churn.csv")
    assert len(raw) == 7043
    assert len(df) == 7032


def test_feature_columns(df):
    feats = build_features(df)
    assert "charge_ratio" in feats.columns
    assert "tenure_x_monthly" in feats.columns
    assert "monthly_above_avg" in feats.columns
    assert feats.shape[0] == len(df)


def test_target_shape(df):
    y = build_target(df)
    assert np.issubdtype(y.dtype, np.integer)
    assert y.mean() > 0.2  # ~26% churn


def test_customer_profile_allowed_fields(df):
    prof = customer_profile(df, df["customerID"].iloc[0])
    assert "TotalCharges" in prof
    assert "complaints" not in prof
    assert "satisfaction scores" not in prof