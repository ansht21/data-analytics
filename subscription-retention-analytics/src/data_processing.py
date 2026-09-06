"""
data_processing.py
------------------
Consolidated data loading, cleaning, and validation for the
Subscription Retention Intelligence project.

Replaces ad-hoc cleaning in notebooks with a single, testable pipeline.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import numpy as np


@dataclass
class DataQualityReport:
    """Summary of data quality checks."""
    n_rows_raw: int
    n_rows_clean: int
    n_duplicates: int
    n_missing_totalcharges: int
    missing_totalcharges_all_tenure_zero: bool
    churn_rate: float
    class_balance: dict


def load_raw_data(path: str | Path) -> pd.DataFrame:
    """Load the raw Telco churn CSV."""
    return pd.read_csv(path)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply standard cleaning rules:
    - Verify unique customer IDs
    - Convert TotalCharges to numeric (blank -> NaN)
    - Drop rows with missing TotalCharges (all are tenure=0 new customers)
    - Create binary churn flag
    """
    df = df.copy()
    
    # Verify unique IDs
    assert df.customerID.is_unique, "Duplicate customer IDs found"
    
    # Convert TotalCharges, coercing blanks to NaN
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    
    # Drop rows with missing TotalCharges (brand-new tenure=0 customers)
    before = len(df)
    df = df.dropna(subset=["TotalCharges"]).copy()
    after = len(df)
    
    # Create binary target
    df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)
    
    return df


def validate_data(df: pd.DataFrame) -> DataQualityReport:
    """Run data quality checks and return a report."""
    raw_path = Path("data/Telco_Customer_Churn.csv")
    df_raw = pd.read_csv(raw_path) if raw_path.exists() else df
    
    n_missing_tc = df_raw["TotalCharges"].isna().sum() if "TotalCharges" in df_raw.columns else 0
    if n_missing_tc == 0:
        # Check for blank strings
        n_missing_tc = (df_raw["TotalCharges"] == "").sum() if "TotalCharges" in df_raw.columns else 0
    
    all_tenure_zero = False
    if n_missing_tc > 0 and "tenure" in df_raw.columns:
        all_tenure_zero = df_raw.loc[df_raw["TotalCharges"].isna() | (df_raw["TotalCharges"] == ""), "tenure"].eq(0).all()
    
    return DataQualityReport(
        n_rows_raw=len(df_raw),
        n_rows_clean=len(df),
        n_duplicates=df_raw.duplicated(subset=["customerID"]).sum() if "customerID" in df_raw.columns else 0,
        n_missing_totalcharges=int(n_missing_tc),
        missing_totalcharges_all_tenure_zero=all_tenure_zero,
        churn_rate=float(df["ChurnFlag"].mean()) if "ChurnFlag" in df.columns else 0.0,
        class_balance=df["ChurnFlag"].value_counts(normalize=True).round(3).to_dict() if "ChurnFlag" in df.columns else {}
    )


def get_feature_columns() -> list[str]:
    """Return the list of categorical columns for one-hot encoding."""
    return [
        "gender", "Partner", "Dependents", "PhoneService", "MultipleLines",
        "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection",
        "TechSupport", "StreamingTV", "StreamingMovies", "Contract",
        "PaperlessBilling", "PaymentMethod"
    ]


def get_numeric_columns() -> list[str]:
    """Return the list of numeric columns to keep as-is."""
    return ["SeniorCitizen", "tenure", "MonthlyCharges"]


def prepare_model_data(df: pd.DataFrame, target_col: str = "ChurnFlag") -> tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features and target for modeling.
    Applies one-hot encoding to categorical features.
    Does NOT apply feature engineering - that's separate.
    """
    cat_cols = get_feature_columns()
    num_cols = get_numeric_columns()
    
    # Select only columns that exist
    available_cats = [c for c in cat_cols if c in df.columns]
    available_nums = [c for c in num_cols if c in df.columns]
    
    feats = pd.get_dummies(
        df[available_cats + available_nums],
        columns=available_cats,
        drop_first=True
    )
    
    y = df[target_col]
    return feats, y


def train_test_split_stratified(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Stratified train/test split with fixed random state for reproducibility."""
    from sklearn.model_selection import train_test_split
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=random_state)


def standard_scale_fit(X_train: pd.DataFrame) -> tuple:
    """Fit StandardScaler on training data and return scaler + scaled train."""
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler().fit(X_train)
    X_train_scaled = pd.DataFrame(
        scaler.transform(X_train),
        columns=X_train.columns,
        index=X_train.index
    )
    return scaler, X_train_scaled


def standard_scale_transform(scaler, X: pd.DataFrame) -> pd.DataFrame:
    """Transform using fitted scaler."""
    return pd.DataFrame(
        scaler.transform(X),
        columns=X.columns,
        index=X.index
    )


if __name__ == "__main__":
    # Quick smoke test
    df = load_raw_data("data/Telco_Customer_Churn.csv")
    df_clean = clean_data(df)
    report = validate_data(df_clean)
    print(f"Clean shape: {df_clean.shape}")
    print(f"Churn rate: {report.churn_rate:.3f}")
    print(f"Class balance: {report.class_balance}")
    
    X, y = prepare_model_data(df_clean)
    print(f"Features: {X.shape[1]}")
    
    Xtr, Xte, ytr, yte = train_test_split_stratified(X, y)
    scaler, Xtr_s = standard_scale_fit(Xtr)
    Xte_s = standard_scale_transform(scaler, Xte)
    print(f"Train: {Xtr.shape}, Test: {Xte.shape}")
    print("Data processing module OK")