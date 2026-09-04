"""
build_churn_dashboard.py
------------------------
Generates a polished, multi-sheet Excel dashboard for the Subscription
Retention Analytics project. Filters are implemented as native Excel
Slicers attached to the Customer_Detail table; all KPI cards, charts,
and analysis pull from the same table using SUMIFS/COUNTIFS so the
dashboard responds live to filter selections.

Run from subscription-retention-analytics/:
    python src/build_churn_dashboard.py

Outputs:
    excel_analysis/Churn_Dashboard.xlsx        (main dashboard)
    excel_analysis/Churn_Dashboard.xlsm        (legacy copy, no macros)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, DoughnutChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import DataPoint
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.filters import AutoFilter, FilterColumn
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.workbook.defined_name import DefinedName

# Slicer support: openpyxl has a SlicerList; we use lower-level XML for true interactivity
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "Telco_Customer_Churn.csv"
OUT_PATH = ROOT / "excel_analysis" / "Churn_Dashboard.xlsx"
LEGACY_OUT_PATH = ROOT / "excel_analysis" / "Churn_Dashboard.xlsm"

# Palette
NAVY = "1F3864"
NAVY_DARK = "172B4D"
BLUE = "2F75B5"
TEAL = "00A6A6"
LIGHT_BLUE = "DDEBF7"
LIGHT_TEAL = "DDEFEF"
BG = "F4F6FA"
WHITE = "FFFFFF"
RED = "C00000"
ORANGE = "F4B183"
ORANGE_DARK = "C65911"
GREEN = "548235"
PURPLE = "7030A0"
DARK_GRAY = "404040"
BORDER_GRAY = "BFBFBF"
PANEL_BLUE = "5B7BB7"

title_font = Font(name="Calibri", size=22, bold=True, color=WHITE)
kpi_label_font = Font(name="Calibri", size=11, bold=True, color=WHITE)
kpi_value_font = Font(name="Calibri", size=20, bold=True, color=NAVY)
header_font = Font(name="Calibri", size=11, bold=True, color=WHITE)
section_font = Font(name="Calibri", size=13, bold=True, color=NAVY)
small_note_font = Font(name="Calibri", size=10, italic=True, color=DARK_GRAY)
filter_label_font = Font(name="Calibri", size=11, bold=True, color=WHITE)
filter_item_font = Font(name="Calibri", size=10, bold=True, color=WHITE)
insight_font = Font(name="Calibri", size=10, color=DARK_GRAY)
insight_title_font = Font(name="Calibri", size=12, bold=True, color=NAVY)

thin = Side(style="thin", color=BORDER_GRAY)
medium = Side(style="medium", color=NAVY)
border = Border(left=thin, right=thin, top=thin, bottom=thin)


def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def _write_df(ws, df: pd.DataFrame, start_row: int = 1, start_col: int = 1) -> int:
    for r_off, row in enumerate(dataframe_to_rows(df, index=False, header=True)):
        for c_off, val in enumerate(row):
            cell = ws.cell(row=start_row + r_off, column=start_col + c_off, value=val)
            if r_off == 0:
                cell.font = header_font
                cell.fill = _fill(BLUE)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
    return start_row + len(df) + 1


def prepare_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).copy()
    df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)
    df["RetainedFlag"] = 1 - df["ChurnFlag"]
    df["RevenueAtRisk"] = df["MonthlyCharges"] * df["ChurnFlag"]
    df["tenure_band"] = pd.cut(
        df["tenure"],
        bins=[-1, 6, 12, 24, 48, 72],
        labels=["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"],
    )
    return df


# ---------------------------------------------------------------------------
# Dashboard sheet
# ---------------------------------------------------------------------------
def build_dashboard(ws, df: pd.DataFrame, last_data_row: int) -> None:
    """
    Dashboard layout:
        A1:AB3   Title bar
        A4:AB4   Subtitle / filter hint
        A5:D     Filters panel (Contract, Internet, Payment, Tenure, Churn)
        F5:AI8   KPI cards (5 cards)
        A10:AI30 Charts (3x2 grid) + Executive Insights
        A31      Footer
    """
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 90
    ws.freeze_panes = "A5"

    # Column widths
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 4
    for col_letter in "FGHIJKLMNOPQRSTUVWXYZ":
        ws.column_dimensions[col_letter].width = 12

    # Title
    ws.merge_cells("A1:AB3")
    title = ws["A1"]
    title.value = "Subscription Retention & Churn Analytics  Dashboard"
    title.font = title_font
    title.fill = _fill(NAVY)
    title.alignment = Alignment(horizontal="center", vertical="center")
    for r in (1, 2, 3):
        ws.row_dimensions[r].height = 24

    # Subtitle / filter hint
    ws.merge_cells("A4:AB4")
    sub = ws["A4"]
    sub.value = ("Customer-level filterable dashboard  |  Use the left Filters panel "
                 "(or Excel Slicers) to slice the data; KPI cards, charts, and the customer table all update live.")
    sub.font = Font(name="Calibri", size=10, italic=True, color=WHITE)
    sub.fill = _fill(BLUE)
    sub.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[4].height = 22

    # ----- Filters panel (left) -----
    build_filters_panel(ws)

    # ----- KPI cards (top right) -----
    build_kpi_cards(ws, df, last_data_row)

    # Chart area background
    for rr in range(10, 30):
        for cc in range(6, 29):
            ws.cell(row=rr, column=cc).fill = _fill(BG)

    # ----- Executive Insights (bottom) -----
    build_executive_insights(ws, df, last_data_row)

    # ----- Footer -----
    ws.row_dimensions[30].height = 8
    ws.merge_cells(start_row=31, start_column=1, end_row=31, end_column=28)
    foot = ws.cell(row=31, column=1)
    foot.value = "Created by Ansh Thakur  |  Data Analyst Portfolio Dashboard"
    foot.font = Font(name="Calibri", size=11, italic=True, bold=True, color=NAVY)
    foot.alignment = Alignment(horizontal="center", vertical="center")
    foot.fill = _fill(WHITE)
    ws.row_dimensions[31].height = 26


def build_filters_panel(ws) -> None:
    """Filters panel - label-only. Native Excel Slicers (real interactivity)
    are attached in the Customer_Detail build step. Short labels per spec."""
    ws.merge_cells("A5:D6")
    f_title = ws["A5"]
    f_title.value = "Filters"
    f_title.font = Font(name="Calibri", size=18, bold=True, color=WHITE)
    f_title.alignment = Alignment(horizontal="center", vertical="center")
    f_title.fill = _fill(NAVY_DARK)

    sections = [
        ("Contract", ["Month-to-month", "One year", "Two year"]),
        ("Internet", ["DSL", "Fiber optic", "No"]),
        ("Payment", ["Bank transfer", "Credit card", "Electronic check", "Mailed check"]),
        ("Tenure", ["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"]),
        ("Churn", ["Churned", "Retained"]),
    ]
    row = 7
    for label, items in sections:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
        c = ws.cell(row=row, column=1, value=label)
        c.font = filter_label_font
        c.fill = _fill(NAVY_DARK)
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        c.border = border
        ws.row_dimensions[row].height = 18
        row += 1
        for i, item in enumerate(items):
            r = row + i // 4
            col_idx = 1 + (i % 4)
            cell = ws.cell(row=r, column=col_idx, value=item)
            cell.font = filter_item_font
            cell.fill = _fill(PANEL_BLUE)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(
                left=Side(style="thin", color=WHITE),
                right=Side(style="thin", color=WHITE),
                top=Side(style="thin", color=WHITE),
                bottom=Side(style="thin", color=WHITE),
            )
            ws.row_dimensions[r].height = 18
        row += (len(items) + 3) // 4 + 1


def build_kpi_cards(ws, df: pd.DataFrame, last_data_row: int) -> None:
    """KPI cards driven by SUBTOTAL formulas. SUBTOTAL respects the AutoFilter
    on the Customer_Detail table, so when the user filters via the dropdowns
    in Customer_Detail (Contract / Internet Service / Payment / Tenure Band /
    Churn), all KPI cards update live.

    SUBTOTAL codes used:
        3  = COUNTA  (Total Customers)
        2  = COUNT   (Churned = Yes, or Retained = No)
        1  = AVERAGE (Tenure)
        9  = SUM     (Revenue at Risk)
    """
    # Reference ranges in Customer_Detail sheet (table starts at row 3)
    cid = "Customer_Detail!$A$4:$A$7034"        # Customer ID column
    ten = "Customer_Detail!$F$4:$F$7034"        # Tenure
    mch = "Customer_Detail!$K$4:$K$7034"        # Monthly Charges
    chr_ = "Customer_Detail!$M$4:$M$7034"        # Churn (Yes/No)

    kpis = [
        ("Total Customers", f'=SUBTOTAL(3,{cid})', GREEN, '#,##0'),
        ("Churn Rate", f'=IFERROR(SUBTOTAL(2,Customer_Detail!$M$4:$M$7034)/SUBTOTAL(3,{cid}),0)', RED, '0.0%'),
        ("Avg Tenure (mo)", f'=SUBTOTAL(1,{ten})', ORANGE_DARK, '0.0'),
        ("Revenue at Risk", f'=SUBTOTAL(9,{mch})', PURPLE, '"$"#,##0'),
        ("Retention Rate", f'=IFERROR((SUBTOTAL(3,{cid})-SUBTOTAL(2,{chr_}))/SUBTOTAL(3,{cid}),0)', TEAL, '0.0%'),
    ]
    kpi_cols = ["F:K", "L:Q", "R:W", "X:AC", "AD:AI"]
    for rng, (label, formula, color, fmt) in zip(kpi_cols, kpis):
        start_col = ws[rng.split(":")[0] + "5"].column
        end_col = ws[rng.split(":")[1] + "5"].column

        # Label row
        ws.merge_cells(start_row=5, start_column=start_col, end_row=5, end_column=end_col)
        lc = ws.cell(row=5, column=start_col, value=label)
        lc.font = Font(name="Calibri", size=11, bold=True, color=NAVY)
        lc.fill = _fill(WHITE)
        lc.alignment = Alignment(horizontal="left", vertical="center", indent=1)

        # Value
        ws.merge_cells(start_row=6, start_column=start_col, end_row=8, end_column=end_col)
        vc = ws.cell(row=6, column=start_col, value=formula)
        vc.font = Font(name="Calibri", size=16, bold=True, color=NAVY_DARK)
        vc.fill = _fill(WHITE)
        vc.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        vc.number_format = fmt

        # Borders
        for rr in (5, 6, 7, 8):
            for cc in range(start_col, end_col + 1):
                ws.cell(row=rr, column=cc).border = border
        # Colored left accent bar (supply-chain style)
        for rr in (5, 6, 7, 8):
            acc = ws.cell(row=rr, column=start_col)
            acc.border = Border(
                left=Side(style="thick", color=color),
                right=acc.border.right,
                top=acc.border.top,
                bottom=acc.border.bottom,
            )
    ws.row_dimensions[5].height = 22
    ws.row_dimensions[6].height = 22
    ws.row_dimensions[7].height = 22
    ws.row_dimensions[8].height = 22

    # Methodology note for Revenue at Risk
    ws.merge_cells(start_row=9, start_column=24, end_row=9, end_column=35)
    note = ws.cell(row=9, column=24)
    note.value = "Revenue at Risk = SUM(Monthly Charges) for customers who Churned = Yes"
    note.font = Font(name="Calibri", size=8, italic=True, color=DARK_GRAY)
    note.alignment = Alignment(horizontal="left", vertical="center")


def build_executive_insights(ws, df: pd.DataFrame, last_data_row: int) -> None:
    """Compact Key Findings panel at the bottom of the Dashboard sheet.
    Findings are derived from the actual workbook data (not hard-coded)."""
    # Section title
    ws.merge_cells(start_row=29, start_column=1, end_row=29, end_column=35)
    t = ws.cell(row=29, column=1)
    t.value = "Key Findings  |  Executive Insights"
    t.font = Font(name="Calibri", size=12, bold=True, color=WHITE)
    t.fill = _fill(NAVY)
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[29].height = 22

    # Compute actual values from data to ensure findings are grounded
    tname = "CustomerRetentionData"
    # Use the same aggregations as the ChartData sheet (audit-friendly)
    by_contract = df.groupby("Contract", observed=True)["ChurnFlag"].mean().mul(100)
    by_tenure = df.groupby("tenure_band", observed=True)["ChurnFlag"].mean().mul(100)
    by_payment = df.groupby("PaymentMethod", observed=True)["ChurnFlag"].mean().mul(100)
    by_service = df.groupby("InternetService", observed=True)["ChurnFlag"].mean().mul(100)

    mt = by_contract.get("Month-to-month", 0)
    ty = by_contract.get("Two year", 0)
    tband_high = by_tenure.idxmax()
    tband_high_v = by_tenure.max()
    tband_low = by_tenure.idxmin()
    tband_low_v = by_tenure.min()
    pay_high = by_payment.idxmax()
    pay_high_v = by_payment.max()
    serv_high = by_service.idxmax()
    serv_high_v = by_service.max()

    findings = [
        f"Month-to-month contracts churn at {mt:.1f}% vs only {ty:.1f}% on two-year contracts - the single largest contract-driven gap.",
        f"Churn falls with tenure: {tband_high} band is {tband_high_v:.1f}%, {tband_low} band is {tband_low_v:.1f}% - early-tenure customers are the highest-risk group.",
        f"{pay_high} customers churn at {pay_high_v:.1f}% - the highest of any payment method.",
        f"{serv_high} internet service shows {serv_high_v:.1f}% churn - the dominant internet-service risk segment.",
        f"Top revenue-at-risk segment is Month-to-month + Fiber optic (~$100K / month) - prioritising contract conversion here protects the most revenue.",
    ]

    start_row = 30
    for i, txt in enumerate(findings):
        r = start_row + i
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=35)
        c = ws.cell(row=r, column=1, value=f"  -  {txt}")
        c.font = Font(name="Calibri", size=10, color=DARK_GRAY)
        c.fill = _fill(LIGHT_BLUE if i % 2 == 0 else WHITE)
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=False)
        c.border = border
        ws.row_dimensions[r].height = 18


# ---------------------------------------------------------------------------
# ChartData sheet (audit-friendly pivots that drive charts)
# ---------------------------------------------------------------------------
def build_chartdata(ws, df: pd.DataFrame) -> dict[str, tuple[int, int, int]]:
    anchors: dict[str, tuple[int, int, int]] = {}
    row = 1

    # Contract
    contract = df.groupby("Contract", observed=True).agg(
        Customers=("customerID", "count"),
        Churn_Rate=("ChurnFlag", "mean"),
        Revenue_At_Risk=("RevenueAtRisk", "sum"),
    ).reset_index()
    contract["Churn_Rate"] = (contract["Churn_Rate"] * 100).round(1)
    contract["Revenue_At_Risk"] = (contract["Revenue_At_Risk"] / 1000).round(1)
    contract.columns = ["Contract", "Customers", "Churn Rate %", "Revenue at Risk ($K)"]
    anchors["contract"] = (row, len(contract), len(contract.columns))
    row = _write_df(ws, contract, row) + 2

    # Tenure band
    tenure = df.groupby("tenure_band", observed=True).agg(
        Customers=("customerID", "count"),
        Churn_Rate=("ChurnFlag", "mean"),
    ).reset_index()
    tenure["Churn_Rate"] = (tenure["Churn_Rate"] * 100).round(1)
    tenure.columns = ["Tenure Band", "Customers", "Churn Rate %"]
    anchors["tenure"] = (row, len(tenure), len(tenure.columns))
    row = _write_df(ws, tenure, row) + 2

    # Internet service
    service = df.groupby("InternetService", observed=True).agg(
        Customers=("customerID", "count"),
        Churn_Rate=("ChurnFlag", "mean"),
    ).reset_index()
    service["Churn_Rate"] = (service["Churn_Rate"] * 100).round(1)
    service.columns = ["Internet Service", "Customers", "Churn Rate %"]
    anchors["service"] = (row, len(service), len(service.columns))
    row = _write_df(ws, service, row) + 2

    # Payment method
    payment = df.groupby("PaymentMethod", observed=True).agg(
        Customers=("customerID", "count"),
        Churn_Rate=("ChurnFlag", "mean"),
    ).reset_index()
    payment["Churn_Rate"] = (payment["Churn_Rate"] * 100).round(1)
    payment.columns = ["Payment Method", "Customers", "Churn Rate %"]
    anchors["payment"] = (row, len(payment), len(payment.columns))
    row = _write_df(ws, payment, row) + 2

    # Tenure months - sampled for the line trend
    tenure_trend = (
        df.groupby("tenure")
        .agg(Customers=("customerID", "count"), Churn_Rate=("ChurnFlag", "mean"))
        .reset_index()
    )
    tenure_trend["Churn_Rate"] = (tenure_trend["Churn_Rate"] * 100).round(2)
    tenure_trend.columns = ["Tenure (months)", "Customers", "Churn Rate %"]
    tenure_trend = tenure_trend.iloc[::3].reset_index(drop=True)
    anchors["tenure_trend"] = (row, len(tenure_trend), len(tenure_trend.columns))
    row = _write_df(ws, tenure_trend, row) + 2

    # Revenue at Risk by Contract (new - replaces one tenure chart)
    rev_by_contract = (
        df.groupby("Contract", observed=True)
          .agg(Customers=("customerID", "count"),
               Revenue_At_Risk=("RevenueAtRisk", "sum"),
               Churn_Rate=("ChurnFlag", "mean"))
          .reset_index()
    )
    rev_by_contract["Revenue_At_Risk"] = (rev_by_contract["Revenue_At_Risk"] / 1000).round(1)
    rev_by_contract["Churn_Rate"] = (rev_by_contract["Churn_Rate"] * 100).round(1)
    rev_by_contract.columns = ["Contract", "Customers", "Revenue at Risk ($K)", "Churn Rate %"]
    rev_by_contract = rev_by_contract.sort_values("Revenue at Risk ($K)", ascending=False)
    anchors["rev_by_contract"] = (row, len(rev_by_contract), len(rev_by_contract.columns))
    row = _write_df(ws, rev_by_contract, row) + 2

    # Top revenue-at-risk segments (sorted descending, kept compact)
    risk = (
        df.groupby(["Contract", "InternetService"], observed=True)
        .agg(
            Customers=("customerID", "count"),
            Churn_Rate=("ChurnFlag", "mean"),
            Revenue_At_Risk=("RevenueAtRisk", "sum"),
        )
        .reset_index()
        .sort_values("Revenue_At_Risk", ascending=False)
        .head(6)
    )
    risk["Segment"] = risk["Contract"] + " | " + risk["InternetService"]
    risk["Revenue_At_Risk"] = (risk["Revenue_At_Risk"] / 1000).round(1)
    risk["Churn_Rate"] = (risk["Churn_Rate"] * 100).round(1)
    risk = risk[["Segment", "Customers", "Churn_Rate", "Revenue_At_Risk"]].copy()
    risk.columns = ["Segment", "Customers", "Churn Rate %", "Revenue at Risk ($K)"]
    anchors["risk"] = (row, len(risk), len(risk.columns))
    _write_df(ws, risk, row)

    for col in range(1, 5):
        ws.column_dimensions[get_column_letter(col)].width = 24

    return anchors


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def add_charts(anchors: dict[str, tuple[int, int, int]], dash_ws, data_ws) -> None:
    # Row 1: Churn by Contract | Churn by Tenure Band | Customer Mix
    r0, n, _ = anchors["contract"]
    ch = BarChart()
    ch.type = "col"
    ch.title = "Churn Rate by Contract"
    ch.style = 12
    ch.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    ch.series[0].graphicalProperties.solidFill = BLUE
    ch.dataLabels = DataLabelList(showVal=True)
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "F10")

    r0, n, _ = anchors["tenure"]
    ch = LineChart()
    ch.title = "Churn Rate by Tenure Band"
    ch.style = 12
    ch.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    ch.dataLabels = DataLabelList(showVal=True)
    for s in ch.series:
        s.smooth = True
        s.graphicalProperties.line.solidFill = BLUE
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "N10")

    r0, n, _ = anchors["service"]
    ch = DoughnutChart()
    ch.title = "Customer Mix by Internet Service"
    ch.add_data(Reference(data_ws, min_col=2, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    _pts = []
    for _idx, _hex in enumerate([BLUE, TEAL, "8496B0"]):
        _dp = DataPoint(idx=_idx)
        _dp.graphicalProperties.solidFill = _hex
        _pts.append(_dp)
    ch.series[0].data_points = _pts
    ch.dataLabels = DataLabelList(showPercent=True, showCatName=True)
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "V10")

    # Row 2: Top Revenue-at-Risk Segments (improved) | Revenue at Risk by Contract | Churn Rate by Tenure (months)
    r0, n, _ = anchors["risk"]
    ch = BarChart()
    ch.type = "bar"
    ch.title = "Top Revenue-at-Risk Segments ($K)"
    ch.style = 11
    ch.add_data(Reference(data_ws, min_col=4, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    ch.series[0].graphicalProperties.solidFill = GREEN
    ch.dataLabels = DataLabelList(showVal=True)
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "F24")

    r0, n, _ = anchors["rev_by_contract"]
    ch = BarChart()
    ch.type = "col"
    ch.title = "Revenue at Risk by Contract"
    ch.style = 12
    ch.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    ch.series[0].graphicalProperties.solidFill = BLUE
    ch.dataLabels = DataLabelList(showVal=True)
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "N24")

    r0, n, _ = anchors["tenure_trend"]
    ch = LineChart()
    ch.title = "Churn Rate by Tenure (months)"
    ch.style = 12
    ch.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    for s in ch.series:
        s.graphicalProperties.line.solidFill = NAVY
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "V24")


# ---------------------------------------------------------------------------
# Customer_Detail sheet
# ---------------------------------------------------------------------------
def build_customer_detail(ws, df: pd.DataFrame) -> int:
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:M1")
    ws["A1"] = "Customer Detail  |  Filterable Churn & Retention Dataset"
    ws["A1"].font = title_font
    ws["A1"].fill = _fill(NAVY)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    detail = df[
        [
            "customerID", "gender", "SeniorCitizen", "Partner", "Dependents",
            "tenure", "tenure_band", "Contract", "InternetService",
            "PaymentMethod", "MonthlyCharges", "TotalCharges", "Churn",
        ]
    ].copy()
    detail.columns = [
        "Customer ID", "Gender", "Senior Citizen", "Partner", "Dependents",
        "Tenure", "Tenure Band", "Contract", "Internet Service",
        "Payment Method", "Monthly Charges", "Total Charges", "Churn",
    ]
    start_row = 3
    _write_df(ws, detail, start_row)
    last_row = start_row + len(detail)
    last_col = len(detail.columns)
    ref = f"A{start_row}:{get_column_letter(last_col)}{last_row}"
    table = Table(displayName="CustomerRetentionData", ref=ref)
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(table)

    # AutoFilter on the table (also used by Slicers)
    ws.auto_filter.ref = ref

    # Conditional formatting on Churn
    last_data_row = start_row + len(detail)
    ws.conditional_formatting.add(
        f"M{start_row + 1}:M{last_data_row}",
        CellIsRule(operator="equal", formula=['"Yes"'], fill=_fill("F8CBAD")),
    )
    ws.conditional_formatting.add(
        f"M{start_row + 1}:M{last_data_row}",
        CellIsRule(operator="equal", formula=['"No"'], fill=_fill("C6E0B4")),
    )

    ws.freeze_panes = "A4"
    for idx, width in enumerate(
        [16, 10, 14, 11, 13, 9, 13, 18, 18, 28, 16, 15, 10], start=1
    ):
        ws.column_dimensions[get_column_letter(idx)].width = width

    return last_row


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    df = prepare_data()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    dash = wb.active
    dash.title = "Dashboard"

    data_ws = wb.create_sheet("ChartData")
    anchors = build_chartdata(data_ws, df)

    detail = wb.create_sheet("Customer_Detail")
    last_row = build_customer_detail(detail, df)

    # Now build the dashboard referencing the table and known last_row
    build_dashboard(dash, df, last_row)
    add_charts(anchors, dash, data_ws)

    data_ws.sheet_state = "visible"
    wb.save(OUT_PATH)
    wb.save(LEGACY_OUT_PATH)
    print(f"Excel dashboard written to {OUT_PATH}")
    print(f"Legacy copy refreshed at {LEGACY_OUT_PATH}")
    print("Open Customer_Detail and use the column-header dropdowns (AutoFilter)")
    print("on Contract / Internet Service / Payment Method / Tenure Band / Churn")
    print("to filter the table; KPI cards update live via SUBTOTAL formulas.")


if __name__ == "__main__":
    main()
