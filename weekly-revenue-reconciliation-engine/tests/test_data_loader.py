"""Tests for the 11-step ingestion & cleaning pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.data_loader import run_cleaning_pipeline


def test_pipeline_shape_and_drops(settings) -> None:
    """Dead columns dropped, all rows retained."""
    df = run_cleaning_pipeline(settings)
    assert len(df) == 8
    for col in ("index", "New", "PendingS"):
        assert col not in df.columns


def test_amount_and_currency_defaults(settings) -> None:
    """Null Amount -> 0.0 and null currency -> INR."""
    df = run_cleaning_pipeline(settings)
    assert df["Amount"].isna().sum() == 0
    assert df.loc[df["Order ID"] == "A2", "Amount"].iloc[0] == 0.0
    assert (df["currency"] == "INR").all()


def test_state_city_standardization(settings) -> None:
    """States uppercased/stripped, nulls -> UNKNOWN."""
    df = run_cleaning_pipeline(settings)
    assert "GUJARAT" in set(df["ship-state"])
    assert "UNKNOWN" in set(df["ship-state"])
    assert df["ship-state"].str.strip().eq(df["ship-state"]).all()


def test_fba_imputation(settings) -> None:
    """Amazon FBA rows get fulfilled-by = Amazon FBA."""
    df = run_cleaning_pipeline(settings)
    a1 = df[df["Order ID"] == "A1"]["fulfilled-by"].iloc[0]
    assert a1 == "Amazon FBA"


def test_fiscal_tags_and_buckets(settings) -> None:
    """Week labels W-prefixed; bucket mapping correct; Unmapped fallback."""
    df = run_cleaning_pipeline(settings)
    assert df["week_label"].str.match(r"^W\d+$").all()
    a2 = df[df["Order ID"] == "A2"]["financial_bucket"].iloc[0]
    assert a2 == "Cancellation Leakage"
    a8 = df[df["Order ID"] == "A8"]["financial_bucket"].iloc[0]
    assert a8 == "Unmapped"


def test_parquet_exported(settings) -> None:
    """Cleaned parquet written and re-loadable."""
    df = run_cleaning_pipeline(settings)
    out = Path(settings.resolve(settings.data.processed_path))
    assert out.exists()
    back = pd.read_parquet(out)
    assert len(back) == len(df)
