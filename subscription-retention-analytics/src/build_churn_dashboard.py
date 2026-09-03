"""
build_churn_dashboard.py  (upgraded, layout-matched to supply chain reference)
-----------------------------------------------------------------------------
Generates a polished Excel dashboard for the Subscription Retention Analytics
project. Layout mirrors the supply chain reference: title bar, Filters panel
on the left, KPI cards on the top right, and a 3x2 grid of native Excel
charts underneath. ChartData sheet provides audit-friendly pivot tables, and
Customer_Detail is a fully filterable Excel table.

Run from subscription-retention-analytics/:
    python src/build_churn_dashboard.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, DoughnutChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "Telco_Customer_Churn.csv"
OUT_PATH = ROOT / "excel_analysis" / "Churn_Dashboard.xlsx"
LEGACY_OUT_PATH = ROOT / "excel_analysis" / "Churn_Dashboard.xlsm"

# Palette (matches the supply chain reference dashboard)
NAVY = "1F3864"          # main title bar
NAVY_DARK = "172B4D"     # filters section bars
BLUE = "2F75B5"          # accent blue (KPI labels)
TEAL = "00A6A6"
LIGHT_BLUE = "DDEBF7"
LIGHT_TEAL = "DDEFEF"
BG = "F4F6FA"            # chart area background
WHITE = "FFFFFF"
RED = "C00000"
ORANGE = "F4B183"
ORANGE_DARK = "C65911"
GREEN = "548235"
DARK_GRAY = "404040"
BORDER_GRAY = "BFBFBF"
PANEL_BLUE = "5B7BB7"    # filter chip fill

title_font = Font(name="Calibri", size=22, bold=True, color=WHITE)
kpi_label_font = Font(name="Calibri", size=11, bold=True, color=WHITE)
kpi_value_font = Font(name="Calibri", size=22, bold=True, color=NAVY)
header_font = Font(name="Calibri", size=11, bold=True, color=WHITE)
small_note_font = Font(name="Calibri", size=10, italic=True, color=DARK_GRAY)
filter_label_font = Font(name="Calibri", size=11, bold=True, color=WHITE)
filter_item_font = Font(name="Calibri", size=10, bold=True, color=WHITE)

thin = Side(style="thin", color=BORDER_GRAY)
border = Border(left=thin, right=thin, top=thin, bottom=thin)


def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def _write_df(ws, df: pd.DataFrame, start_row: int = 1, start_col: int = 1) -> int:
    """Write a dataframe with styled headers and return the next blank row."""
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
# Dashboard layout (matches supply chain reference image)
# ---------------------------------------------------------------------------
# Column layout:
#   A-D : Filters panel  (width 14 each)
#   E   : spacer (width 4)
#   F-AB: KPI cards and chart area (width 12 each)
# Rows:
#   1-3 : title bar
#   4   : subtitle / spacer
#   5-8 : KPI cards (top right), filters header
#   9-22: filter chips
#   23-25: chart row 1 (3 charts)
#   26-29: chart row 2 (3 charts)
#   30   : footer
# ---------------------------------------------------------------------------

def build_dashboard(ws, df: pd.DataFrame) -> None:
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 90
    ws.freeze_panes = "A5"

    # Column widths (matching reference proportions)
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 4
    for col_letter in "FGHIJKLMNOPQRSTUVWXYZ":
        ws.column_dimensions[col_letter].width = 12

    # Title bar (row 1-3)
    ws.merge_cells("A1:AB3")
    title = ws["A1"]
    title.value = "Executive Supply Chain Analytics  Dashboard"
    title.font = title_font
    title.fill = _fill(NAVY)
    title.alignment = Alignment(horizontal="center", vertical="center")
    for r in (1, 2, 3):
        ws.row_dimensions[r].height = 24

    # Row 4 spacer
    ws.row_dimensions[4].height = 8

    # --- Filters panel (left, rows 5-22) ---
    ws.merge_cells("A5:D6")
    f_title = ws["A5"]
    f_title.value = "Filters"
    f_title.font = Font(name="Calibri", size=18, bold=True, color=WHITE)
    f_title.alignment = Alignment(horizontal="center", vertical="center")
    f_title.fill = _fill(NAVY_DARK)

    sections = [
        ("Category", ["Month-to-month", "One year", "Two year"]),
        ("Supplier", sorted(df["InternetService"].dropna().unique().tolist())),
        ("Delivery Status", ["Churned", "Retained"]),
        ("Warehouse Code", ["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"]),
    ]
    row = 7
    for label, items in sections:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
        c = ws.cell(row=row, column=1, value=label)
        c.font = filter_label_font
        c.fill = _fill(NAVY_DARK)
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        c.border = border
        ws.row_dimensions[row].height = 22
        row += 1
        # Filter chips: 4 per row in columns A-D
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
            ws.row_dimensions[r].height = 22
        row += (len(items) + 3) // 4 + 1

    # --- KPI cards (top right, rows 5-8) ---
    # 5 KPI cards across columns F to AB (each 5 columns wide)
    kpis = [
        ("Total Customers", '=ChartData!B3', GREEN),
        ("Churn Rate", '=TEXT(ChartData!B3,"#,##0")&" of "&TEXT(ChartData!B3,"#,##0")', RED),  # placeholder
        ("Avg Tenure", f'=TEXT({df["tenure"].mean():.1f},"0.0")&" mo"', ORANGE_DARK),
        ("Revenue at Risk", f'="$"&TEXT({df["RevenueAtRisk"].sum()/1000:.0f},"#,##0")&"K"', RED),
        ("Retention Rate", f'={1-df["ChurnFlag"].mean():.1%}', GREEN),
    ]
    # Rebuild with correct churn-rate formula
    kpis = [
        ("Total Customers", f'={len(df):,}', GREEN),
        ("Churn Rate", f'={df["ChurnFlag"].mean():.1%}', RED),
        ("Avg Tenure", f'={df["tenure"].mean():.1f}&" mo"', ORANGE_DARK),
        ("Revenue at Risk", f'="$"&TEXT({df["RevenueAtRisk"].sum()/1000:.0f},"#,##0")&"K"', RED),
        ("Retention Rate", f'={1-df["ChurnFlag"].mean():.1%}', GREEN),
    ]
    kpi_cols = ["F:K", "L:Q", "R:W", "X:AC", "AD:AI"]
    kpi_colors = {
        "F:K": GREEN, "L:Q": RED, "R:W": ORANGE_DARK,
        "X:AC": NAVY, "AD:AI": TEAL,
    }
    for rng, (label, value, color) in zip(kpi_cols, kpis):
        # Label row (row 5)
        start_col = ws[rng.split(":")[0] + "5"].column
        end_col = ws[rng.split(":")[1] + "5"].column
        ws.merge_cells(start_row=5, start_column=start_col, end_row=5, end_column=end_col)
        lc = ws.cell(row=5, column=start_col, value=label)
        lc.font = kpi_label_font
        lc.fill = _fill(color)
        lc.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        # Value rows (row 6-8 merged)
        ws.merge_cells(start_row=6, start_column=start_col, end_row=8, end_column=end_col)
        vc = ws.cell(row=6, column=start_col, value=value)
        vc.font = kpi_value_font
        vc.fill = _fill(WHITE)
        vc.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        # Outer borders
        for rr in (5, 6, 7, 8):
            for cc in range(start_col, end_col + 1):
                ws.cell(row=rr, column=cc).border = border
    ws.row_dimensions[5].height = 22
    ws.row_dimensions[6].height = 18
    ws.row_dimensions[7].height = 18
    ws.row_dimensions[8].height = 18

    # --- Chart area background (rows 9-29, columns F-AI) ---
    for rr in range(9, 30):
        for cc in range(6, 36):
            ws.cell(row=rr, column=cc).fill = _fill(BG)

    # --- Footer (row 31) ---
    ws.row_dimensions[30].height = 8
    ws.merge_cells(start_row=31, start_column=1, end_row=31, end_column=35)
    foot = ws.cell(row=31, column=1)
    foot.value = "Created by Ansh Thakur  |  Data Analyst Portfolio Dashboard"
    foot.font = Font(name="Calibri", size=11, italic=True, bold=True, color=NAVY)
    foot.alignment = Alignment(horizontal="center", vertical="center")
    foot.fill = _fill(WHITE)
    ws.row_dimensions[31].height = 26

    # Ensure proper column widths for KPI area (some need slightly wider for the values)
    # Already set to 12 above; F:K through AD:AI cover 5*5=25 cols (F..AI)


# ---------------------------------------------------------------------------
# ChartData sheet (pivot tables used by chart formulas and KPIs)
# ---------------------------------------------------------------------------
def build_chartdata(ws, df: pd.DataFrame) -> dict[str, tuple[int, int, int]]:
    anchors: dict[str, tuple[int, int, int]] = {}
    row = 1

    # KPI summary table — first 3 rows are referenced by chart data
    kpi = pd.DataFrame([{
        "TotalCustomers": len(df),
        "ChurnRate": round(df["ChurnFlag"].mean(), 4),
        "Churned": int(df["ChurnFlag"].sum()),
        "Retained": int(df["RetainedFlag"].sum()),
        "MonthlyRevenue": round(df["MonthlyCharges"].sum(), 2),
        "RevenueAtRisk": round(df["RevenueAtRisk"].sum(), 2),
        "AvgTenure": round(df["tenure"].mean(), 2),
        "AvgMonthly": round(df["MonthlyCharges"].mean(), 2),
    }])
    ws.cell(row=1, column=1, value="KPI")
    ws.cell(row=1, column=2, value="Value")
    for c in (ws.cell(row=1, column=1), ws.cell(row=1, column=2)):
        c.font = header_font
        c.fill = _fill(BLUE)
        c.alignment = Alignment(horizontal="center")
        c.border = border
    for i, (k, v) in enumerate(kpi.iloc[0].items(), start=2):
        ws.cell(row=i, column=1, value=k).font = Font(bold=True)
        ws.cell(row=i, column=1).fill = _fill(LIGHT_BLUE)
        ws.cell(row=i, column=1).border = border
        cell = ws.cell(row=i, column=2, value=v)
        cell.border = border
        cell.alignment = Alignment(horizontal="right")
    row = 11  # leave gap

    # --- Churn Rate by Contract (column) ---
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

    # --- Churn Rate by Tenure Band (line) ---
    tenure = df.groupby("tenure_band", observed=True).agg(
        Customers=("customerID", "count"),
        Churn_Rate=("ChurnFlag", "mean"),
    ).reset_index()
    tenure["Churn_Rate"] = (tenure["Churn_Rate"] * 100).round(1)
    tenure.columns = ["Tenure Band", "Customers", "Churn Rate %"]
    anchors["tenure"] = (row, len(tenure), len(tenure.columns))
    row = _write_df(ws, tenure, row) + 2

    # --- Customer Mix by Internet Service (doughnut) ---
    service = df.groupby("InternetService", observed=True).agg(
        Customers=("customerID", "count"),
        Churn_Rate=("ChurnFlag", "mean"),
    ).reset_index()
    service["Churn_Rate"] = (service["Churn_Rate"] * 100).round(1)
    service.columns = ["Internet Service", "Customers", "Churn Rate %"]
    anchors["service"] = (row, len(service), len(service.columns))
    row = _write_df(ws, service, row) + 2

    # --- Churn Rate by Payment Method (column) ---
    payment = df.groupby("PaymentMethod", observed=True).agg(
        Customers=("customerID", "count"),
        Churn_Rate=("ChurnFlag", "mean"),
    ).reset_index()
    payment["Churn_Rate"] = (payment["Churn_Rate"] * 100).round(1)
    payment.columns = ["Payment Method", "Customers", "Churn Rate %"]
    anchors["payment"] = (row, len(payment), len(payment.columns))
    row = _write_df(ws, payment, row) + 2

    # --- Churn Rate by Tenure months (line) ---
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

    # --- Top Revenue at Risk Segments (bar) ---
    risk = (
        df.groupby(["Contract", "InternetService"], observed=True)
        .agg(
            Customers=("customerID", "count"),
            Churn_Rate=("ChurnFlag", "mean"),
            Revenue_At_Risk=("RevenueAtRisk", "sum"),
        )
        .reset_index()
        .sort_values("Revenue_At_Risk", ascending=False)
        .head(8)
    )
    risk["Segment"] = risk["Contract"] + " | " + risk["InternetService"]
    risk["Revenue_At_Risk"] = (risk["Revenue_At_Risk"] / 1000).round(1)
    risk["Churn_Rate"] = (risk["Churn_Rate"] * 100).round(1)
    risk = risk[["Segment", "Customers", "Churn_Rate", "Revenue_At_Risk"]].copy()
    risk.columns = ["Segment", "Customers", "Churn Rate %", "Revenue at Risk ($K)"]
    anchors["risk"] = (row, len(risk), len(risk.columns))
    _write_df(ws, risk, row)

    for col in range(1, 5):
        ws.column_dimensions[get_column_letter(col)].width = 26

    return anchors


# ---------------------------------------------------------------------------
# Charts (3x2 grid matching the reference image positions)
# ---------------------------------------------------------------------------
def add_charts(anchors: dict[str, tuple[int, int, int]], dash_ws, data_ws) -> None:
    # Row 1: 3 charts across columns F-AB
    #   F9  : Churn Rate by Contract  (column)
    #   N9  : Churn by Tenure Band     (line)
    #   V9  : Delivery Status / Customer Mix (doughnut)
    # Row 2: 3 charts across columns F-AB
    #   F23 : Revenue at Risk by Segment (bar horizontal)
    #   N23 : Churn by Payment Method    (column)
    #   V23 : Churn by Tenure months     (line)

    # 1) Churn Rate by Contract
    r0, n, _ = anchors["contract"]
    ch = BarChart()
    ch.type = "col"
    ch.title = "Churn Rate by Contract"
    ch.y_axis.title = "Churn Rate %"
    ch.x_axis.title = "Contract"
    ch.style = 12
    ch.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    ch.dataLabels = DataLabelList(showVal=True)
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "F9")

    # 2) Churn Rate by Tenure Band
    r0, n, _ = anchors["tenure"]
    ch = LineChart()
    ch.title = "Churn Rate by Tenure Band"
    ch.y_axis.title = "Churn Rate %"
    ch.x_axis.title = "Tenure Band"
    ch.style = 12
    ch.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    ch.dataLabels = DataLabelList(showVal=True)
    for s in ch.series:
        s.smooth = True
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "N9")

    # 3) Customer Mix by Internet Service (doughnut)
    r0, n, _ = anchors["service"]
    ch = DoughnutChart()
    ch.title = "Customer Mix by Internet Service"
    ch.add_data(Reference(data_ws, min_col=2, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.dataLabels = DataLabelList(showPercent=True, showCatName=True)
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "V9")

    # 4) Top Revenue at Risk Segments (horizontal bar)
    r0, n, _ = anchors["risk"]
    ch = BarChart()
    ch.type = "bar"
    ch.title = "Top Revenue-at-Risk Segments"
    ch.x_axis.title = "Revenue at Risk ($K)"
    ch.style = 11
    ch.add_data(Reference(data_ws, min_col=4, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    ch.dataLabels = DataLabelList(showVal=True)
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "F23")

    # 5) Churn Rate by Payment Method (column)
    r0, n, _ = anchors["payment"]
    ch = BarChart()
    ch.type = "col"
    ch.title = "Churn Rate by Payment Method"
    ch.y_axis.title = "Churn Rate %"
    ch.x_axis.title = "Payment Method"
    ch.style = 12
    ch.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    ch.dataLabels = DataLabelList(showVal=True)
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "N23")

    # 6) Churn Rate by Tenure (line) - months view
    r0, n, _ = anchors["tenure_trend"]
    ch = LineChart()
    ch.title = "Churn Rate by Tenure (months)"
    ch.y_axis.title = "Churn Rate %"
    ch.x_axis.title = "Tenure (months)"
    ch.style = 12
    ch.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    ch.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    ch.legend = None
    ch.width = 11
    ch.height = 7
    dash_ws.add_chart(ch, "V23")


# ---------------------------------------------------------------------------
# Customer detail sheet
# ---------------------------------------------------------------------------
def build_customer_detail(ws, df: pd.DataFrame) -> None:
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    df = prepare_data()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    dash = wb.active
    dash.title = "Dashboard"
    build_dashboard(dash, df)

    data_ws = wb.create_sheet("ChartData")
    anchors = build_chartdata(data_ws, df)
    add_charts(anchors, dash, data_ws)

    detail = wb.create_sheet("Customer_Detail")
    build_customer_detail(detail, df)

    data_ws.sheet_state = "visible"
    wb.save(OUT_PATH)
    wb.save(LEGACY_OUT_PATH)
    print(f"Excel dashboard written to {OUT_PATH}")
    print(f"Legacy copy refreshed at {LEGACY_OUT_PATH}")


if __name__ == "__main__":
    main()
