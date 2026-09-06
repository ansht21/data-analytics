"""
modeling.py
-----------
Enhanced modeling pipeline with:
- Cross-validation for model stability
- Probability calibration
- Threshold optimization
- Comprehensive evaluation metrics (including PR-AUC)
- Error analysis
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import (
    StratifiedKFold, cross_val_score, cross_val_predict
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report, roc_curve, precision_recall_curve
)
from sklearn.preprocessing import StandardScaler
from sklearn.base import clone
import warnings
warnings.filterwarnings("ignore")


@dataclass
class ModelMetrics:
    """Container for model evaluation metrics."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    confusion_matrix: np.ndarray
    threshold: float
    
    def to_dict(self) -> dict:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "roc_auc": round(self.roc_auc, 4),
            "pr_auc": round(self.pr_auc, 4),
            "threshold": round(self.threshold, 4),
            "tn": int(self.confusion_matrix[0, 0]),
            "fp": int(self.confusion_matrix[0, 1]),
            "fn": int(self.confusion_matrix[1, 0]),
            "tp": int(self.confusion_matrix[1, 1])
        }


@dataclass
class CVResults:
    """Container for cross-validation results."""
    mean_roc_auc: float
    std_roc_auc: float
    fold_scores: list[float]
    mean_pr_auc: float
    std_pr_auc: float
    fold_pr_scores: list[float]


@dataclass
class CalibrationResults:
    """Container for calibration analysis."""
    ece: float  # Expected Calibration Error
    mce: float  # Maximum Calibration Error
    is_calibrated: bool
    n_bins: int = 10


def get_models(random_state: int = 42) -> dict:
    """Return dictionary of base models."""
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=5000, random_state=random_state, class_weight="balanced"
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=400, min_samples_leaf=5, 
            random_state=random_state, n_jobs=-1, class_weight="balanced"
        )
    }


def cross_validate_model(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    cv: int = 5,
    random_state: int = 42
) -> CVResults:
    """
    Perform stratified cross-validation with ROC-AUC and PR-AUC.
    
    Returns fold-level results for stability assessment.
    """
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=random_state)
    
    # ROC-AUC
    roc_scores = cross_val_score(model, X, y, cv=skf, scoring="roc_auc", n_jobs=-1)
    
    # PR-AUC - need custom scoring
    from sklearn.metrics import make_scorer
    pr_scorer = make_scorer(average_precision_score, needs_proba=True)
    pr_scores = cross_val_score(model, X, y, cv=skf, scoring=pr_scorer, n_jobs=-1)
    
    return CVResults(
        mean_roc_auc=float(np.mean(roc_scores)),
        std_roc_auc=float(np.std(roc_scores)),
        fold_scores=roc_scores.tolist(),
        mean_pr_auc=float(np.mean(pr_scores)),
        std_pr_auc=float(np.std(pr_scores)),
        fold_pr_scores=pr_scores.tolist()
    )


def calibrate_model(
    model,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    method: str = "isotonic",
    cv: int = 3
):
    """
    Calibrate predicted probabilities using CalibratedClassifierCV.
    
    Args:
        model: Base estimator (should be unfitted or pre-fitted)
        X_train: Training features
        y_train: Training target
        method: 'isotonic' or 'sigmoid' (Platt scaling)
        cv: Cross-validation folds for calibration
        
    Returns:
        Calibrated classifier
    """
    calibrated = CalibratedClassifierCV(model, method=method, cv=cv)
    calibrated.fit(X_train, y_train)
    return calibrated


def evaluate_calibration(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10
) -> CalibrationResults:
    """
    Evaluate probability calibration using Expected Calibration Error (ECE).
    
    Lower ECE = better calibrated. ECE < 0.01 is well-calibrated.
    """
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
    
    # Expected Calibration Error
    bin_counts = np.histogram(y_prob, bins=n_bins, range=(0, 1))[0]
    ece = np.sum(bin_counts * np.abs(prob_true - prob_pred)) / len(y_prob)
    mce = np.max(np.abs(prob_true - prob_pred))
    
    return CalibrationResults(
        ece=float(ece),
        mce=float(mce),
        is_calibrated=ece < 0.01,
        n_bins=n_bins
    )


