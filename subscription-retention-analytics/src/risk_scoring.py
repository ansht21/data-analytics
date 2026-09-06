"""
risk_scoring.py
---------------
Risk scoring, revenue-at-risk calculation, and threshold logic.

Revenue-at-risk is defined as: sum of (churn_probability * MonthlyCharges) per customer.
This is the mathematically correct expected value formulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd


@dataclass
class RevenueAtRiskResult:
    """Container for revenue-at-risk analysis."""
    total_customers: int
    total_monthly_revenue: float
    expected_monthly_revenue_at_risk: float
    high_risk_customers: int
    high_risk_revenue_at_risk: float
    risk_segmentation: pd.DataFrame  # Per-customer breakdown
    assumptions: list[str]
    limitations: list[str]


@dataclass
class ThresholdAnalysis:
    """Container for threshold optimization results."""
    optimal_threshold: float
    metric_used: str
    min_recall_constraint: float
    threshold_metrics: list[dict]
    business_rationale: str


def calculate_revenue_at_risk(
    df: pd.DataFrame,
    churn_probabilities: np.ndarray,
    monthly_charge_col: str = "MonthlyCharges",
    customer_id_col: str = "customerID"
) -> RevenueAtRiskResult:
    """
    Calculate expected revenue at risk using probability-weighted formulation.
    
    Definition: E[Revenue at Risk] = Σ (churn_probability_i * MonthlyCharges_i)
    
    This is the mathematically correct expected value, NOT just summing
    MonthlyCharges of already-churned customers.
    
    Args:
        df: DataFrame with customer data including MonthlyCharges
        churn_probabilities: Predicted churn probabilities (same length as df)
        monthly_charge_col: Column name for monthly charges
        customer_id_col: Column name for customer ID
        
    Returns:
        RevenueAtRiskResult with breakdown and documentation
    """
    df = df.copy()
    df["churn_probability"] = churn_probabilities
    df["expected_revenue_at_risk"] = df["churn_probability"] * df[monthly_charge_col]
    
    # Risk segmentation
    def risk_segment(prob):
        if prob >= 0.7:
            return "Critical"
        elif prob >= 0.5:
            return "High"
        elif prob >= 0.3:
            return "Medium"
        else:
            return "Low"
    
    df["risk_segment"] = df["churn_probability"].apply(risk_segment)
    
    # Per-customer breakdown
    risk_breakdown = df[[customer_id_col, monthly_charge_col, "churn_probability", 
                         "expected_revenue_at_risk", "risk_segment"]].copy()
    risk_breakdown.columns = [customer_id_col, "monthly_charges", "churn_probability",
                              "expected_revenue_at_risk", "risk_segment"]
    
    # Aggregate metrics
    total_customers = len(df)
    total_monthly_revenue = df[monthly_charge_col].sum()
    expected_monthly_revenue_at_risk = df["expected_revenue_at_risk"].sum()
    
    high_risk = df[df["churn_probability"] >= 0.5]
    high_risk_customers = len(high_risk)
    high_risk_revenue_at_risk = high_risk["expected_revenue_at_risk"].sum()
    
    assumptions = [
        "Churn probabilities are well-calibrated (validated via calibration curves)",
        "MonthlyCharges represents recurring monthly revenue per customer",
        "Churn probability is independent across customers",
        "Revenue at risk is calculated at monthly granularity",
        "No discounting or time-value adjustment applied"
    ]
    
    limitations = [
        "Expected value, not guaranteed loss - actual churn is binary per customer",
        "Assumes independence; correlation in churn (e.g., service outage) not modeled",
        "Does not account for retention intervention effects",
        "Based on single-point-in-time snapshot; no temporal dynamics",
        "MonthlyCharges may not reflect total customer lifetime value",
        "Probabilities from hold-out test; production drift not assessed"
    ]
    
    return RevenueAtRiskResult(
        total_customers=total_customers,
        total_monthly_revenue=round(float(total_monthly_revenue), 2),
        expected_monthly_revenue_at_risk=round(float(expected_monthly_revenue_at_risk), 2),
        high_risk_customers=high_risk_customers,
        high_risk_revenue_at_risk=round(float(high_risk_revenue_at_risk), 2),
        risk_segmentation=risk_breakdown,
        assumptions=assumptions,
        limitations=limitations
    )


def calculate_segment_revenue_at_risk(
    df: pd.DataFrame,
    churn_probabilities: np.ndarray,
    segment_cols: list[str],
    monthly_charge_col: str = "MonthlyCharges"
) -> pd.DataFrame:
    """
    Calculate revenue at risk by segment (e.g., Contract x InternetService).
    
    Args:
        df: Customer dataframe
        churn_probabilities: Predicted churn probabilities
        segment_cols: Columns to segment by
        monthly_charge_col: Monthly charges column
        
    Returns:
        DataFrame with segment-level revenue at risk
    """
    df = df.copy()
    df["churn_probability"] = churn_probabilities
    df["expected_revenue_at_risk"] = df["churn_probability"] * df[monthly_charge_col]
    
    seg = df.groupby(segment_cols, observed=True).agg(
        customers=(df.columns[0], "count"),
        avg_churn_probability=("churn_probability", "mean"),
        total_monthly_revenue=(monthly_charge_col, "sum"),
        expected_revenue_at_risk=("expected_revenue_at_risk", "sum")
    ).reset_index()
    
    seg["expected_revenue_at_risk"] = seg["expected_revenue_at_risk"].round(2)
    seg["avg_churn_probability"] = seg["avg_churn_probability"].round(4)
    seg = seg.sort_values("expected_revenue_at_risk", ascending=False)
    
    return seg


def get_risk_level(probability: float, thresholds: tuple = (0.3, 0.5, 0.7)) -> str:
    """Map probability to risk level."""
    if probability >= thresholds[2]:
        return "Critical"
    elif probability >= thresholds[1]:
        return "High"
    elif probability >= thresholds[0]:
        return "Medium"
    else:
        return "Low"


def score_customer_base(
    model,
    X: pd.DataFrame,
    df_original: pd.DataFrame,
    threshold: float = 0.5,
    scaler=None
) -> pd.DataFrame:
    """
    Score entire customer base and return enriched dataframe.
    
    Args:
        model: Trained (calibrated) model
        X: Feature matrix for all customers
        df_original: Original dataframe with customer attributes
        threshold: Decision threshold
        scaler: Optional scaler for Logistic Regression
        
    Returns:
        DataFrame with churn_probability, risk_level, predicted_churn
    """
    X_score = X.copy()
    if scaler is not None:
        X_score = pd.DataFrame(
            scaler.transform(X_score),
            columns=X_score.columns,
            index=X_score.index
        )
    
    churn_probs = model.predict_proba(X_score)[:, 1]
    predictions = (churn_probs >= threshold).astype(int)
    risk_levels = [get_risk_level(p) for p in churn_probs]
    
    result = df_original.copy()
    result["churn_probability"] = churn_probs
    result["predicted_churn"] = predictions
    result["risk_level"] = risk_levels
    result["expected_revenue_at_risk"] = churn_probs * result["MonthlyCharges"]
    
    return result


def threshold_analysis_report(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    thresholds: list[float] = None
) -> pd.DataFrame:
    """
    Generate comprehensive threshold analysis report.
    
    Returns DataFrame with metrics at each threshold.
    """
    if thresholds is None:
        thresholds = np.linspace(0.05, 0.95, 19)
    
    rows = []
    for thresh in thresholds:
        y_pred = (y_prob >= thresh).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        youden = recall + specificity - 1
        
        rows.append({
            "threshold": round(thresh, 3),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "specificity": round(specificity, 4),
            "f1": round(f1, 4),
            "youden_j": round(youden, 4),
            "n_predicted_churn": tp + fp,
            "n_predicted_retain": tn + fn
        })
    
    return pd.DataFrame(rows)


# Import needed for threshold_analysis_report
from sklearn.metrics import confusion_matrix


if __name__ == "__main__":
    # Smoke test
    print("Risk scoring module loaded.")
    print("Use calculate_revenue_at_risk() for probability-weighted revenue at risk.")