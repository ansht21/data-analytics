"""Shared openpyxl styling: fills, fonts, borders, currency formats."""

from __future__ import annotations

from copy import copy

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

INR_FORMAT = '₹#,##0.00'
PCT_FORMAT = '0.00"%"'
INT_FORMAT = '#,##0'

THIN = Side(style="thin", color="D9D9D9")
THIN_BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

KPI_ACCENTS = {
    "blue": "0B2A4A",     # Executive Navy
    "green": "0EA5E9",    # Sky (single-accent positive)
    "red": "64748B",      # Muted slate (negative flag)
    "yellow": "94A3B8",   # Muted slate (warning flag)
    "gray": "475569",     # Slate
    "purple": "38BDF8",   # Sky (single-accent highlight)
}

CARD_BG_FILL = PatternFill("solid", fgColor="FFFFFF")
CARD_HEADER_FILL = PatternFill("solid", fgColor="F8FAFC")
CARD_BORDER_COLOR = "CBD5E1"

HEADER_FILL = PatternFill("solid", fgColor="0B2A4A")
HEADER_FONT = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Segoe UI", size=16, bold=True, color="0B2A4A")
SUBTITLE_FONT = Font(name="Segoe UI", size=9, italic=True, color="64748B")
CARD_LABEL_FONT = Font(name="Segoe UI", size=8.5, bold=True, color="475569")
CARD_VALUE_FONT = Font(name="Segoe UI", size=15, bold=True, color="0F172A")
CARD_SUB_FONT = Font(name="Segoe UI", size=7.5, italic=True, color="64748B")
TABLE_FONT = Font(name="Segoe UI", size=9.5)

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def style_header_row(ws, row: int, ncols: int) -> None:
    """Apply dark header styling to ``row`` across ``ncols`` columns."""
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER
        cell.border = THIN_BORDER


def style_range_border(ws, min_row: int, max_row: int, min_col: int, max_col: int) -> None:
    """Draw a thin border around a rectangular range."""
    for r in range(min_row, max_row + 1):
        for c in range(min_col, max_col + 1):
            ws.cell(row=r, column=c).border = copy(THIN_BORDER)
