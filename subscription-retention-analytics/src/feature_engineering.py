"""Feature engineering — identical definitions to Churn_Prediction_Analysis.ipynb
(cells 3) so existing model results remain comparable, but refactored into a
fit/transform class so the same statistics (monthly-charge average) are learned
on TRAINING data only and reused everywhere (train, test, app, SHAP, copilot).

Leakage policy (unchanged from the existing notebook):
  - raw TotalCharges is excluded: it approximates tenure x MonthlyCharges
  - charge_ratio       = TotalCharges / (tenure + 1)  -> avg monthly charge paid
  - tenure_x_monthly   = tenure * MonthlyCharges      -> lifetime-value proxy
  - monthly_above_avg  = MonthlyCharges > train-mean   -> premium flag (fit on train)
Categoricals are one-hot encoded with drop_first=True (same as notebook).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import CATEGORICAL_COLS, ENGINEERED_COLS, NUMERIC_COLS, TARGET

FEATURE_COLUMNS = (
    [f"{c}_{v}" for c in CATEGORICAL_COLS for v in ()]  # placeholder, set in fit
    + NUMERIC_COLS + ENGINEERED_COLS
)


class FeatureBuilder:
    """fit() on training data, transform() anywhere (train/test/new customer)."""

    def __init__(self) -> None:
        self.monthly_mean_: float | None = None
        self.dummy_columns_: list[str] | None = None
        self.feature_columns_: list[str] | None = None

    def fit(self, df: pd.DataFrame) -> "FeatureBuilder":
        self.monthly_mean_ = float(df["MonthlyCharges"].mean())
        dummies = pd.get_dummies(
            df[CATEGORICAL_COLS + NUMERIC_COLS], columns=CATEGORICAL_COLS,
            drop_first=True,
        )
        self.dummy_columns_ = list(dummies.columns)
        self.feature_columns_ = self.dummy_columns_ + ENGINEERED_COLS
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.monthly_mean_ is None or self.dummy_columns_ is None:
            raise RuntimeError("FeatureBuilder.fit must be called before transform")
        dummies = pd.get_dummies(
            df[CATEGORICAL_COLS + NUMERIC_COLS], columns=CATEGORICAL_COLS,
            drop_first=True,
        ).reindex(columns=self.dummy_columns_, fill_value=0)
        dummies = dummies.astype(float)

        feats = dummies.copy()
        feats["charge_ratio"] = df["TotalCharges"] / (df["tenure"] + 1)
        feats["tenure_x_monthly"] = df["tenure"] * df["MonthlyCharges"]
        feats["monthly_above_avg"] = (df["MonthlyCharges"] > self.monthly_mean_).astype(float)

        # Feature columns must not contain the target or identifiers.
        assert TARGET not in feats.columns and "customerID" not in feats.columns
        return feats[self.feature_columns_]

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)
