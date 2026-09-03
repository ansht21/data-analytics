"""
build_churn_dashboard.py
------------------------
Generates a polished, multi-sheet Excel dashboard for the Subscription
Retention Analytics project, following the same native-Excel dashboard pattern
used in the Supply Chain project: executive KPI cards, a visible ChartData sheet
with aggregated pivots, native Excel charts, and a filterable customer table.

Run from subscription-retention-analytics/:
    python src/build_churn_dashboard.py

Output:
    excel_analysis/Churn_Dashboard.xlsx
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, DoughnutChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "Telco_Customer_Churn.csv"
OUT_PATH = ROOT / "excel_analysis" / "Churn_Dashboard.xlsx"
LEGACY_OUT_PATH = ROOT / "excel_analysis" / "Churn_Dashboard.xlsm"

NAVY = "172B4D"
BLUE = "2F75B5"
TEAL = "00A6A6"
LIGHT_BLUE = "DDEBF7"
LIGHT_TEAL = "DDEFEF"
WHITE = "FFFFFF"
RED = "C00000"
ORANGE = "F4B183"
DARK_GRAY = "404040"

title_font = Font(name="Calibri", size=18, bold=True, color=WHITE)
kpi_label_font = Font(name="Calibri", size=10, bold=True, color=WHITE)
kpi_value_font = Font(name="Calibri", size=16, bold=True, color=WHITE)
header_font = Font(name="Calibri", size=11, bold=True, color=WHITE)
section_font = Font(name="Calibri", size=13, bold=True, color=NAVY)
small_note_font = Font(name="Calibri", size=10, italic=True, color=DARK_GRAY)
thin = Side(style="thin", color="BFBFBF")
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
                cell.alignment = Alignment(horizontal="center")
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


def build_dashboard(ws, df: pd.DataFrame) -> None:
    """Create a premium executive dashboard sheet."""
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A8"

    # Executive title band
    ws.merge_cells("B2:K2")
    title = ws["B2"]
    title.value = "Subscription Retention Performance Dashboard"
    title.font = Font(name="Calibri", size=20, bold=True, color=WHITE)
    title.fill = _fill(NAVY)
    title.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 36

    ws.merge_cells("B3:K3")
    subtitle = ws["B3"]
    subtitle.value = "Executive view of churn risk, retention health, revenue exposure, and priority customer segments"
    subtitle.font = Font(name="Calibri", size=11, italic=True, color=DARK_GRAY)
    subtitle.fill = _fill(LIGHT_BLUE)
    subtitle.alignment = Alignment(horizontal="center")

    # KPI cards in two-color premium style
    kpis = [
        ("Customers", f"{len(df):,}", NAVY),
        ("Churn Rate", f"{df['ChurnFlag'].mean():.1%}", RED),
        ("Retained", f"{int(df['RetainedFlag'].sum()):,}", TEAL),
        ("Churned", f"{int(df['ChurnFlag'].sum()):,}", RED),
        ("Monthly Revenue", f"${df['MonthlyCharges'].sum()/1000:,.1f}K", NAVY),
        ("Revenue at Risk", f"${df['RevenueAtRisk'].sum()/1000:,.1f}K", RED),
        ("Avg Tenure", f"{df['tenure'].mean():,.1f} mo", TEAL),
        ("Avg Monthly", f"${df['MonthlyCharges'].mean():,.2f}", NAVY),
    ]
    for i, (label, value, color) in enumerate(kpis, start=2):
        lab = ws.cell(row=5, column=i, value=label)
        lab.font = kpi_label_font
        lab.fill = _fill(color)
        lab.alignment = Alignment(horizontal="center")
        lab.border = border

        val = ws.cell(row=6, column=i, value=value)
        val.font = Font(name="Calibri", size=15, bold=True, color=WHITE)
        val.fill = _fill(color)
        val.alignment = Alignment(horizontal="center")
        val.border = border
        ws.column_dimensions[get_column_letter(i)].width = 16
    ws.row_dimensions[5].height = 22
    ws.row_dimensions[6].height = 28

    # Insight/action panel, like a better executive dashboard cover page.
    insights = [
        "Highest churn driver: month-to-month contracts",
        "Early tenure customers need onboarding and save offers",
        "Revenue-at-risk view prioritizes retention spend by dollars",
        "Use Customer_Detail filters for Contract, Tenure Band, Service, Payment Method, and Churn",
    ]
    # The action panel begins after the two aligned chart rows.
    ws.merge_cells("B40:K40")
    ws["B40"] = "Recommended Retention Actions"
    ws["B40"].font = Font(name="Calibri", size=14, bold=True, color=WHITE)
    ws["B40"].fill = _fill(NAVY)
    ws["B40"].alignment = Alignment(horizontal="center")
    for row, item in enumerate(insights, start=41):
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=11)
        c = ws.cell(row=row, column=2, value=f"- {item}")
        c.font = Font(name="Calibri", size=11, color=DARK_GRAY)
        c.fill = _fill(LIGHT_TEAL if row % 2 else LIGHT_BLUE)
        c.alignment = Alignment(vertical="center")
        ws.row_dimensions[row].height = 22

    ws.merge_cells("B8:K8")
    note = ws["B8"]
    note.value = "Native Excel charts below are clickable/selectable. Open Customer_Detail to use filter dropdowns for interactive analysis."
    note.font = small_note_font
    note.fill = _fill(LIGHT_BLUE)
    note.alignment = Alignment(horizontal="center")

    # Light background framing for chart area
    for row in range(9, 39):
        for col in range(2, 12):
            ws.cell(row=row, column=col).fill = _fill("F7F9FC")

def build_chartdata(ws, df: pd.DataFrame) -> dict[str, tuple[int, int, int]]:
    anchors: dict[str, tuple[int, int, int]] = {}
    row = 1

    contract = df.groupby("Contract", observed=True).agg(
        Customers=("customerID", "count"), Churn_Rate=("ChurnFlag", "mean"), Revenue_At_Risk=("RevenueAtRisk", "sum")
    ).reset_index()
    contract["Churn_Rate"] = (contract["Churn_Rate"] * 100).round(1)
    contract["Revenue_At_Risk"] = (contract["Revenue_At_Risk"] / 1000).round(1)
    contract.columns = ["Contract", "Customers", "Churn Rate %", "Revenue at Risk ($K)"]
    anchors["contract"] = (row, len(contract), len(contract.columns))
    row = _write_df(ws, contract, row) + 2

    tenure = df.groupby("tenure_band", observed=True).agg(
        Customers=("customerID", "count"), Churn_Rate=("ChurnFlag", "mean")
    ).reset_index()
    tenure["Churn_Rate"] = (tenure["Churn_Rate"] * 100).round(1)
    tenure.columns = ["Tenure Band", "Customers", "Churn Rate %"]
    anchors["tenure"] = (row, len(tenure), len(tenure.columns))
    row = _write_df(ws, tenure, row) + 2

    service = df.groupby("InternetService", observed=True).agg(
        Customers=("customerID", "count"), Churn_Rate=("ChurnFlag", "mean")
    ).reset_index()
    service["Churn_Rate"] = (service["Churn_Rate"] * 100).round(1)
    service.columns = ["Internet Service", "Customers", "Churn Rate %"]
    anchors["service"] = (row, len(service), len(service.columns))
    row = _write_df(ws, service, row) + 2

    payment = df.groupby("PaymentMethod", observed=True).agg(
        Customers=("customerID", "count"), Churn_Rate=("ChurnFlag", "mean")
    ).reset_index()
    payment["Churn_Rate"] = (payment["Churn_Rate"] * 100).round(1)
    payment.columns = ["Payment Method", "Customers", "Churn Rate %"]
    anchors["payment"] = (row, len(payment), len(payment.columns))
    row = _write_df(ws, payment, row) + 2

    risk = df.groupby(["Contract", "InternetService"], observed=True).agg(
        Customers=("customerID", "count"), Churn_Rate=("ChurnFlag", "mean"), Revenue_At_Risk=("RevenueAtRisk", "sum")
    ).reset_index().sort_values("Revenue_At_Risk", ascending=False).head(8)
    risk["Segment"] = risk["Contract"] + " | " + risk["InternetService"]
    risk["Revenue_At_Risk"] = (risk["Revenue_At_Risk"] / 1000).round(1)
    risk["Churn_Rate"] = (risk["Churn_Rate"] * 100).round(1)
    risk = risk[["Segment", "Customers", "Churn_Rate", "Revenue_At_Risk"]]
    risk.columns = ["Segment", "Customers", "Churn Rate %", "Revenue at Risk ($K)"]
    anchors["risk"] = (row, len(risk), len(risk.columns))
    _write_df(ws, risk, row)

    for col in range(1, 5):
        ws.column_dimensions[get_column_letter(col)].width = 24
    return anchors


def add_charts(data_ws, anchors: dict[str, tuple[int, int, int]], dash_ws) -> None:
    r0, n, _ = anchors["contract"]
    chart = BarChart()
    chart.type = "col"
    chart.title = "Churn Rate by Contract Type"
    chart.y_axis.title = "Churn Rate %"
    chart.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    chart.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    chart.legend = None
    chart.width = 10.8
    chart.height = 7.2
    dash_ws.add_chart(chart, "B10")

    r0, n, _ = anchors["tenure"]
    chart = LineChart()
    chart.title = "Churn Falls as Tenure Increases"
    chart.y_axis.title = "Churn Rate %"
    chart.add_data(Reference(data_ws, min_col=3, min_row=r0, max_row=r0 + n), titles_from_data=True)
    chart.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    chart.legend = None
    chart.width = 10.8
    chart.height = 7.2
    dash_ws.add_chart(chart, "G10")

    r0, n, _ = anchors["service"]
    chart = DoughnutChart()
    chart.title = "Customers by Internet Service"
    chart.add_data(Reference(data_ws, min_col=2, min_row=r0, max_row=r0 + n), titles_from_data=True)
    chart.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    chart.width = 10.8
    chart.height = 7.2
    dash_ws.add_chart(chart, "B25")

    r0, n, _ = anchors["risk"]
    chart = BarChart()
    chart.type = "bar"
    chart.title = "Top Revenue-at-Risk Segments"
    chart.x_axis.title = "Revenue at Risk ($K)"
    chart.add_data(Reference(data_ws, min_col=4, min_row=r0, max_row=r0 + n), titles_from_data=True)
    chart.set_categories(Reference(data_ws, min_col=1, min_row=r0 + 1, max_row=r0 + n))
    chart.legend = None
    chart.width = 10.8
    chart.height = 7.2
    dash_ws.add_chart(chart, "G25")


def build_customer_detail(ws, df: pd.DataFrame) -> None:
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:M1")
    ws["A1"] = "Customer Detail | Filterable Churn & Retention Dataset"
    ws["A1"].font = title_font
    ws["A1"].fill = _fill(NAVY)
    ws["A1"].alignment = Alignment(horizontal="center")

    detail = df[[
        "customerID", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure", "tenure_band",
        "Contract", "InternetService", "PaymentMethod", "MonthlyCharges", "TotalCharges", "Churn"
    ]].copy()
    detail.columns = [
        "Customer ID", "Gender", "Senior Citizen", "Partner", "Dependents", "Tenure", "Tenure Band",
        "Contract", "Internet Service", "Payment Method", "Monthly Charges", "Total Charges", "Churn"
    ]
    start_row = 3
    _write_df(ws, detail, start_row)
    last_row = start_row + len(detail)
    last_col = len(detail.columns)
    ref = f"A{start_row}:{get_column_letter(last_col)}{last_row}"
    table = Table(displayName="CustomerRetentionData", ref=ref)
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(table)
    ws.freeze_panes = "A4"
    for idx, width in enumerate([16, 10, 14, 11, 13, 9, 13, 18, 18, 28, 16, 15, 10], start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width


def main() -> None:
    df = prepare_data()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    dashboard = wb.active
    dashboard.title = "Dashboard"
    build_dashboard(dashboard, df)

    chartdata = wb.create_sheet("ChartData")
    anchors = build_chartdata(chartdata, df)
    add_charts(chartdata, anchors, dashboard)

    detail = wb.create_sheet("Customer_Detail")
    build_customer_detail(detail, df)

    # Keep ChartData visible like the Supply Chain reference workbook so reviewers can audit chart pivots.
    chartdata.sheet_state = "visible"
    wb.save(OUT_PATH)
    wb.save(LEGACY_OUT_PATH)
    print(f"Excel dashboard written to {OUT_PATH}")
    print(f"Legacy copy refreshed at {LEGACY_OUT_PATH}")


if __name__ == "__main__":
    main()
