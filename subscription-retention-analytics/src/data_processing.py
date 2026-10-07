"""Data loading + cleaning. Mirrors the logic already validated in
Churn_EDA_Analysis.ipynb (cell 1) so existing results are preserved exactly:
  - TotalCharges contains blank strings -> coerce to numeric
  - the 11 blank TotalCharges rows are all tenure-0 brand-new customers -> dropped
  - ChurnFlag = 1 when Churn == "Yes"
No other transformation happens here; feature engineering lives in
feature_engineering.py and is fit on training data only where statistics apply.
"""
from __future__ import annotations

import pandas as pd

from config import RAW_DATA_PATH, TARGET


def load_raw(path=RAW_DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the documented cleaning rules. Returns a copy; validates results."""
    df = df.copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    # The only source of nulls: blank TotalCharges strings for tenure-0 customers.
    blanks = df["TotalCharges"].isna()
    assert blanks.isna().sum() == 0  # coercion never introduces NaN beyond blanks
    if blanks.any():
        assert (df.loc[blanks, "tenure"] == 0).all(), \
            "unexpected: TotalCharges blanks are not all tenure-0 customers"
    df = df.dropna(subset=["TotalCharges"]).reset_index(drop=True)

    assert df["customerID"].is_unique, "duplicate customer IDs after cleaning"
    df[TARGET] = (df["Churn"] == "Yes").astype(int)
    return df


def load_clean(path=RAW_DATA_PATH) -> pd.DataFrame:
    return clean(load_raw(path))
