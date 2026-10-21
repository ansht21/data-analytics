"""Tests for weekly aggregation, WoW variance & anomaly detection."""

from __future__ import annotations

import pandas as pd
import pytest
from src.config import Thresholds
from src.reconciliation.engine import aggregate_weekly
from src.reconciliation.variance_analyzer import add_wow_variance, detect_anomalies


@pytest.fixture
def weekly_src() -> pd.DataFrame:
    """Two synthetic weeks: W1 (healthy) then W2 (collapsed)."""
    return pd.DataFrame([
        # week_label, year, week, bucket, Amount
        *[( "W1", 2022, 13, "Net Realized", 1000.0)] * 2,
        ("W1", 2022, 13, "Cancellation Leakage", 100.0),
        ("W1", 2022, 13, "Return Leakage", 50.0),
        ("W1", 2022, 13, "Loss Leakage", 50.0),
        ("W1", 2022, 13, "In-Transit", 200.0),
        *[( "W2", 2022, 14, "Net Realized", 500.0)] * 2,
        ("W2", 2022, 14, "Cancellation Leakage", 400.0),
        ("W2", 2022, 14, "Return Leakage", 100.0),
        ("W2", 2022, 14, "Pending", 50.0),
    ]).rename(columns={0: "week_label", 1: "fiscal_year", 2: "fiscal_week",
                       3: "financial_bucket", 4: "Amount"})


def test_weekly_math(weekly_src: pd.DataFrame) -> None:
    """Gross/Net/leakage/clearance math matches hand calculations."""
    w = aggregate_weekly(weekly_src)
    w1 = w[w["week_label"] == "W1"].iloc[0]
    assert w1["gross_revenue"] == 2400.0
    assert w1["net_realized"] == 2000.0
    assert w1["cancellation_leakage"] == 100.0
    assert w1["total_leakage"] == 200.0
    assert w1["clearance_rate"] == pytest.approx(83.33, abs=0.01)
    assert w1["total_orders"] == 6
    assert w1["cancellation_rate"] == pytest.approx(16.67, abs=0.01)


def test_wow_variance(weekly_src: pd.DataFrame) -> None:
    """WoW net growth: W1 = 0 (no prior), W2 = -50%."""
    w = add_wow_variance(aggregate_weekly(weekly_src))
    assert w.iloc[0]["wow_net_growth"] == 0.0
    assert w.iloc[1]["wow_net_growth"] == -50.0


def test_anomaly_rules(weekly_src: pd.DataFrame) -> None:
    """W2 triggers all three rules; severity labels correct."""
    w = add_wow_variance(aggregate_weekly(weekly_src))
    a = detect_anomalies(w, Thresholds())
    assert set(a[a["week_label"] == "W2"]["severity"]) == {
        "CRITICAL", "WARNING", "ALERT"}
    assert len(a[a["week_label"] == "W1"]) >= 1  # clearance 71% < 85
