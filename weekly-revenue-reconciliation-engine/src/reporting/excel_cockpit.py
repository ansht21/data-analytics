"""Dark "Command Center" Excel tab — the Excel twin of the Streamlit cockpit.

Lays out the executive workbook the same way the Streamlit dashboard looks:
a title bar, an audit-status banner, two gradient hero cards with a stack
of stat pills, then a chart band (revenue trend, revenue mix donut,
settlement gauge) over a weekly detail table.

Excel has no page background, so the dark canvas is painted by filling the
used range; charts are real native Excel charts, not images.
"""

from __future__ import annotations

import pandas as pd
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from ..config import Settings
from ..reconciliation.metrics import compute_headline_kpis
from .excel_cards import (
    render_hero_card,
    render_section_header,
    render_stat_pill,
    render_status_banner,
)
from .excel_charts import (
    build_area_trend,
    build_bucket_donut,
    build_settlement_gauge,
)
from .excel_theme import (
    CANVAS_FILL,
    INR_FORMAT,
    INT_FORMAT,
    PANEL_FILL,
    SUBTITLE_FONT,
    TABLE_FONT,
    TABLE_HEADER_FONT,
    TITLE_FONT,
)

# Column layout of the Command Center sheet.
CANVAS_COLS = 14
HERO_COL = 1
HERO_SPAN = 5
HERO2_COL = 7
PILL_COL = 12
PILL_SPAN = 3

# The hidden data block that feeds the native Excel charts.
DATA_COL = 18  # column R


def _paint_canvas(ws: Worksheet, last_row: int) -> None:
    """Fill the whole used range with the dark canvas colour.

    Args:
        ws: Target worksheet.
        last_row: Last row to paint.
    """
    for r in range(1, last_row + 1):
        for c in range(1, CANVAS_COLS + 1):
            ws.cell(row=r, column=c).fill = CANVAS_FILL


def _format_inr_short(value: float) -> str:
    """Format an amount using Indian short units (Cr / L / K).

    Hero values are wide, so the headline figure uses short units and the
    exact rupee amount is carried in the card footer.

    Args:
        value: Amount in rupees.

    Returns:
        Formatted string, e.g. ``₹7.86 Cr``.
    """
    magnitude = abs(value)
    if magnitude >= 1e7:
        return f"₹{value / 1e7:,.2f} Cr"
    if magnitude >= 1e5:
        return f"₹{value / 1e5:,.2f} L"
    if magnitude >= 1e3:
        return f"₹{value / 1e3:,.1f} K"
    return f"₹{value:,.0f}"


def _bucket_totals(weekly: pd.DataFrame, df: pd.DataFrame | None) -> dict[str, float]:
    """Compute revenue by financial bucket, largest first.

    Prefers the raw transaction frame (exact) and falls back to the weekly
    aggregates, so the workbook builds even when the caller does not supply
    the transaction frame.

    Args:
        weekly: Weekly KPI frame.
        df: Optional cleaned transaction frame.

    Returns:
        Mapping of bucket name -> total amount, sorted descending.
    """
    if df is not None and len(df) and "financial_bucket" in df.columns:
        totals = df.groupby("financial_bucket")["Amount"].sum()
    else:
        totals = pd.Series(dtype="float64")
        for bucket, column in (
            ("Net Realized", "net_realized"),
            ("Cancellation Leakage", "cancellation_leakage"),
            ("Return Leakage", "return_leakage"),
            ("Loss Leakage", "loss_leakage"),
            ("In-Transit", "in_transit_value"),
            ("Pending", "pending_value"),
        ):
            if column in weekly.columns:
                totals[bucket] = float(weekly[column].sum())
    return {str(k): float(v) for k, v in totals.sort_values(ascending=False).items()}


