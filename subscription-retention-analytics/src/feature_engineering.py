"""
feature_engineering.py
----------------------
Leakage-safe feature engineering for churn prediction.

All features are derived from account-state fields available at scoring time.
No feature uses information that would not be known at prediction time.
"""
from __future__ import annotations

import pandas as pd
import numpy as np


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add leakage-safe engineered features to the cleaned dataframe.
    
    Features:
    - charge_ratio: TotalCharges / (tenure + 1) = average monthly charge actually paid
      A rising bill over time is a churn signal.
    - tenure_x_monthly: tenure * MonthlyCharges = lifetime value interaction
    - monthly_above_avg: binary flag for premium plans (MonthlyCharges > mean)
    
    Args:
        df: Cleaned dataframe with TotalCharges, tenure, MonthlyCharges
        
    Returns:
        DataFrame with engineered features added
    """
    df = df.copy()
    
    # Average monthly charge actually paid (handles tenure=0 via +1)
    df["charge_ratio"] = df["TotalCharges"] / (df["tenure"] + 1)
    
    # Lifetime value interaction
    df["tenure_x_monthly"] = df["tenure"] * df["MonthlyCharges"]
    
    # Premium plan flag
    df["monthly_above_avg"] = (df["MonthlyCharges"] > df["MonthlyCharges"].mean()).astype(int)
    
    return df


def get_engineered_feature_names() -> list[str]:
    """Return names of engineered features for reference."""
    return ["charge_ratio", "tenure_x_monthly", "monthly_above_avg"]


def prepare_features_with_engineering(
    df: pd.DataFrame,
    target_col: str = "ChurnFlag"
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Full feature preparation pipeline:
    1. Add engineered features
    2. One-hot encode categoricals
    3. Return feature matrix and target
    
    This is the main entry point for modeling notebooks.
    """
    from .data_processing import get_feature_columns, get_numeric_columns
    
    # Add engineered features
    df = add_engineered_features(df)
    
    cat_cols = get_feature_columns()
    num_cols = get_numeric_columns() + get_engineered_feature_names()
    
    available_cats = [c for c in cat_cols if c in df.columns]
    available_nums = [c for c in num_cols if c in df.columns]
    
    X = pd.get_dummies(
        df[available_cats + available_nums],
        columns=available_cats,
        drop_first=True
    )
    y = df[target_col]
    
    return X, y


def get_feature_groups() -> dict[str, list[str]]:
    """
    Return feature groups for interpretability.
    Useful for SHAP grouping and model inspection.
    """
    return {
        "contract": ["Contract_One year", "Contract_Two year"],
        "tenure": ["tenure"],
        "charges": ["MonthlyCharges", "charge_ratio", "tenure_x_monthly", "monthly_above_avg"],
        "internet_service": ["InternetService_Fiber optic", "InternetService_No"],
        "payment_method": [
            "PaymentMethod_Credit card (automatic)",
            "PaymentMethod_Electronic check",
            "PaymentMethod_Mailed check"
        ],
        "addon_services": [
            "OnlineSecurity_Yes", "OnlineBackup_Yes", "DeviceProtection_Yes",
            "TechSupport_Yes", "StreamingTV_Yes", "StreamingMovies_Yes"
        ],
        "demographics": ["gender_Male", "SeniorCitizen", "Partner_Yes", "Dependents_Yes"],
        "phone": ["PhoneService_Yes", "MultipleLines_No phone service", "MultipleLines_Yes"],
        "billing": ["PaperlessBilling_Yes"]
    }


if __name__ == "__main__":
    # Smoke test
    from data_processing import load_raw_data, clean_data
    df = clean_data(load_raw_data("data/Telco_Customer_Churn.csv"))
    df_fe = add_engineered_features(df)
    print(f"Engineered features added: {get_engineered_feature_names()}")
    print(f"charge_ratio stats: {df_fe['charge_ratio'].describe().round(2).to_dict()}")
    print(f"tenure_x_monthly stats: {df_fe['tenure_x_monthly'].describe().round(2).to_dict()}")
    print(f"monthly_above_avg dist: {df_fe['monthly_above_avg'].value_counts().to_dict()}")
    
    X, y = prepare_features_with_engineering(df_fe)
    print(f"Final feature matrix: {X.shape}")
    print("Feature engineering module OK")