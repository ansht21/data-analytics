"""Tests for ISO fiscal calendar + date utilities."""

from __future__ import annotations

import pandas as pd
from src.reconciliation.fiscal_calendar import (
    iso_week_label,
    sorted_week_labels,
    week_bounds,
)
from src.utils.date_utils import add_fiscal_tags, parse_mixed_dates


def test_iso_week_label() -> None:
    """W-prefixed label formatting."""
    assert iso_week_label(2022, 13) == "W13"


def test_week_bounds_monday_sunday() -> None:
    """Bounds land on Monday..Sunday, 7 days apart."""
    mon, sun = week_bounds(2022, 13)
    assert mon.dayofweek == 0
    assert (sun - mon).days == 6


def test_mixed_date_parsing() -> None:
    """MM-DD-YY and MM-DD-YYYY both parse."""
    parsed = parse_mixed_dates(pd.Series(["03-31-22", "04-30-2022"]))
    assert parsed.iloc[0].year == 2022
    assert parsed.iloc[1].month == 4


def test_fiscal_tags_match_reference_dates() -> None:
    """31-Mar-2022 -> W13; 29-Jun-2022 -> W26 (dataset bounds)."""
    df = pd.DataFrame({"d": pd.to_datetime(["2022-03-31", "2022-06-29"])})
    out = add_fiscal_tags(df, date_col="d")
    assert out["week_label"].iloc[0] == "W13"
    assert out["fiscal_year"].iloc[0] == 2022
    assert out["week_label"].iloc[-1] == "W26"


def test_sorted_week_labels() -> None:
    """Labels sort by numeric week, not string."""
    df = pd.DataFrame({"week_label": ["W26", "W13"],
                       "fiscal_year": [2022, 2022],
                       "fiscal_week": [26, 13]})
    assert sorted_week_labels(df) == ["W13", "W26"]