def _write_chart_data(
    ws: Worksheet,
    weekly: pd.DataFrame,
    df: pd.DataFrame,
    kpi,
) -> dict[str, int]:
    """Write the hidden source block that the native charts reference.

    Args:
        ws: Target worksheet.
        weekly: Weekly KPI frame.
        df: Cleaned transaction frame.
        kpi: Headline KPIs.

    Returns:
        Mapping of data-block anchors (row indices).
    """
    c = DATA_COL
    week_col = c
    gross_col = c + 1
    net_col = c + 2
    orders_col = c + 3
    bucket_label_col = c + 5
    bucket_value_col = c + 6
    gauge_value_col = c + 8

    # Weekly series: header row then one row per week.
    ws.cell(row=1, column=week_col, value="Week")
    ws.cell(row=1, column=gross_col, value="Gross Invoiced")
    ws.cell(row=1, column=net_col, value="Net Realized")
    ws.cell(row=1, column=orders_col, value="Transaction Lines")
    for i, (_, r) in enumerate(weekly.iterrows()):
        row = 2 + i
        ws.cell(row=row, column=week_col, value=str(r["week_label"]))
        ws.cell(row=row, column=gross_col, value=float(r["gross_revenue"]))
        ws.cell(row=row, column=net_col, value=float(r["net_realized"]))
        ws.cell(row=row, column=orders_col, value=int(r["total_orders"]))

    # Bucket mix. Derived from the weekly frame so the block is available
    # even when the raw transaction frame is not supplied.
    ws.cell(row=1, column=bucket_label_col, value="Financial Bucket")
    ws.cell(row=1, column=bucket_value_col, value="Amount")
    buckets = _bucket_totals(weekly, df)
    for i, (name, amount) in enumerate(buckets.items()):
        row = 2 + i
        ws.cell(row=row, column=bucket_label_col, value=str(name))
        ws.cell(row=row, column=bucket_value_col, value=float(amount))

    # Gauge: retained vs the rest of the settled base.
    ws.cell(row=1, column=gauge_value_col, value="Retained")
    ws.cell(row=1, column=gauge_value_col + 1, value="Rest")
    ws.cell(row=2, column=gauge_value_col, value=round(kpi.settled_clearance_rate, 2))
    ws.cell(row=2, column=gauge_value_col + 1,
            value=round(100 - kpi.settled_clearance_rate, 2))

    return {
        "weekly_row": 2,
        "week_col": week_col,
        "gross_col": gross_col,
        "net_col": net_col,
        "orders_col": orders_col,
        "bucket_row": 2,
        "bucket_label_col": bucket_label_col,
        "bucket_value_col": bucket_value_col,
        "gauge_row": 2,
        "gauge_value_col": gauge_value_col,
        "bucket_labels": list(buckets.keys()),
    }


