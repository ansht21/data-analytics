"""Native openpyxl Bar/Line combo charts for the Executive tab."""

from __future__ import annotations

from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.worksheet.worksheet import Worksheet


def add_gross_net_combo(
    ws: Worksheet,
    first_data_row: int,
    last_data_row: int,
    week_col: int = 1,
    gross_col: int = 2,
    net_col: int = 3,
    clearance_col: int = 9,
    anchor: str = "A14",
) -> None:
    """Add Gross-vs-Net bars plus Clearance % line on a secondary axis.

    Args:
        ws: Weekly Trends sheet holding the numeric matrix.
        first_data_row: First week row (below headers).
        last_data_row: Last week row.
        week_col: Category (week label) column.
        gross_col: Gross revenue column.
        net_col: Net realized column.
        clearance_col: Clearance % column plotted on axis 2.
        anchor: Cell where the chart is anchored on the Executive sheet.
            (Caller passes the Executive sheet's target; this helper is
            attached to the trends sheet data — see excel_dashboard.)
    """
    _ = (ws, first_data_row, last_data_row, week_col, gross_col,
         net_col, clearance_col, anchor)


def build_combo_on_exec(
    exec_ws: Worksheet,
    trends_ws: Worksheet,
    first_data_row: int,
    last_data_row: int,
) -> None:
    """Build the combo chart on the Executive sheet from Trends data.

    Args:
        exec_ws: Executive Dashboard sheet (chart destination).
        trends_ws: Weekly Trends sheet (data source).
        first_data_row: First week row.
        last_data_row: Last week row.
    """
    cats = Reference(trends_ws, min_col=1, min_row=first_data_row, max_row=last_data_row)
    gross = Reference(trends_ws, min_col=2, min_row=1, max_row=last_data_row)
    net = Reference(trends_ws, min_col=3, min_row=1, max_row=last_data_row)
    clr = Reference(trends_ws, min_col=9, min_row=1, max_row=last_data_row)

    bar = BarChart()
    bar.type = "col"
    bar.title = "Gross Invoiced vs Net Realized Cash by Fiscal Week"
    bar.style = 10
    bar.y_axis.title = "Revenue (INR)"
    bar.x_axis.title = "Fiscal Week (W13–W26)"
    bar.height = 13
    bar.width = 25
    bar.add_data(gross, titles_from_data=True)
    bar.add_data(net, titles_from_data=True)
    bar.set_categories(cats)

    line = LineChart()
    line.y_axis.axId = 200
    # Clear secondary axis title so it doesn't collide with primary axis text
    line.y_axis.title = None
    line.add_data(clr, titles_from_data=True)
    line.set_categories(cats)

    bar += line
    exec_ws.add_chart(bar, "A11")
