"""Dark "Executive Slate" theme tokens for the openpyxl dashboard.

Mirrors :mod:`streamlit_app.theme` so the Excel workbook and the Streamlit
cockpit read as the same product: slate-900 canvas, elevated charcoal panels,
a single sapphire/sky-blue accent, muted slate labels and status flags.

Excel has no page background, so the canvas is painted by filling the used
cell range with :data:`CANVAS_BG` and drawing "panels" as merged, filled
cell blocks.
"""

from __future__ import annotations

from openpyxl.styles import Alignment, Border, Font, GradientFill, PatternFill, Side

# --- Canvas / surface / border -------------------------------------------
CANVAS_BG = "0F172A"
PANEL_BG = "1E293B"
PANEL_HI = "27364A"
BORDER = "334155"
GRID = "24344B"

# --- Text ----------------------------------------------------------------
TEXT_LIGHT = "E2E8F0"
TEXT_MUTED = "94A3B8"
TEXT_DIM = "64748B"

# --- Accents -------------------------------------------------------------
ACCENT = "38BDF8"
ACCENT_SOFT = "7DD3FC"
ACCENT_DEEP = "0284C7"
POSITIVE = "0EA5E9"
POSITIVE_DEEP = "075985"
WARNING = "94A3B8"
NEGATIVE = "64748B"

# Hero gradient card fills (left -> right).
GRAD_HERO_A = ("0369A1", "38BDF8")
GRAD_HERO_B = ("0C4A6E", "7DD3FC")

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
BANNER_FILL = PatternFill("solid", fgColor="0F2743")
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
