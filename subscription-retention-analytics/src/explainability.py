"""
explainability.py
-----------------
SHAP-based explainability for churn prediction models.

Provides both global (population-level) and local (individual customer)
explanations. Uses model-supported language, not causal claims.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
import shap
import warnings
warnings.filterwarnings("ignore")


@dataclass
class GlobalExplanation:
    """Container for global model explanations."""
    feature_importance: pd.DataFrame  # mean |SHAP| per feature
    shap_values: np.ndarray           # SHAP values for all samples
    base_value: float                 # Expected model output (mean prediction)
    feature_names: list[str]


@dataclass
class LocalExplanation:
    """Container for individual customer explanation."""
    customer_id: str
    churn_probability: float
    risk_level: str                   # "Low", "Medium", "High", "Critical"
    top_drivers: list[dict]           # List of {feature, value, contribution, direction}
    shap_values: np.ndarray           # SHAP values for this customer
    base_value: float
    feature_names: list[str]


def create_explainer(model, X_background: pd.DataFrame, model_type: str = "tree"):
    """
    Create appropriate SHAP explainer for the model type.
    
    Args:
        model: Trained model (calibrated or base)
        X_background: Background dataset for expected values
        model_type: "tree" for RF, "linear" for LogReg, "auto" for auto-detect
        
    Returns:
        SHAP explainer object
    """
    if model_type == "tree" or model_type == "auto":
        # TreeExplainer works for Random Forest
        return shap.TreeExplainer(model)
    elif model_type == "linear":
        # LinearExplainer for Logistic Regression
        return shap.LinearExplainer(model, X_background)
    else:
        # Default to KernelExplainer (model-agnostic but slower)
        return shap.KernelExplainer(model.predict_proba, X_background)


def compute_global_shap(
    explainer,
    X: pd.DataFrame,
    max_samples: int = 500
) -> GlobalExplanation:
    """
    Compute global SHAP values for model interpretability.
    
    Uses a sample for efficiency (SHAP is computationally expensive).
    """
    # Sample for efficiency if large dataset
    if len(X) > max_samples:
        X_sample = X.sample(n=max_samples, random_state=42)
    else:
        X_sample = X
    
    shap_values = explainer.shap_values(X_sample)
    
    # Handle different output formats
    if isinstance(shap_values, list):
        # Binary classification: [class_0_shap, class_1_shap]
        shap_values_class1 = shap_values[1]
    else:
        shap_values_class1 = shap_values
    
    # Mean absolute SHAP per feature (global importance)
    mean_abs_shap = np.mean(np.abs(shap_values_class1), axis=0)
    feature_importance = pd.DataFrame({
        "feature": X_sample.columns,
        "mean_abs_shap": mean_abs_shap
    }).sort_values("mean_abs_shap", ascending=False)
    
    # Base value (expected model output)
    if hasattr(explainer, "expected_value"):
        base_value = explainer.expected_value
        if isinstance(base_value, (list, np.ndarray)):
            base_value = base_value[1] if len(base_value) > 1 else base_value[0]
    else:
        base_value = float(np.mean(shap_values_class1.sum(axis=1)))
    
    return GlobalExplanation(
        feature_importance=feature_importance,
        shap_values=shap_values_class1,
        base_value=float(base_value),
        feature_names=X_sample.columns.tolist()
    )


def compute_local_explanation(
    explainer,
    X_customer: pd.DataFrame,
    customer_id: str,
    churn_probability: float,
    risk_thresholds: tuple = (0.3, 0.5, 0.7),
    top_k: int = 5
) -> LocalExplanation:
    """
    Compute SHAP explanation for a single customer.
    
    Args:
        explainer: SHAP explainer
        X_customer: Single-row DataFrame with customer features
        customer_id: Customer identifier
        churn_probability: Model's predicted churn probability
        risk_thresholds: (low, medium, high) thresholds for risk levels
        top_k: Number of top drivers to return
        
    Returns:
        LocalExplanation with top contributing features
    """
    shap_values = explainer.shap_values(X_customer)
    
    if isinstance(shap_values, list):
        shap_values_class1 = shap_values[1][0]  # First (only) row, class 1
    else:
        shap_values_class1 = shap_values[0]
    
    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = base_value[1] if len(base_value) > 1 else base_value[0]
    
    # Create feature contribution dataframe
    contributions = pd.DataFrame({
        "feature": X_customer.columns,
        "feature_value": X_customer.iloc[0].values,
        "shap_value": shap_values_class1
    })
    
    # Sort by absolute contribution
    contributions["abs_shap"] = contributions["shap_value"].abs()
    contributions = contributions.sort_values("abs_shap", ascending=False)
    
    # Get top k drivers
    top_drivers = []
    for _, row in contributions.head(top_k).iterrows():
        direction = "increases" if row["shap_value"] > 0 else "decreases"
        top_drivers.append({
            "feature": row["feature"],
            "feature_value": row["feature_value"],
            "contribution": round(float(row["shap_value"]), 4),
            "direction": direction,
            "abs_contribution": round(float(row["abs_shap"]), 4)
        })
    
    # Determine risk level
    if churn_probability >= risk_thresholds[2]:
        risk_level = "Critical"
    elif churn_probability >= risk_thresholds[1]:
        risk_level = "High"
    elif churn_probability >= risk_thresholds[0]:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    return LocalExplanation(
        customer_id=customer_id,
        churn_probability=round(float(churn_probability), 4),
        risk_level=risk_level,
        top_drivers=top_drivers,
        shap_values=shap_values_class1,
        base_value=float(base_value),
        feature_names=X_customer.columns.tolist()
    )


def format_local_explanation_for_llm(local_exp: LocalExplanation) -> dict:
    """
    Format local explanation for GenAI consumption.
    
    Returns structured dict with only validated, model-supported information.
    """
    return {
        "customer_id": local_exp.customer_id,
        "churn_probability": local_exp.churn_probability,
        "risk_level": local_exp.risk_level,
        "top_model_drivers": [
            {
                "feature": d["feature"],
                "feature_value": d["feature_value"],
                "model_supported_contribution": d["contribution"],
                "direction": d["direction"]
            }
            for d in local_exp.top_drivers
        ],
        "base_value": local_exp.base_value,
        "note": "Contributions are model-supported (SHAP), not causal evidence."
    }


def get_feature_display_name(feature: str) -> str:
    """Convert technical feature name to human-readable form."""
    # Handle one-hot encoded features
    mappings = {
        "Contract_One year": "Contract: One year",
        "Contract_Two year": "Contract: Two year",
        "InternetService_Fiber optic": "Internet: Fiber optic",
        "InternetService_No": "Internet: No service",
        "PaymentMethod_Credit card (automatic)": "Payment: Credit card (auto)",
        "PaymentMethod_Electronic check": "Payment: Electronic check",
        "PaymentMethod_Mailed check": "Payment: Mailed check",
        "OnlineSecurity_Yes": "Online Security: Yes",
        "OnlineBackup_Yes": "Online Backup: Yes",
        "DeviceProtection_Yes": "Device Protection: Yes",
        "TechSupport_Yes": "Tech Support: Yes",
        "StreamingTV_Yes": "Streaming TV: Yes",
        "StreamingMovies_Yes": "Streaming Movies: Yes",
        "PhoneService_Yes": "Phone Service: Yes",
        "MultipleLines_No phone service": "Multiple Lines: No phone service",
        "MultipleLines_Yes": "Multiple Lines: Yes",
        "PaperlessBilling_Yes": "Paperless Billing: Yes",
        "gender_Male": "Gender: Male",
        "SeniorCitizen": "Senior Citizen",
        "Partner_Yes": "Partner: Yes",
        "Dependents_Yes": "Dependents: Yes",
        "tenure": "Tenure (months)",
        "MonthlyCharges": "Monthly Charges ($)",
        "charge_ratio": "Avg Monthly Charges Paid ($)",
        "tenure_x_monthly": "Tenure × Monthly Charges",
        "monthly_above_avg": "Above Avg Monthly Charge"
    }
    
    # Try exact match first
    if feature in mappings:
        return mappings[feature]
    
    # Try prefix match for one-hot encoded
    for prefix, display in mappings.items():
        if feature.startswith(prefix.replace(" ", "_").replace("(", "").replace(")", "")):
            return display
    
    # Default: clean up the feature name
    return feature.replace("_", " ").title()


def summarize_global_drivers(global_exp: GlobalExplanation, top_n: int = 10) -> list[dict]:
    """Summarize top global drivers for reporting."""
    top = global_exp.feature_importance.head(top_n)
    return [
        {
            "rank": i + 1,
            "feature": format_feature_name(row["feature"]),
            "mean_abs_shap": round(row["mean_abs_shap"], 4)
        }
        for i, (_, row) in enumerate(top.iterrows())
    ]


def format_feature_name(feature: str) -> str:
    """Format feature name for display (alias for get_feature_display_name)."""
    return get_feature_display_name(feature)


if __name__ == "__main__":
    # Smoke test (requires trained model)
    print("Explainability module loaded. Requires trained model and SHAP.")
    print("Use create_explainer() -> compute_global_shap() -> compute_local_explanation()")