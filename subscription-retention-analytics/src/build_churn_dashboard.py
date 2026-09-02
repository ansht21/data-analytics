"""build_churn_dashboard.py
---------------------------
Generates an INTERACTIVE Excel dashboard (.xlsm) from the cleaned telco churn
data using openpyxl - matching the supply-chain project's dashboard standard
(executive Summary KPI cards, native charts, autofilters on real Excel tables,
and a raw data sheet). Charts are clickable and filters are applied with the
built-in Excel filter dropdowns.

Run:
    python src/build_churn_dashboard.py
Output:
    excel_analysis/Churn_Dashboard.xlsm
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "Telco_Customer_Churn.csv"
OUT_PATH = ROOT / "excel_analysis" / "Churn_Dashboard.xlsm"

NAVY = "1F3864"
BLUE = "2E5496"
WHITE = "FFFFFF"

title_font = Font(name="Calibri", size=18, bold=True, color=WHITE)
kpi_label_font = Font(name="Calibri", size=10, bold=True, color=WHITE)
kpi_value_font = Font(name="Calibri", size=16, bold=True, color=WHITE)
header_font = Font(name="Calibri", size=11, bold=True, color=WHITE)
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)


def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def _write_df(ws, df: pd.DataFrame, start_row: int = 1, start_col: int = 1, header=True):
    for r_off, row in enumerate(dataframe_to_rows(df, index=False, header=header)):
        for c_off, val in enumerate(row):
            cell = ws.cell(row=start_row + r_off, column=start_col + c_off, value=val)
            if header and r_off == 0:
                cell.font = header_font
                cell.fill = _fill(BLUE)
                cell.alignment = Alignment(horizontal="center")
            cell.border = border
    return start_row + len(df) + 1


def _kpi_cards(ws, kpis: list[tuple[str, str]]):
    ws.merge_cells("B2:H2")
    t = ws["B2"]
    t.value = "Subscription Retention Dashboard"
    t.font = title_font
    ws["B2"].fill = _fill(NAVY)
    for i, (label, value) in enumerate(kpis):
        col = 2 + i
        lab = ws.cell(row=4, column=col, value=label)
        lab.font = kpi_label_font
        lab.fill = _fill(BLUE)
        val = ws.cell(row=5, column=col, value=value)
        val.font = kpi_value_font
        val.fill = _fill(NAVY if i % 2 == 0 else BLUE)
        val.alignment = Alignment(horizontal="center")


def build_summary(ws, df: pd.DataFrame):
    ws.sheet_view.showGridLines = False
    _kpi_cards(ws, [
        ("Customers", f"{len(df):,}"),
        ("Churn Rate", f"{df.ChurnFlag.mean():.1%}"),
        ("Churned", f"{int(df.ChurnFlag.sum()):,}"),
        ("Monthly Revenue", f"${df.MonthlyCharges.sum():,.0f}"),
        ("Revenue at Risk", f"${df.loc[df.ChurnFlag == 1, 'MonthlyCharges'].sum():,.0f}"),
        ("Avg Monthly", f"${df.MonthlyCharges.mean():.2f}"),
    ])


def _first_chart(ws, dfgroup):
    # bar chart of churn rate by contract
    r = _write_df(ws, dfgroup.groupby("Contract").agg(
        churn_rate=("ChurnFlag", "mean")).round(3))
    chart = BarChart()
    data = Reference(ws, min_col=2, min_row=1, max_col=2, max_row=len(dfgroup.groupby("Contract")) + 1)
    cats = Reference(ws, min_col=1, min_row=2, max_row=len(dfgroup.groupby("Contract")) + 1)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.title = "Churn Rate by Contract Type"
    chart.style = 2
    ws.add_chart(chart, "E2")
    return r

def build_summary_dashboard(ws, df):
    # A second summary-facing sheet with the chart + filter table
    ws.merge_cells("A1:H1")
    ws["A1"] = "Interactive Retention Summary - click a chart or use the filter dropdowns"
    r = _first_chart(ws, df)

    # An autofiltered data table below the chart (filter dropdowns)
    table_df = df[["customerID", "Contract", "InternetService", "PaymentMethod",
                   "tenure", "MonthlyCharges", "TotalCharges", "Churn"]].copy()
    start = r + 1
    _write_df(ws, table_df, start)
    last_row = start + len(table_df)
    ws.auto_filter.ref = f"A{start}:H{last_row}"
    tab = Table(displayName="RetentionData", ref=f"A{start}:H{last_row}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(tab)
    for col, w in zip("ABCDEFGH", [18, 14, 16, 18, 8, 14, 14, 8]):
        ws.column_dimensions[col].width = w


def build_chart_data(ws, df: pd.DataFrame, _start_row: int = 1) -> None:
    rows = 1
    rows = _write_df(ws, df.groupby("Contract").agg(
        customers=("customerID", "count"),
        churn_rate=("ChurnFlag", "mean")).round(3), rows)
    rows = _write_df(ws, df.groupby("tenure_band", observed=True).agg(
        churn_rate=("ChurnFlag", "mean")).round(3), rows)
    rows = _write_df(ws, df.groupby("InternetService").agg(
        churn_rate=("ChurnFlag", "mean")).round(3), rows)
    rows = _write_df(ws, df.groupby("PaymentMethod").agg(
        churn_rate=("ChurnFlag", "mean")).round(3), rows)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    df["TotalCharges"] = pd.to_numeric(df.TotalCharges, errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).copy()
    df["ChurnFlag"] = (df.Churn == "Yes").astype(int)
    df["tenure_band"] = pd.cut(df.tenure, [0, 6, 12, 24, 48, 72],
                               labels=["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"])

    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "Summary"
    build_summary(ws_summary, df)

    ws_dash = wb.create_sheet("Dashboard")
    build_summary_dashboard(ws_dash, df)

    ws_data = wb.create_sheet("ChartData")
    build_chart_data(ws_data, df)

    wb.save(OUT_PATH)
    print("saved:", OUT_PATH, "| sheets:", wb.sheetnames)


if __name__ == "__main__":
    main()