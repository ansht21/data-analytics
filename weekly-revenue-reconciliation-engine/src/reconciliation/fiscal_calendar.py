"""ISO fiscal calendar helpers and week-boundary utilities."""

from __future__ import annotations

import pandas as pd


def iso_week_label(year: int, week: int) -> str:
    """Return the ``Wnn`` label for an ISO year/week pair."""
    return f"W{int(week)}"


def week_bounds(year: int, week: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return Monday..Sunday bounds for an ISO year/week pair."""
    monday = pd.Timestamp.fromisocalendar(int(year), int(week), 1)
    return monday, monday + pd.Timedelta(days=6)


def sorted_week_labels(df: pd.DataFrame, label_col: str = "week_label") -> list[str]:
    """Return week labels sorted by (year, week) numeric order."""
    cols = [c for c in ("fiscal_year", "fiscal_week", label_col) if c in df.columns]
    ordered = df[cols].drop_duplicates().sort_values(
        ["fiscal_year", "fiscal_week"] if "fiscal_year" in cols else cols
    )
    return ordered[label_col].tolist() if label_col in ordered else []
