"""Dark "Midnight Deck" theme tokens for the openpyxl dashboard.

Mirrors :mod:`streamlit_app.theme` so the Excel workbook and the Streamlit
cockpit read as the same product: deep-navy canvas, sky-cyan and emerald
accents, muted slate labels.

Excel has no page background, so the canvas is painted by filling the used
cell range with :data:`CANVAS_BG` and drawing "panels" as merged, filled
cell blocks.
"""

from __future__ import annotations

from openpyxl.styles import Alignment, Border, Font, GradientFill, PatternFill, Side

# --- Canvas / surface / border -------------------------------------------
CANVAS_BG = "0B1220"
PANEL_BG = "101A2C"
PANEL_HI = "16223A"
BORDER = "1E2C45"
GRID = "26385A"

# --- Text ----------------------------------------------------------------
TEXT_LIGHT = "EAF0FA"
TEXT_MUTED = "8FA3BF"
TEXT_DIM = "5B6E8C"

# --- Accents -------------------------------------------------------------
ACCENT = "22D3EE"
ACCENT_SOFT = "7DD3FC"
ACCENT_DEEP = "0E7490"
POSITIVE = "34D399"
POSITIVE_DEEP = "065F46"
WARNING = "F59E0B"
NEGATIVE = "FB7185"

# Hero gradient card fills (left -> right).
GRAD_HERO_A = ("0E7490", "22D3EE")
GRAD_HERO_B = ("065F46", "34D399")

# --- Fonts ---------------------------------------------------------------
TITLE_FONT = Font(name="Segoe UI", size=20, bold=True, color=TEXT_LIGHT)
SUBTITLE_FONT = Font(name="Segoe UI", size=10, color=TEXT_MUTED)
HERO_LABEL_FONT = Font(name="Segoe UI", size=9, bold=True, color="D8E6F5")
HERO_VALUE_FONT = Font(name="Segoe UI", size=26, bold=True, color="FFFFFF")
HERO_SUB_FONT = Font(name="Segoe UI", size=9.5, bold=True, color="EAF7FF")
HERO_FOOT_FONT = Font(name="Segoe UI", size=8, color="C9DCEF")
PILL_LABEL_FONT = Font(name="Segoe UI", size=8, bold=True, color=TEXT_MUTED)
PILL_VALUE_FONT = Font(name="Segoe UI", size=12, bold=True, color=TEXT_LIGHT)
SECTION_FONT = Font(name="Segoe UI", size=11, bold=True, color=ACCENT)
BANNER_TITLE_FONT = Font(name="Segoe UI", size=12, bold=True, color=ACCENT)
BANNER_SUB_FONT = Font(name="Segoe UI", size=9, color=TEXT_MUTED)
TABLE_HEADER_FONT = Font(name="Segoe UI", size=9, bold=True, color=TEXT_LIGHT)
TABLE_FONT = Font(name="Segoe UI", size=9, color=TEXT_LIGHT)

# --- Fills ---------------------------------------------------------------
CANVAS_FILL = PatternFill("solid", fgColor=CANVAS_BG)
PANEL_FILL = PatternFill("solid", fgColor=PANEL_BG)
BANNER_FILL = PatternFill("solid", fgColor="0B1B24")
PILL_FILL = PatternFill("solid", fgColor=PANEL_HI)

THIN = Side(style="thin", color=BORDER)
MEDIUM = Side(style="medium", color=ACCENT)
HAIRLINE = Side(style="hair", color=BORDER)
THIN_BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)

# --- Number formats ------------------------------------------------------
INR_FORMAT = '₹#,##0.00'
INR_CR_FORMAT = '₹#,##0.00,," Cr"'
PCT_FORMAT = '0.00"%"'
INT_FORMAT = '#,##0'


def hero_gradient(stops: tuple[str, str]) -> GradientFill:
    """Build a horizontal two-stop gradient fill for a hero card.

    Args:
        stops: Tuple of (start hex, end hex) colours.

    Returns:
        A configured :class:`GradientFill`.
    """
    return GradientFill(type="linear", degree=0, stop=list(stops))


def panel_border() -> Border:
    """Return the thin border used around dark panels.

    Returns:
        A :class:`Border` instance.
    """
    return Border(left=HAIRLINE, right=HAIRLINE, top=HAIRLINE, bottom=HAIRLINE)


def section_fill() -> PatternFill:
    """Return the fill used for section header rows.

    Returns:
        A :class:`PatternFill` instance.
    """
    return PatternFill("solid", fgColor=PANEL_HI)
