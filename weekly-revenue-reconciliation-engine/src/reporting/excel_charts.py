"""Dark-styled native Excel charts for the Command Center tab.

openpyxl builds real Excel charts (not images), so the workbook stays fully
interactive: the user can click a series, read the underlying cells and
re-sort the data.

Every chart is styled for the dark canvas: transparent chart area, dark
plot area, light axis text and the "Midnight Deck" accent palette.
"""

from __future__ import annotations

import pandas as pd
from openpyxl.chart import AreaChart, BarChart, DoughnutChart, Reference
from openpyxl.chart.data_source import AxDataSource, StrRef
from openpyxl.chart.legend import Legend
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText
from openpyxl.drawing.line import LineProperties
from openpyxl.drawing.text import (
    CharacterProperties,
    Paragraph,
    ParagraphProperties,
    RichTextProperties,
)
from openpyxl.worksheet.worksheet import Worksheet

from .excel_theme import (
    ACCENT,
    ACCENT_SOFT,
    CANVAS_BG,
    GRID,
    NEGATIVE,
    PANEL_BG,
    POSITIVE,
    TEXT_LIGHT,
    TEXT_MUTED,
    WARNING,
)

__all__ = [
    "style_chart",
    "build_area_trend",
    "build_bucket_donut",
    "build_volume_bars",
    "build_settlement_gauge",
]

# Bucket -> colour, matching the Streamlit donut.
BUCKET_COLORS = {
    "Net Realized": POSITIVE,
    "Cancellation Leakage": NEGATIVE,
    "Return Leakage": WARNING,
    "Loss Leakage": "64748B",
    "In-Transit": ACCENT,
    "Pending": ACCENT_SOFT,
}


def _axis_text(size: int = 800) -> RichText:
    """Build the rich-text style used for chart axis labels.

    Args:
        size: Font size in hundredths of a point.

    Returns:
        A :class:`RichText` instance.
    """
    return RichText(
        bodyPr=RichTextProperties(),
        p=[Paragraph(
            pPr=ParagraphProperties(defRPr=CharacterProperties(
                sz=size, solidFill=TEXT_MUTED, b=False)),
            endParaRPr=CharacterProperties(sz=size, solidFill=TEXT_MUTED),
        )],
    )


def style_chart(chart, title: str = "") -> None:
    """Apply the dark Command Center styling to an Excel chart.

    Args:
        chart: An openpyxl chart object.
        title: Optional chart title.
    """
    chart.graphical_properties = GraphicalProperties(solidFill=CANVAS_BG)
    chart.graphical_properties.line = LineProperties(noFill=True)
    if title:
        chart.title = title
        chart.title.tx.rich.p[0].pPr = ParagraphProperties(
            defRPr=CharacterProperties(sz=1000, b=True, solidFill=TEXT_LIGHT)
        )
    chart.style = 2
    chart.roundedCorners = False
    # The chart source block lives in hidden columns; without this Excel
    # would skip hidden data and render empty charts.
    chart.visible_cells_only = False

    plot = chart.plot_area
    plot.graphicalProperties = GraphicalProperties(solidFill=PANEL_BG)
    plot.graphicalProperties.line = LineProperties(noFill=True)

    # openpyxl defaults *both* axes to axPos="l". Excel renders nothing when
    # the category axis is not on the bottom, so pin them explicitly.
    for axis, position in (("x_axis", "b"), ("y_axis", "l")):
        ax = getattr(chart, axis, None)
        if ax is None:
            continue
        ax.axPos = position
        ax.txPr = _axis_text()
        ax.majorGridlines = None
        ax.delete = False
        ax.spPr = GraphicalProperties()
        ax.spPr.line = LineProperties(solidFill=GRID, w=6350)
    chart.legend = None


def _set_text_categories(chart, ref) -> None:
    """Point the category axis at text cells using a string reference.

    ``set_categories`` always writes a numeric reference, which makes Excel
    label a text category axis with 1, 2, 3 instead of the week names.

    Args:
        chart: An openpyxl chart whose series already exist.
        ref: An openpyxl :class:`Reference` covering the label cells.
    """
    for series in chart.series:
        series.cat = AxDataSource(strRef=StrRef(f=ref))


def build_area_trend(
    ws: Worksheet,
    weekly: pd.DataFrame,
    data_row: int,
    first_col: int,
    last_col: int,
    anchor: str,
) -> AreaChart:
    """Build the Gross-vs-Net filled area trend chart.

    Args:
        ws: Worksheet holding the source data block.
        weekly: Weekly KPI frame (used for the row count).
        data_row: First row of the data block.
        first_col: Column index of the week labels.
        last_col: Column index of the last plotted series.
        anchor: Cell the chart is anchored to.

    Returns:
        The styled :class:`AreaChart`.
    """
    cats = Reference(ws, min_col=first_col, min_row=data_row,
                     max_row=data_row + len(weekly) - 1)
    chart = AreaChart()
    # "standard" keeps both series anchored to the baseline so Gross and Net
    # overlap as two independent areas. "stacked" would add Net on top of
    # Gross, which misrepresents the reconciliation.
    chart.grouping = "standard"
    chart.overlap = 100
    # Excel draws the *last* series in front, so Net Realized is added last:
    # the smaller green area stays visible over the gross area.
    for col in (first_col + 1, first_col + 2):
        chart.add_data(
            Reference(ws, min_col=col, min_row=data_row - 1,
                      max_row=data_row + len(weekly) - 1),
            titles_from_data=True,
        )
    chart.set_categories(cats)
    _set_text_categories(chart, cats)

    colors = [ACCENT_SOFT, POSITIVE]
    for series, color in zip(chart.series, colors, strict=False):
        series.graphicalProperties = GraphicalProperties(solidFill=color)
        series.graphicalProperties.line = LineProperties(solidFill=color, w=12700)
        series.smooth = True

    style_chart(chart, "Revenue Trend — Gross Invoiced vs Net Realized")
    chart.height = 9.5
    chart.width = 19
    # Each trailing comma scales by 1,000, so two commas show millions.
    # Weekly values are in the lakhs, so "Cr" would mislabel them 10x.
    chart.y_axis.numFmt = '₹#,##0,,"M"'
    ws.add_chart(chart, anchor)
    return chart


