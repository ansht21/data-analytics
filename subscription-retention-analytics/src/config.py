"""Central configuration: paths and constants for the Subscription Retention
Intelligence pipeline. All modules import paths from here so the project can be
run from any working directory."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
RAW_DATA_PATH = DATA_DIR / "Telco_Customer_Churn.csv"

OUTPUT_DIR = ROOT / "outputs"
IMAGE_DIR = ROOT / "image"
MODEL_DIR = ROOT / "models"
GENAI_OUTPUT_DIR = OUTPUT_DIR / "genai"

for _d in (OUTPUT_DIR, IMAGE_DIR, MODEL_DIR, GENAI_OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --- reproducibility -------------------------------------------------------
RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# --- dataset contract ------------------------------------------------------
TARGET = "ChurnFlag"
CATEGORICAL_COLS = [
    "gender", "Partner", "Dependents", "PhoneService", "MultipleLines",
    "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies", "Contract",
    "PaperlessBilling", "PaymentMethod",
]
NUMERIC_COLS = ["SeniorCitizen", "tenure", "MonthlyCharges"]
ENGINEERED_COLS = ["charge_ratio", "tenure_x_monthly", "monthly_above_avg"]
# TotalCharges is deliberately EXCLUDED as a model feature: it is approximately
# tenure x MonthlyCharges (a near-duplicate of tenure). It is redrafted into the
# engineered features above. See README "Leakage policy".

# Attributes the GenAI copilot is allowed to see (dataset whitelist).
ALLOWED_ATTRIBUTES = CATEGORICAL_COLS + NUMERIC_COLS + ENGINEERED_COLS

# --- risk levels (probability bands, documented in README) ------------------
RISK_BANDS = [(0.0, 0.4, "Low"), (0.4, 0.7, "Medium"), (0.7, 1.01, "High")]
