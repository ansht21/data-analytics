"""Shared fixtures: synthetic raw data + temp-path settings."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import pytest  # noqa: E402
import yaml  # noqa: E402
from src.config import load_settings  # noqa: E402

SYNTH_ROWS = [
    {"index": 0, "Order ID": "A1", "Date": "03-31-22", "Category": "T-shirt",
     "Status": "Shipped - Delivered to Buyer", "Amount": 100.0,
     "Fulfilment": "Amazon", "currency": "INR", "ship-state": "Maharashtra",
     "ship-city": "Mumbai", "ship-postal-code": 400001.0, "B2B": False,
     "fulfilled-by": None, "New": None, "PendingS": None},
    {"index": 1, "Order ID": "A2", "Date": "04-30-2022", "Category": "Shirt",
     "Status": "Cancelled", "Amount": None,
     "Fulfilment": "Merchant", "currency": None, "ship-state": " gujarat ",
     "ship-city": " Surat ", "ship-postal-code": None, "B2B": True,
     "fulfilled-by": "Easy Ship", "New": None, "PendingS": None},
    {"index": 2, "Order ID": "A3", "Date": "05-15-22", "Category": "T-shirt",
     "Status": "Shipped - Returned to Seller", "Amount": 250.5,
     "Fulfilment": "Amazon", "currency": "INR", "ship-state": "KARNATAKA",
     "ship-city": "Bengaluru", "ship-postal-code": 560001.0, "B2B": False,
     "fulfilled-by": None, "New": None, "PendingS": None},
    {"index": 3, "Order ID": "A4", "Date": "06-01-22", "Category": "Blaze",
     "Status": "Shipped - Lost in Transit", "Amount": 99.9,
     "Fulfilment": "Amazon", "currency": "INR", "ship-state": "Delhi",
     "ship-city": "Delhi", "ship-postal-code": 110001.0, "B2B": False,
     "fulfilled-by": None, "New": None, "PendingS": None},
    {"index": 4, "Order ID": "A5", "Date": "06-15-22", "Category": "T-shirt",
     "Status": "Shipped", "Amount": 150.0,
     "Fulfilment": "Merchant", "currency": "INR", "ship-state": "Punjab",
     "ship-city": "Ludhiana", "ship-postal-code": 141001.0, "B2B": False,
     "fulfilled-by": "Easy Ship", "New": None, "PendingS": None},
    {"index": 5, "Order ID": "A6", "Date": "06-29-22", "Category": "Shirt",
     "Status": "Shipped - Delivered to Buyer", "Amount": 300.0,
     "Fulfilment": "Amazon", "currency": "INR", "ship-state": "Tamil Nadu",
     "ship-city": "Chennai", "ship-postal-code": 600001.0, "B2B": False,
     "fulfilled-by": None, "New": None, "PendingS": None},
    {"index": 6, "Order ID": "A7", "Date": "06-29-22", "Category": "T-shirt",
     "Status": "Pending", "Amount": 0.0,
     "Fulfilment": "Amazon", "currency": "INR", "ship-state": None,
     "ship-city": None, "ship-postal-code": None, "B2B": False,
     "fulfilled-by": None, "New": None, "PendingS": None},
    {"index": 7, "Order ID": "A8", "Date": "04-05-22", "Category": "T-shirt",
     "Status": "Something New", "Amount": 42.0,
     "Fulfilment": "Amazon", "currency": "INR", "ship-state": "Goa",
     "ship-city": "Panaji", "ship-postal-code": 403001.0, "B2B": False,
     "fulfilled-by": None, "New": None, "PendingS": None},
]


@pytest.fixture
def raw_df() -> pd.DataFrame:
    """Synthetic raw frame covering all buckets + dirty-data cases."""
    return pd.DataFrame(SYNTH_ROWS)


@pytest.fixture
def settings(tmp_path: Path, raw_df: pd.DataFrame):
    """Temp settings pointing at a synthetic CSV + tmp parquet/reports."""
    csv_path = tmp_path / "raw.csv"
    raw_df.to_csv(csv_path, index=False)
    cfg = {
        "data": {
            "raw_path": str(csv_path),
            "processed_path": str(tmp_path / "cleaned.parquet"),
            "archive_dir": str(tmp_path / "archive"),
        },
        "cleaning": {
            "drop_columns": ["index", "New", "PendingS"],
            "date_column": "Date",
            "amount_column": "Amount",
            "default_currency": "INR",
            "unknown_state": "UNKNOWN",
        },
        "fiscal": {"week_column": "fiscal_week", "year_column": "fiscal_year",
                   "label_column": "week_label"},
        "buckets": {
            "Net Realized": ["Shipped - Delivered to Buyer"],
            "Cancellation Leakage": ["Cancelled"],
            "Return Leakage": ["Shipped - Returned to Seller",
                               "Shipped - Returning to Seller",
                               "Shipped - Rejected by Buyer"],
            "Loss Leakage": ["Shipped - Lost in Transit", "Shipped - Damaged"],
            "In-Transit": ["Shipped", "Shipped - Picked Up",
                           "Shipped - Out for Delivery", "Shipping"],
            "Pending": ["Pending", "Pending - Waiting for Pick Up"],
        },
        "thresholds": {
            "settled_clearance_critical_below": 70.0,
            "leakage_warning_above": 35.0,
            "cancellation_warning_above": 15.0,
            "wow_drop_alert_below": -10.0,
            "min_days_for_full_week": 7,
        },
        "reports": {"output_dir": str(tmp_path / "reports"),
                    "workbook_prefix": "Test_Dashboard"},
        "logging": {"level": "INFO", "file": str(tmp_path / "logs" / "t.log")},
    }
    cfg_path = tmp_path / "settings.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return load_settings(cfg_path)
