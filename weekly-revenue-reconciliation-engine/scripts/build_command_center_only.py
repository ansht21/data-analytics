"""Build only the dark Command Center tab, for fast visual QA.

Renders the executive cockpit worksheet (with its native Excel charts) to a
standalone workbook, skipping the 20k-row exception audit tab which is the
slow part of the full build.

Usage:
    python scripts/build_command_center_only.py [output.xlsx]
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_settings  # noqa: E402
from src.data_loader import load_processed  # noqa: E402
from src.reconciliation.engine import aggregate_weekly  # noqa: E402
from src.reconciliation.variance_analyzer import add_wow_variance  # noqa: E402
from src.reporting.excel_cockpit import build_command_center  # noqa: E402


def main() -> None:
    """Write a workbook containing only the Command Center tab."""
    settings = load_settings()
    df = load_processed(settings)
    weekly = add_wow_variance(aggregate_weekly(
        df, min_days_for_full_week=settings.thresholds.min_days_for_full_week))
    period = f"{weekly['week_label'].min()}-{weekly['week_label'].max()}"

    wb = Workbook()
    ws = wb.active
    ws.title = "Executive Dashboard"
    build_command_center(ws, settings, weekly, df, period,
                         datetime.now().strftime("%Y-%m-%d %H:%M"))

    out = (Path(sys.argv[1]) if len(sys.argv) > 1
           else ROOT / "reports" / "Command_Center_Preview.xlsx")
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"Command Center -> {out}")


if __name__ == "__main__":
    main()
