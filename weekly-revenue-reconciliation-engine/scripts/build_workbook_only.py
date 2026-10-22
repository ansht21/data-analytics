"""Build the Excel workbook from the already-cleaned parquet.

A fast path for re-rendering the dashboard without re-running the 11-step
cleaning pipeline over the 19 MB raw CSV.

Usage:
    python scripts/build_workbook_only.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_settings  # noqa: E402
from src.data_loader import load_processed  # noqa: E402
from src.reconciliation.engine import aggregate_weekly  # noqa: E402
from src.reconciliation.variance_analyzer import add_wow_variance  # noqa: E402
from src.reporting.excel_dashboard import build_workbook  # noqa: E402


def main() -> None:
    """Rebuild the reconciliation workbook from the cached parquet."""
    settings = load_settings()
    df = load_processed(settings)
    weekly = add_wow_variance(aggregate_weekly(
        df, min_days_for_full_week=settings.thresholds.min_days_for_full_week))
    exceptions = df[df["financial_bucket"].isin(
        ["Cancellation Leakage", "Return Leakage", "Loss Leakage"]
    )]
    period = (f"{weekly['week_label'].min()}-{weekly['week_label'].max()}"
              if len(weekly) else "empty")
    path = build_workbook(settings, weekly, exceptions, period, df)
    print(f"Workbook: {path}")
    print(f"Built at {datetime.now():%Y-%m-%d %H:%M:%S}")


if __name__ == "__main__":
    main()