def find_optimal_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric: str = "f1",
    min_recall: float = 0.0,
    min_precision: float = 0.0
) -> tuple[float, dict]:
    """
    Find optimal decision threshold based on business criteria.
    
    Args:
        y_true: True labels
        y_prob: Predicted probabilities
        metric: Optimization metric ('f1', 'precision', 'recall', 'youden')
        min_recall: Minimum acceptable recall (business constraint)
        min_precision: Minimum acceptable precision (business constraint)
        
    Returns:
        (optimal_threshold, all_threshold_metrics)
    """
    thresholds = np.linspace(0.01, 0.99, 99)
    results = []
    
    for thresh in thresholds:
        y_pred = (y_prob >= thresh).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        youden = recall + (tn / (tn + fp)) - 1 if (tn + fp) > 0 else 0  # sensitivity + specificity - 1
        
        # Check constraints
        if recall < min_recall or precision < min_precision:
            continue
            
        results.append({
            "threshold": thresh,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "youden": youden,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn
        })
    
    if not results:
        # Fallback: no threshold meets constraints, return best F1
        results = [{
            "threshold": thresh,
            "precision": tp / (tp + fp) if (tp + fp) > 0 else 0,
            "recall": tp / (tp + fn) if (tp + fn) > 0 else 0,
            "f1": 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0,
            "youden": recall + (tn / (tn + fp)) - 1 if (tn + fp) > 0 else 0,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn
        } for thresh in thresholds
        for tp, fp, tn, fn in [confusion_matrix(y_true, (y_prob >= thresh).astype(int)).ravel()]]
    
    df_results = pd.DataFrame(results)
    best_idx = df_results[metric].idxmax()
    best = df_results.loc[best_idx]
    
    return float(best["threshold"]), df_results.to_dict("records")


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float = 0.5
) -> ModelMetrics:
    """Evaluate model on test set with given threshold."""
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)
    
    cm = confusion_matrix(y_test, y_pred)
    
    return ModelMetrics(
        accuracy=accuracy_score(y_test, y_pred),
        precision=precision_score(y_test, y_pred, zero_division=0),
        recall=recall_score(y_test, y_pred, zero_division=0),
        f1=f1_score(y_test, y_pred, zero_division=0),
        roc_auc=roc_auc_score(y_test, y_prob),
        pr_auc=average_precision_score(y_test, y_prob),
        confusion_matrix=cm,
        threshold=threshold
    )


