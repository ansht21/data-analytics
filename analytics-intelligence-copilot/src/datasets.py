"""Dataset registry + loaders for the Analytics Intelligence Copilot.

The agent reads the cleaned CSVs already committed in the sibling project
folders — no data is duplicated inside this project.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent

DATASETS: dict[str, dict] = {
    "supply": {
        "label": "Supply Chain Orders",
        "icon": "📦",
        "scale": "7,991 orders · 47 SKUs",
        "path": REPO_ROOT / "supply-chain-performance-analysis" / "data" / "Cleaned_Supplychain_Data.csv",
        "blurb": "P&L + fulfilment audit: $73.0M net revenue, delivery SLAs, discount-vs-margin, ABC classification.",
    },
    "uber": {
        "label": "Uber Trip Demand",
        "icon": "🚗",
        "scale": "35,000 trips",
        "path": REPO_ROOT / "uber-trip-demand-analysis" / "data" / "Uber_Cleaned_data.csv",
        "blurb": "Hourly demand, surge timing, airport revenue mix, vehicle-tier efficiency.",
    },
    "churn": {
        "label": "Customer Churn",
        "icon": "👥",
        "scale": "7,043 customers (7,032 after cleaning)",
        "path": REPO_ROOT / "subscription-retention-analytics" / "data" / "Telco_Customer_Churn.csv",
        "blurb": "Churn cohorts, revenue at risk, tenure decay, payment-method risk.",
    },
}


def _as_bool(series: pd.Series) -> pd.Series:
    """Normalise True/False/Yes/No/1/0 (bool or string) columns to bool."""
    if series.dtype == bool:
        return series
    mapping = {"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False}
    return (
        series.astype(str).str.strip().str.lower().map(mapping).fillna(False).astype(bool)
    )


def load_dataset(key: str) -> pd.DataFrame:
    """Load + lightly normalise one dataset.

    Raises FileNotFoundError if the sibling CSV is missing, KeyError on bad key.
    """
    if key not in DATASETS:
        raise KeyError(f"Unknown dataset '{key}'. Choose from {sorted(DATASETS)}.")
    df = pd.read_csv(DATASETS[key]["path"])
    if key == "supply":
        df["late"] = ~_as_bool(df["on_time"])
    elif key == "uber":
        df["is_airport"] = _as_bool(df["Is_Airport_Trip"])
        df["Hour"] = pd.to_numeric(df["Hour"], errors="coerce")
    elif key == "churn":
        df["churned"] = df["Churn"].astype(str).str.strip().str.lower() == "yes"
        df["MonthlyCharges"] = pd.to_numeric(df["MonthlyCharges"], errors="coerce")
        df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    return df


def dataset_kpis(key: str, df: pd.DataFrame) -> list[tuple[str, str]]:
    """Four headline KPI cards per dataset — each returns (label, formatted value)."""
    if key == "supply":
        return [
            ("Net revenue", f"${df['revenue'].sum() / 1e6:.1f}M"),
            ("Profit", f"${df['profit'].sum() / 1e6:.1f}M"),
            ("Late orders", f"{df['late'].mean() * 100:.1f}%"),
            ("Avg delivery", f"{df['delivery_days'].mean():.1f} days"),
        ]
    if key == "uber":
        airport_share = df.loc[df["is_airport"], "Fare_Amount"].sum() / df["Fare_Amount"].sum() * 100
        return [
            ("Trips", f"{len(df):,}"),
            ("Revenue", f"₹{df['Fare_Amount'].sum() / 1e5:.1f}L"),
            ("Avg fare", f"₹{df['Fare_Amount'].mean():.0f}"),
            ("Airport revenue", f"{airport_share:.1f}%"),
        ]
    monthly = df["MonthlyCharges"].sum()
    at_risk = (
        df.loc[
            (df["Contract"] == "Month-to-month") & (df["InternetService"] == "Fiber optic"),
            "MonthlyCharges",
        ].sum()
        / monthly
        * 100
    )
    return [
        ("Customers", f"{len(df):,}"),
        ("Churn rate", f"{df['churned'].mean() * 100:.1f}%"),
        ("Revenue at risk", f"{at_risk:.0f}%"),
        ("Avg tenure", f"{df['tenure'].mean():.0f} mo"),
    ]
