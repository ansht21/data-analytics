"""Date helpers: mixed-format parsing and ISO fiscal calendar tagging."""

from __future__ import annotations

import pandas as pd


def parse_mixed_dates(series: pd.Series) -> pd.Series:
    """Parse Amazon's mixed ``MM-DD-YY`` / ``MM-DD-YYYY`` date strings.

    Args:
        series: Raw string date column.

    Returns:
        Datetime series (``NaT`` where unparseable).
    """
    return pd.to_datetime(series, format="mixed", dayfirst=False)


def add_fiscal_tags(
    df: pd.DataFrame,
    date_col: str = "parsed_date",
    week_col: str = "fiscal_week",
    year_col: str = "fiscal_year",
    label_col: str = "week_label",
) -> pd.DataFrame:
    """Attach ISO fiscal week / year / label columns (``W13`` … ``W26``).

    Args:
        df: Frame with a datetime column.
        date_col: Source datetime column name.
        week_col: Destination ISO week integer column.
        year_col: Destination ISO year column.
        label_col: Destination ``Wnn`` label column.

    Returns:
        Copy of ``df`` with the three fiscal columns added.
    """
    out = df.copy()
    iso = out[date_col].dt.isocalendar()
    out[week_col] = iso["week"].astype(int)
    out[year_col] = iso["year"].astype(int)
    out[label_col] = "W" + out[week_col].astype(str)
    return out


def week_bounds(year: int, week: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return Monday..Sunday bounds for an ISO year/week pair."""
    monday = pd.Timestamp.fromisocalendar(year, week, 1)
    return monday, monday + pd.Timedelta(days=6)