def build_bucket_donut(
    ws: Worksheet,
    labels: list[str],
    data_row: int,
    label_col: int,
    value_col: int,
    anchor: str,
) -> DoughnutChart:
    """Build the revenue-by-financial-bucket donut chart.

    Args:
        ws: Worksheet holding the source data block.
        labels: Bucket labels (for the legend order).
        data_row: First row of the data block.
        label_col: Column index of the labels.
        value_col: Column index of the values.
        anchor: Cell the chart is anchored to.

    Returns:
        The styled :class:`DoughnutChart`.
    """
    chart = DoughnutChart(holeSize=62)
    chart.add_data(
        Reference(ws, min_col=value_col, min_row=data_row - 1,
                  max_row=data_row + len(labels) - 1),
        titles_from_data=True,
    )
    chart.set_categories(
        Reference(ws, min_col=label_col, min_row=data_row,
                  max_row=data_row + len(labels) - 1)
    )

    series = chart.series[0]
    points = []
    for label in labels:
        point = DataPoint(idx=len(points))
        point.graphicalProperties = GraphicalProperties(
            solidFill=BUCKET_COLORS.get(label, "64748B")
        )
        point.graphicalProperties.line = LineProperties(solidFill=CANVAS_BG, w=19050)
        points.append(point)
    series.data_points = points

    style_chart(chart, "Revenue by Financial Bucket")
    chart.height = 9.5
    chart.width = 12
    # Re-create the legend (style_chart removes it) and pin it to the right.
    chart.legend = Legend()
    chart.legend.position = "r"
    chart.legend.overlay = False
    ws.add_chart(chart, anchor)
    return chart


def build_volume_bars(
    ws: Worksheet,
    weekly: pd.DataFrame,
    data_row: int,
    week_col: int,
    value_col: int,
    anchor: str,
) -> BarChart:
    """Build the weekly transaction-volume bar chart.

    Args:
        ws: Worksheet holding the source data block.
        weekly: Weekly KPI frame (used for the row count).
        data_row: First row of the data block.
        week_col: Column index of the week labels.
        value_col: Column index of the volume values.
        anchor: Cell the chart is anchored to.

    Returns:
        The styled :class:`BarChart`.
    """
    chart = BarChart()
    chart.type = "col"
    chart.gapWidth = 60
    chart.add_data(
        Reference(ws, min_col=value_col, min_row=data_row - 1,
                  max_row=data_row + len(weekly) - 1),
        titles_from_data=True,
    )
    chart.set_categories(
        Reference(ws, min_col=week_col, min_row=data_row,
                  max_row=data_row + len(weekly) - 1)
    )
    _set_text_categories(
        chart,
        Reference(ws, min_col=week_col, min_row=data_row,
                  max_row=data_row + len(weekly) - 1),
    )
    series = chart.series[0]
    series.graphicalProperties = GraphicalProperties(solidFill=ACCENT)
    series.graphicalProperties.line = LineProperties(solidFill=ACCENT_SOFT, w=6350)

    style_chart(chart, "Transaction Volume / Week")
    chart.height = 8.5
    chart.width = 14
    chart.y_axis.numFmt = '#,##0'
    ws.add_chart(chart, anchor)
    return chart


def build_settlement_gauge(
    ws: Worksheet,
    data_row: int,
    label_col: int,
    value_col: int,
    anchor: str,
) -> DoughnutChart:
    """Build the settlement-health gauge ring.

    A two-slice donut (retained vs the rest) drawn as a ring, with the
    percentage in the hole — the Excel twin of the Streamlit gauge.

    Args:
        ws: Worksheet holding the source data block.
        data_row: First row of the gauge data block.
        label_col: Column index of the slice labels.
        value_col: Column index of the slice values.
        anchor: Cell the chart is anchored to.

    Returns:
        The styled :class:`DoughnutChart`.
    """
    chart = DoughnutChart(holeSize=70)
    chart.firstSliceAng = 270
    # The two gauge slices live side by side in one row, so the reference
    # spans two columns of a single row (not a vertical range).
    chart.add_data(
        Reference(ws, min_col=value_col, max_col=value_col + 1,
                  min_row=data_row, max_row=data_row),
        titles_from_data=False, from_rows=True,
    )
    series = chart.series[0]
    points = []
    for idx, color in enumerate((ACCENT, "182338")):
        point = DataPoint(idx=idx)
        point.graphicalProperties = GraphicalProperties(solidFill=color)
        point.graphicalProperties.line = LineProperties(noFill=True)
        points.append(point)
    series.data_points = points

    style_chart(chart, "Settlement Health")
    chart.height = 8.5
    chart.width = 10
    chart.legend = None
    ws.add_chart(chart, anchor)
    return chart
