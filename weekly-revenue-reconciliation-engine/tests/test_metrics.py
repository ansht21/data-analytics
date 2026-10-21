"""Tests for the shared metrics layer and partial-week handling."""

from __future__ import annotations

import pandas as pd
import pytest
from src.config import Thresholds
from src.reconciliation.engine import aggregate_weekly
from src.reconciliation.metrics import (
    category_revenue,
    compute_headline_kpis,
    fulfilment_settlement,
    leakage_by_dimension,
)
from src.reconciliation.variance_analyzer import add_wow_variance, detect_anomalies


@pytest.fixture
def frame() -> pd.DataFrame:
    """Two weeks of transactions across four buckets."""
    return pd.DataFrame(
        [
            ("W1", 2022, 13, "Net Realized", 1000.0, "T-shirt", "Amazon", "MAHARASHTRA"),
            ("W1", 2022, 13, "Net Realized", 1000.0, "Shirt", "Amazon", "MAHARASHTRA"),
            ("W1", 2022, 13, "Cancellation Leakage", 250.0, "T-shirt", "Merchant", "KARNATAKA"),
            ("W1", 2022, 13, "Return Leakage", 250.0, "Shirt", "Merchant", "KARNATAKA"),
            ("W2", 2022, 14, "Net Realized", 1200.0, "T-shirt", "Amazon", "MAHARASHTRA"),
            ("W2", 2022, 14, "Cancellation Leakage", 300.0, "T-shirt", "Merchant", "KARNATAKA"),
            ("W2", 2022, 14, "In-Transit", 500.0, "Shirt", "Amazon", "TAMIL NADU"),
        ],
        columns=[
            "week_label", "fiscal_year", "fiscal_week", "financial_bucket",
            "Amount", "Category", "Fulfilment", "ship-state",
        ],
    )


def test_settled_clearance_uses_settled_base(frame: pd.DataFrame) -> None:
    """Settled clearance is Net / (Net + leakage), not Net / Gross."""
    w = aggregate_weekly(frame)
    w1 = w[w["week_label"] == "W1"].iloc[0]
    assert w1["gross_revenue"] == 2500.0
    assert w1["net_realized"] == 2000.0
    assert w1["total_leakage"] == 500.0
    assert w1["settled_base"] == 2500.0
    assert w1["settled_clearance_rate"] == pytest.approx(80.0, abs=0.01)
    # Gross coverage is much lower because In-Transit is excluded from net.
    assert w1["clearance_rate"] == pytest.approx(80.0, abs=0.01)


def test_settled_clearance_ignores_in_transit(frame: pd.DataFrame) -> None:
    """In-Transit must not drag the settled clearance metric down."""
    w = aggregate_weekly(frame)
    w2 = w[w["week_label"] == "W2"].iloc[0]
    assert w2["in_transit_value"] == 500.0
    # 1200 net / (1200 + 300 leakage) = 80%, unaffected by the 500 In-Transit.
    assert w2["settled_clearance_rate"] == pytest.approx(80.0, abs=0.01)
    assert w2["clearance_rate"] == pytest.approx(60.0, abs=0.01)


def test_partial_week_is_flagged() -> None:
    """A week with fewer observed days is flagged as partial."""
    df = pd.DataFrame(
        [
            ("W1", 2022, 13, "Net Realized", 100.0, pd.Timestamp("2022-04-04")),
            ("W1", 2022, 13, "Net Realized", 100.0, pd.Timestamp("2022-04-05")),
        ],
        columns=["week_label", "fiscal_year", "fiscal_week",
                 "financial_bucket", "Amount", "parsed_date"],
    )
    w = aggregate_weekly(df)
    assert bool(w.iloc[0]["is_partial_week"]) is True
    assert w.iloc[0]["days_observed"] == 2


def test_anomalies_skip_partial_weeks() -> None:
    """A truncated week must not fire CRITICAL/ALERT rules."""
    df = pd.DataFrame(
        [
            ("W1", 2022, 13, "Net Realized", 0.0, pd.Timestamp("2022-04-04")),
            ("W1", 2022, 13, "Cancellation Leakage", 500.0, pd.Timestamp("2022-04-04")),
        ],
        columns=["week_label", "fiscal_year", "fiscal_week",
                 "financial_bucket", "Amount", "parsed_date"],
    )
    w = add_wow_variance(aggregate_weekly(df))
    anomalies = detect_anomalies(w, Thresholds())
    assert len(anomalies) == 0


def test_headline_kpis_are_consistent(frame: pd.DataFrame) -> None:
    """Headline KPIs reconcile with the weekly frame."""
    w = aggregate_weekly(frame)
    kpi = compute_headline_kpis(frame, w)
    assert kpi.gross_revenue == 4500.0
    assert kpi.net_realized == 3200.0
    assert kpi.total_leakage == 800.0
    assert kpi.settled_base == 4000.0
    assert kpi.settled_clearance_rate == pytest.approx(80.0, abs=0.01)
    assert kpi.gross_coverage_rate == pytest.approx(71.11, abs=0.01)
    assert kpi.in_transit_value == 500.0
    assert kpi.total_lines == 7
    assert kpi.unique_orders == 7


def test_leakage_by_dimension_sums_correctly(frame: pd.DataFrame) -> None:
    """Dimension leakage only counts true leakage buckets."""
    out = leakage_by_dimension(frame, "ship-state")
    assert not out.empty
    assert out.iloc[0]["ship-state"] == "KARNATAKA"
    assert out.iloc[0]["leakage_amount"] == 800.0
    assert "MAHARASHTRA" not in out["ship-state"].tolist()


def test_fulfilment_settlement_splits_channels(frame: pd.DataFrame) -> None:
    """Each fulfilment channel gets its own gross/net/leakage split."""
    out = fulfilment_settlement(frame)
    assert len(out) == 2
    amazon = out[out["Fulfilment"] == "Amazon"].iloc[0]
    assert amazon["gross_revenue"] == 3700.0
    assert amazon["net_realized"] == 3200.0
    assert amazon["total_leakage"] == 0.0
    merchant = out[out["Fulfilment"] == "Merchant"].iloc[0]
    assert merchant["gross_revenue"] == 800.0
    assert merchant["total_leakage"] == 800.0


def test_category_revenue_sorted(frame: pd.DataFrame) -> None:
    """Category revenue is sorted descending by gross revenue."""
    out = category_revenue(frame)
    assert out["revenue"].tolist() == sorted(out["revenue"].tolist(), reverse=True)
    assert out.iloc[0]["Category"] == "T-shirt"
