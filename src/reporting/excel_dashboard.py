"""3-tab openpyxl workbook orchestrator: Executive, Trends, Audit."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

from ..config import Settings
from ..logger import get_logger
from ..reconciliation.metrics import compute_headline_kpis
from ..utils.file_utils import ensure_dir
from .charts import build_combo_on_exec
from .formatters import INR_FORMAT, INT_FORMAT, SUBTITLE_FONT, TITLE_FONT
from .kpi_cards import render_kpi_card
from .tabs_audit import build_audit_tab
from .tabs_trends import build_trends_tab

log = get_logger(__name__)


def _build_executive_tab(
    wb: Workbook, weekly: pd.DataFrame, period: str, run_str: str, df: pd.DataFrame
):
    """Executive Dashboard tab: metadata banner + 6 styled KPI cards.

    Args:
        wb: Target workbook (first sheet is reused).
        weekly: Weekly KPI frame from the reconciliation engine.
        period: Human fiscal period label.
        run_str: Human-readable run timestamp.
        df: Cleaned transaction frame (for headline KPI computation).

    Returns:
        The Executive sheet (chart destination).
    """
    ws = wb.active
    ws.title = "Executive Dashboard"
    ws["A1"] = "Weekly Revenue Reconciliation — Executive Dashboard"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = f"Fiscal Period: {period}   |   Run Date: {run_str}"
    ws["A2"].font = SUBTITLE_FONT

    kpi = compute_headline_kpis(df, weekly)
    totals = weekly[["gross_revenue", "net_realized",
                     "total_leakage", "total_orders"]].sum()
    avg_clear = (
        round(float(weekly["settled_clearance_rate"].mean()), 2)
        if "settled_clearance_rate" in weekly.columns and len(weekly)
        else 0.0
    )
    avg_aov = round(
        float(totals["gross_revenue"] / totals["total_orders"])
        if totals["total_orders"]
        else 0.0,
        2,
    )
    peak_row = weekly.loc[weekly["avg_order_value"].idxmax()] if len(weekly) else None
    peak_aov = f"Peak: {peak_row['week_label']} @ ₹{peak_row['avg_order_value']:,.2f}" if peak_row is not None else ""

    # 2 rows of 3 modern floating cards with subtitles.
    # Every subtext is computed from the data, never hardcoded.
    kpis = [
        # (row, col, label, value, color, fmt, subtext)
        (4, 1, "Gross Invoiced Revenue", float(totals["gross_revenue"]), "blue", INR_FORMAT,
         f"{kpi.total_lines:,} transaction lines · {kpi.unique_orders:,} unique orders"),
        (4, 3, "Net Realized Cash", float(totals["net_realized"]), "green", INR_FORMAT,
         f"{kpi.unique_orders - kpi.cancelled_orders:,} settled orders"),
        (4, 5, "Total Revenue Leakage", float(totals["total_leakage"]), "red", INR_FORMAT,
         f"Cancellations ₹{kpi.cancellation_leakage/1e5:,.2f}L + Returns ₹{kpi.return_leakage/1e5:,.2f}L"),
        (8, 1, "Settled Clearance %", avg_clear, "yellow", '0.00"%"',
         f"Target {70.0:.0f}% of settled base · leakage share {100-avg_clear:.1f}%"),
        (8, 3, "Total Orders Audited", int(totals["total_orders"]), "gray", INT_FORMAT,
         f"{kpi.weeks_active} fiscal weeks ({kpi.full_weeks} full)"),
        (8, 5, "Avg Order Value (AOV)", avg_aov, "purple", INR_FORMAT, peak_aov),
    ]
    for row, col, label, value, color, fmt, sub in kpis:
        render_kpi_card(ws, row, col, label, value, color, fmt, subtext=sub)

    # Set explicit row heights for vertical rhythm
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[3].height = 8
    ws.row_dimensions[4].height = 16
    ws.row_dimensions[5].height = 24
    ws.row_dimensions[6].height = 14
    ws.row_dimensions[7].height = 8
    ws.row_dimensions[8].height = 16
    ws.row_dimensions[9].height = 24
    ws.row_dimensions[10].height = 14
    ws.row_dimensions[11].height = 10

    for col_letter in ["A", "B", "C", "D", "E", "F"]:
        ws.column_dimensions[col_letter].width = 16
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "A3"
    return ws


def build_workbook(
    settings: Settings,
    weekly: pd.DataFrame,
    exceptions: pd.DataFrame,
    period_label: str,
    df: pd.DataFrame | None = None,
) -> Path:
    """Generate the 3-tab reconciliation workbook.

    Args:
        settings: Loaded settings (output dir + prefix).
        weekly: Weekly KPI frame (with ``wow_net_growth``).
        exceptions: Cancelled / returned / lost order detail rows.
        period_label: Human fiscal period string for the header.
        df: Optional cleaned transaction frame, used to compute headline KPIs
            for the executive cards. When omitted, the cards fall back to
            values aggregated from ``weekly`` alone.

    Returns:
        Path of the written ``.xlsx`` workbook.
    """
    wb = Workbook()
    now = datetime.now()
    run_str = now.strftime("%Y-%m-%d %H:%M")
    source = df if df is not None else pd.DataFrame()
    exec_ws = _build_executive_tab(wb, weekly, period_label, run_str, source)
    trends, first_row, last_row = build_trends_tab(wb, weekly)
    build_combo_on_exec(exec_ws, trends, first_row, last_row)
    build_audit_tab(wb, exceptions, run_str)
    out_dir = ensure_dir(settings.resolve(settings.reports.output_dir))
    stamp = now.strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"{settings.reports.workbook_prefix}_{stamp}.xlsx"
    wb.save(path)
    log.info("Workbook written -> %s", path)
    return path