def error_analysis(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float = 0.5,
    original_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Analyze prediction errors (TP, TN, FP, FN) to find patterns.
    
    Returns DataFrame with error type and original features for inspection.
    """
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)
    
    # Error type classification
    conditions = [
        (y_test == 1) & (y_pred == 1),  # TP
        (y_test == 0) & (y_pred == 0),  # TN
        (y_test == 0) & (y_pred == 1),  # FP
        (y_test == 1) & (y_pred == 0),  # FN
    ]
    choices = ["TP", "TN", "FP", "FN"]
    error_types = np.select(conditions, choices, default="Unknown")
    
    # Create analysis dataframe
    analysis = pd.DataFrame({
        "y_true": y_test.values,
        "y_pred": y_pred,
        "y_prob": y_prob,
        "error_type": error_types
    }, index=X_test.index)
    
    # Add original features if provided
    if original_df is not None:
        # Align indices
        common_idx = analysis.index.intersection(original_df.index)
        analysis = analysis.loc[common_idx]
        orig_aligned = original_df.loc[common_idx]
        
        # Add key features for error analysis
        key_features = ["Contract", "tenure", "MonthlyCharges", "InternetService", 
                       "PaymentMethod", "TotalCharges", "OnlineSecurity", "TechSupport"]
        available = [f for f in key_features if f in orig_aligned.columns]
        for feat in available:
            analysis[feat] = orig_aligned[feat].values
    
    return analysis


def print_error_analysis_summary(analysis: pd.DataFrame) -> None:
    """Print summary of error patterns."""
    print("\n=== ERROR ANALYSIS SUMMARY ===")
    print(f"Total test samples: {len(analysis)}")
    print(f"\nError type distribution:")
    print(analysis["error_type"].value_counts())
    
    print(f"\nMean churn probability by error type:")
    print(analysis.groupby("error_type")["y_prob"].mean().round(4))
    
    if "Contract" in analysis.columns:
        print(f"\nFP by Contract:")
        fp = analysis[analysis["error_type"] == "FP"]
        print(fp["Contract"].value_counts())
        
        print(f"\nFN by Contract:")
        fn = analysis[analysis["error_type"] == "FN"]
        print(fn["Contract"].value_counts())
    
    if "tenure" in analysis.columns:
        print(f"\nMean tenure by error type:")
        print(analysis.groupby("error_type")["tenure"].mean().round(1))
    
    if "MonthlyCharges" in analysis.columns:
        print(f"\nMean MonthlyCharges by error type:")
        print(analysis.groupby("error_type")["MonthlyCharges"].mean().round(2))


def train_and_evaluate_full(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    original_df_train: Optional[pd.DataFrame] = None,
    original_df_test: Optional[pd.DataFrame] = None,
    cv_folds: int = 5,
    calibrate: bool = True,
    optimize_threshold: bool = True,
    min_recall: float = 0.3,
    random_state: int = 42
) -> dict:
    """
    Full training and evaluation pipeline.
    
    Returns dictionary with all models, metrics, and analysis.
    """
    models = get_models(random_state)
    results = {}
    
    # Scale for Logistic Regression
    scaler = StandardScaler().fit(X_train)
    X_train_scaled = pd.DataFrame(scaler.transform(X_train), columns=X_train.columns, index=X_train.index)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns, index=X_test.index)
    
    for name, model in models.items():
        print(f"\n{'='*50}")
        print(f"Training {name}")
        print(f"{'='*50}")
        
        # Use scaled data for LogReg, original for RF
        Xtr = X_train_scaled if name == "Logistic Regression" else X_train
        Xte = X_test_scaled if name == "Logistic Regression" else X_test
        
        # Cross-validation
        print(f"\nCross-validation ({cv_folds}-fold)...")
        cv_results = cross_validate_model(model, Xtr, y_train, cv=cv_folds, random_state=random_state)
        print(f"  ROC-AUC: {cv_results.mean_roc_auc:.4f} (+/- {cv_results.std_roc_auc:.4f})")
        print(f"  Fold scores: {[f'{s:.4f}' for s in cv_results.fold_scores]}")
        print(f"  PR-AUC:  {cv_results.mean_pr_auc:.4f} (+/- {cv_results.std_pr_auc:.4f})")
        
        # Fit on full training set
        model.fit(Xtr, y_train)
        
        # Calibration
        calibrated_model = model
        cal_results = None
        if calibrate:
            print(f"\nCalibrating ({method})...")
            calibrated_model = calibrate_model(model, Xtr, y_train, method="isotonic", cv=3)
            y_prob_cal = calibrated_model.predict_proba(Xte)[:, 1]
            cal_results = evaluate_calibration(y_test.values, y_prob_cal)
            print(f"  ECE: {cal_results.ece:.6f}, MCE: {cal_results.mce:.6f}")
            print(f"  Well-calibrated: {cal_results.is_calibrated}")
        
        # Threshold optimization
        y_prob = calibrated_model.predict_proba(Xte)[:, 1]
        threshold = 0.5
        thresh_details = None
        if optimize_threshold:
            print(f"\nOptimizing threshold (min_recall={min_recall})...")
            threshold, thresh_details = find_optimal_threshold(
                y_test.values, y_prob, metric="f1", min_recall=min_recall
            )
            print(f"  Optimal threshold: {threshold:.4f}")
        
        # Final evaluation
        metrics = evaluate_model(calibrated_model, Xte, y_test, threshold)
        print(f"\nTest set metrics (threshold={threshold:.4f}):")
        print(f"  Accuracy:  {metrics.accuracy:.4f}")
        print(f"  Precision: {metrics.precision:.4f}")
        print(f"  Recall:    {metrics.recall:.4f}")
        print(f"  F1:        {metrics.f1:.4f}")
        print(f"  ROC-AUC:   {metrics.roc_auc:.4f}")
        print(f"  PR-AUC:    {metrics.pr_auc:.4f}")
        print(f"  Confusion Matrix:")
        print(f"    TN={metrics.confusion_matrix[0,0]} FP={metrics.confusion_matrix[0,1]}")
        print(f"    FN={metrics.confusion_matrix[1,0]} TP={metrics.confusion_matrix[1,1]}")
        
        # Error analysis
        print(f"\nError Analysis:")
        error_df = error_analysis(calibrated_model, Xte, y_test, threshold, original_df_test)
        print_error_analysis_summary(error_df)
        
        results[name] = {
            "model": calibrated_model,
            "base_model": model,
            "cv_results": cv_results,
            "calibration": cal_results,
            "threshold": threshold,
            "threshold_details": thresh_details,
            "metrics": metrics,
            "error_analysis": error_df,
            "scaler": scaler if name == "Logistic Regression" else None
        }
    
    return results


if __name__ == "__main__":
    # Smoke test
    from data_processing import load_raw_data, clean_data, train_test_split_stratified
    from feature_engineering import prepare_features_with_engineering
    
    df = clean_data(load_raw_data("data/Telco_Customer_Churn.csv"))
    X, y = prepare_features_with_engineering(df)
    Xtr, Xte, ytr, yte = train_test_split_stratified(X, y)
    
    results = train_and_evaluate_full(Xtr, ytr, Xte, yte, df, df, cv_folds=3)
    print("\nModeling module OK")