def build_command_center(
    ws: Worksheet,
    settings: Settings,
    weekly: pd.DataFrame,
    df: pd.DataFrame,
    period_label: str,
    run_str: str,
) -> Worksheet:
    """Build the dark Command Center executive tab.

    Args:
        ws: Target worksheet.
        settings: Loaded settings (thresholds).
        weekly: Weekly KPI frame.
        df: Cleaned transaction frame.
        period_label: Human fiscal period label.
        run_str: Run timestamp.

    Returns:
        The populated worksheet.
    """
    kpi = compute_headline_kpis(df, weekly)
    target = settings.thresholds.settled_clearance_critical_below
    in_flight = kpi.in_transit_value + kpi.pending_value

    # Paint the dark canvas first; the cards and panels are drawn on top.
    _paint_canvas(ws, 52)

    # --- Title block -----------------------------------------------------
    ws["A1"] = "REVENUE RECONCILIATION COCKPIT"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = (
        f"Amazon India Marketplace   |   Fiscal Period: {period_label}   |   "
        f"Run Date: {run_str}"
    )
    ws["A2"].font = SUBTITLE_FONT
    ws.merge_cells("A1:F1")
    ws.merge_cells("A2:F2")
    # --- Audit status banner ---------------------------------------------
    render_status_banner(
        ws, 4, 1, CANVAS_COLS,
        "AUDIT STATUS: RECONCILED",
        f"{kpi.total_lines:,} lines  |  {kpi.unique_orders:,} unique orders  |  "
        f"{kpi.weeks_active} fiscal weeks ({kpi.full_weeks} full, "
        f"{kpi.partial_weeks} partial)",
    )

    # --- Hero cards + stat pills ----------------------------------------
    render_hero_card(
        ws, 6, HERO_COL, HERO_SPAN, 5,
        "Total Revenue Invoiced",
        _format_inr_short(kpi.gross_revenue),
        f"{kpi.total_lines:,} transaction lines audited",
        foot=f"Exact: ₹{kpi.gross_revenue:,.2f}  |  {kpi.weeks_active} fiscal "
             f"weeks  |  AOV ₹{kpi.avg_order_value:,.0f}",
    )
    render_hero_card(
        ws, 6, HERO2_COL, HERO_SPAN, 5,
        "Net Realized Cash",
        _format_inr_short(kpi.net_realized),
        f"{kpi.settled_clearance_rate:.1f}% of the settled base retained",
        foot=f"Exact: ₹{kpi.net_realized:,.2f}  |  Settlement lag "
             f"{kpi.settlement_lag_rate:.1f}%  |  ₹{in_flight/1e7:,.2f} Cr in flight",
        alt=True,
    )
    render_stat_pill(ws, 6, PILL_COL, PILL_SPAN, "Total Leakage",
                      f"₹{kpi.total_leakage/1e7:,.2f} Cr", "neg")
    render_stat_pill(ws, 8, PILL_COL, PILL_SPAN, "Cancelled Orders",
                      f"{kpi.cancelled_orders:,}", "neg")
    render_stat_pill(ws, 10, PILL_COL, PILL_SPAN, "Settled Clearance",
                      f"{kpi.settled_clearance_rate:.1f}%",
                      "pos" if kpi.settled_clearance_rate >= target else "warn")

    # --- Chart band ------------------------------------------------------
    render_section_header(ws, 13, 1, CANVAS_COLS, "Performance Cockpit")
    refs = _write_chart_data(ws, weekly, df, kpi)
    build_area_trend(ws, weekly, refs["weekly_row"], refs["week_col"],
                     refs["net_col"], "A14")
    build_bucket_donut(ws, refs["bucket_labels"], refs["bucket_row"],
                       refs["bucket_label_col"], refs["bucket_value_col"], "H14")
    build_settlement_gauge(ws, refs["gauge_row"], refs["gauge_value_col"],
                           refs["gauge_value_col"], "M14")

    # --- Weekly detail table --------------------------------------------
    table_row = 34
    render_section_header(ws, table_row, 1, CANVAS_COLS,
                          "Weekly Reconciliation Detail")
    headers = ["Week", "Gross ₹", "Net ₹", "Leakage ₹", "Settled Clearance %",
               "WoW Net %", "Lines", "Partial"]
    for i, head in enumerate(headers, start=1):
        cell = ws.cell(row=table_row + 1, column=i, value=head)
        cell.font = TABLE_HEADER_FONT
        cell.fill = PANEL_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for i, (_, r) in enumerate(weekly.iterrows()):
        row = table_row + 2 + i
        values = [
            str(r["week_label"]), float(r["gross_revenue"]), float(r["net_realized"]),
            float(r["total_leakage"]), float(r["settled_clearance_rate"]),
            float(r["wow_net_growth"]) if "wow_net_growth" in r else 0.0,
            int(r["total_orders"]),
            "YES" if bool(r.get("is_partial_week", False)) else "NO",
        ]
        for c, val in enumerate(values, start=1):
            cell = ws.cell(row=row, column=c, value=val)
            cell.font = TABLE_FONT
            if c in (2, 3, 4):
                cell.number_format = INR_FORMAT
            elif c in (5, 6):
                cell.number_format = '0.00"%"'
            elif c == 7:
                cell.number_format = INT_FORMAT

    # --- Column widths + canvas -----------------------------------------
    for c in range(1, CANVAS_COLS + 1):
        ws.column_dimensions[get_column_letter(c)].width = 14
    ws.column_dimensions["A"].width = 16
    # Give the detail table's money and percentage columns room for their
    # headers, which are wider than the default column width.
    for col, width in (("B", 16), ("C", 16), ("D", 16), ("E", 20), ("F", 14),
                       ("G", 12), ("H", 10)):
        ws.column_dimensions[col].width = width
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A5"

    # Size the rows so the hero cards and the banner have breathing room.
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 16
    ws.row_dimensions[4].height = 22
    for r in range(6, 12):
        ws.row_dimensions[r].height = 20
    ws.row_dimensions[7].height = 30
    ws.row_dimensions[8].height = 12

    # Hide the chart-source block so the dashboard reads cleanly.
    for c in range(DATA_COL, DATA_COL + 10):
        ws.column_dimensions[get_column_letter(c)].hidden = True
        ws.column_dimensions[get_column_letter(c)].width = 12

    return ws
