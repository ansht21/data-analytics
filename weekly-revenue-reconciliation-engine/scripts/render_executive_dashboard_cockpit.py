"""Render the Executive E-Commerce Revenue Reconciliation Cockpit.

Output: docs/images/Revenue_Reconciliation_Dashboard_Cockpit.png
        exactly 2560x1440 (16:9) and **opaque** - a clean rectangle with
        no transparent background and no tight-bbox cropping.
        (The previous build came out 3880x2204 RGBA with alpha, which made
        it render as a non-rectangular blob on light backgrounds.)

Aesthetic: "Executive Slate / Metric Flow" - deep slate-900 canvas, slightly
lighter rounded cards with generous padding, a delta pill in the top-right of
every KPI card, and a single sky-blue accent. Only the accent hue differs
from the reference board; geometry, spacing and hierarchy follow it.

The colour tokens are imported from :mod:`streamlit_app.theme` so this
static render, the Streamlit app and the Excel workbook are guaranteed to
share one palette (slate-900 canvas, charcoal cards, sky-blue accent,
tonal-blue series, muted slate flags).

Every number is computed from the cleaned parquet via
``src.reconciliation.metrics`` -- the same single source of truth the
Streamlit dashboard and the Excel workbook use.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.reconciliation.engine import aggregate_weekly  # noqa: E402
from src.reconciliation.metrics import (  # noqa: E402
    category_revenue,
    compute_headline_kpis,
    fulfilment_settlement,
    leakage_by_dimension,
)
from src.reconciliation.variance_analyzer import add_wow_variance  # noqa: E402
from streamlit_app.theme import (  # noqa: E402
    ACCENT,
    ACCENT_SOFT,
    BORDER,
    CANVAS_BG,
    CARD_BG,
    CARD_HI,
    GRID,
    NEGATIVE,
    NEUTRAL,
    PANEL_BG,
    POSITIVE,
    TEXT_LIGHT,
    TEXT_MUTED,
    WARNING,
)

PARQUET_PATH = ROOT / "data" / "processed" / "cleaned_transactions.parquet"
OUT_PATH = ROOT / "docs" / "images" / "Revenue_Reconciliation_Dashboard_Cockpit.png"

# ---- Dark theme (shared with the Streamlit app and the Excel workbook) ----
GRID_COLOR = GRID
CHIP_BG = CARD_HI
CHIP_EDGE = BORDER

# ---- Semantic KPI palette: ONE accent colour everywhere ----
KPI_SLATE = ACCENT
KPI_TEAL = ACCENT
KPI_CORAL = ACCENT
KPI_AMBER = ACCENT
KPI_INDIGO = ACCENT

# Gross -> Net composition stack: strict tonal-blue ladder (single hue family).
C_NET = "#38BDF8"
C_CANCEL = "#0369A1"
C_RETURN = "#0EA5E9"
C_LOSS = "#64748B"
C_TRANSIT = "#475569"

FIG_W_IN, FIG_H_IN, DPI = 12.8, 7.2, 200   # -> exactly 2560 x 1440

# Panel metrics (axes-fraction units).
CHIP_H = 0.021
CHIP_PAD_X = 0.004
CHIP_PAD_Y = 0.003
CHIP_GAP_X = 0.003
CHIP_GAP_Y = 0.002
SECTION_HEADER_H = 0.018
SECTION_TAIL = 0.003
RANK_HEAD_H = 0.016
RANK_ROW_H = 0.026
STATUS_H = 0.038

# Single-hue series ladder: everything the charts draw lives in the same
# blue family (dark navy -> pale sky); muted slate is the only neutral.
BLUE_LADDER = ["#0C4A6E", "#0369A1", "#0284C7", "#0EA5E9", "#38BDF8", "#7DD3FC", "#BAE6FD"]


def _rect(ax, x, y, w, h, face, edge=None, lw=0.8, z=1, r=0.0):
    """Draw a card/panel in axes-fraction units.

    With ``r`` > 0 the card gets rounded corners (FancyBboxPatch) like the
    Metric-Flow reference; tiny decorations (bars, legend swatches) keep
    square corners by leaving ``r`` at 0.
    """
    if r > 0:
        p = FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0,rounding_size={r}",
            mutation_scale=1, linewidth=lw, edgecolor=edge or face,
            facecolor=face, transform=ax.transAxes, zorder=z)
    else:
        p = Rectangle((x, y), w, h, linewidth=lw, edgecolor=edge or face,
                      facecolor=face, transform=ax.transAxes, zorder=z)
    ax.add_patch(p)
    return p


def _kpi(ax, x, y, w, h, label, value, subtext, delta, delta_up, accent):
    """Metric-Flow KPI card: delta pill top-right, white value, airy layout.

    All offsets scale with the card height so the geometry can be re-derived
    without touching each text position independently.
    """
    _rect(ax, x, y - h, w, h, CARD_BG, edge=BORDER, lw=0.9, z=1, r=0.007)

    # Row 1: delta pill, pinned to the top-right corner (reference style).
    pw, ph = 0.062, 0.020
    pill_x = x + w - pw - 0.011
    pill_y = y - 0.028
    _rect(ax, pill_x, pill_y, pw, ph,
          "#0B2E4A" if delta_up else CHIP_BG,
          edge=ACCENT if delta_up else CHIP_EDGE, lw=0.7, z=3, r=ph / 2)
    c_pill = ACCENT if delta_up else TEXT_MUTED
    arrow = "\u25b2" if delta_up else "\u25bc"
    # "WoW" is spelled out: without it a -43% chip on Net Realized reads as
    # "the business collapsed" rather than "one flagged week vs the prior one".
    ax.text(pill_x + pw / 2, pill_y + ph / 2, f"{arrow} {delta} WoW",
            color=c_pill, fontsize=5.9, weight="bold",
            transform=ax.transAxes, ha="center", va="center", zorder=4)

    # Row 2: full-width label line (long titles get the whole card width).
    ax.text(x + 0.012, y - 0.052, label.upper(), color=TEXT_MUTED, fontsize=6.8,
            weight="bold", transform=ax.transAxes, va="center", ha="left", zorder=3)

    # Row 3: big white value (reference: values are white, the accent lives in the pill).
    ax.text(x + 0.012, y - h * 0.643, value, color=TEXT_LIGHT, fontsize=15.5,
            weight="bold", transform=ax.transAxes, va="center", ha="left", zorder=3)

    # Row 4: muted sub-line above the card's bottom edge.
    ax.text(x + 0.012, y - h + 0.015, subtext, color=TEXT_MUTED, fontsize=6.6,
            transform=ax.transAxes, va="center", ha="left", zorder=3)


def _fit_font(text, chip_w, base, fig_w_in=FIG_W_IN, dpi_pts=72.0):
    usable_pt = chip_w * fig_w_in * dpi_pts * 0.86
    est_pt = len(str(text)) * base * 0.62
    return base if est_pt <= usable_pt else max(5.0, base * usable_pt / est_pt)


def _chip(ax, x, y, w, h, text, base=7.8):
    _rect(ax, x, y, w, h, CHIP_BG, edge=CHIP_EDGE, lw=0.7, r=0.006)
    ax.text(x + w / 2, y + h / 2, text, color=TEXT_LIGHT,
            fontsize=_fit_font(text, w, base), weight="bold",
            transform=ax.transAxes, ha="center", va="center", zorder=3)


def _section_box_h(rows):
    body_h = CHIP_PAD_Y * 2 + rows * CHIP_H + (rows - 1) * CHIP_GAP_Y
    return SECTION_HEADER_H + body_h + SECTION_TAIL


def _filter_section(ax, x_top, y_top, w, items, label, cols):
    rows = math.ceil(len(items) / cols)
    box_h = _section_box_h(rows)
    box_y = y_top - box_h
    _rect(ax, x_top, box_y, w, box_h, CARD_BG, edge=BORDER, lw=0.8, r=0.006)
    ax.text(x_top + 0.008, y_top - SECTION_HEADER_H / 2, label.upper(), color=ACCENT,
            fontsize=7.8, weight="bold", transform=ax.transAxes, ha="left", va="center")
    chip_w = (w - (cols + 1) * CHIP_PAD_X) / cols
    for i, item in enumerate(items):
        row, col = divmod(i, cols)
        cx = x_top + CHIP_PAD_X + col * (chip_w + CHIP_PAD_X)
        cy = y_top - SECTION_HEADER_H - CHIP_PAD_Y - CHIP_H - row * (CHIP_H + CHIP_GAP_Y)
        _chip(ax, cx, cy, chip_w, CHIP_H, str(item))
    return box_h


def _rank_card(ax, x, y_top, w, title, items, accent=ACCENT):
    n = len(items)
    box_h = RANK_HEAD_H + 0.006 + n * RANK_ROW_H + 0.006
    _rect(ax, x, y_top - box_h, w, box_h, CARD_BG, edge=BORDER, lw=0.8, r=0.006)
    ax.text(x + 0.008, y_top - RANK_HEAD_H / 2, title.upper(), color=accent,
            fontsize=7.8, weight="bold", transform=ax.transAxes, ha="left", va="center")
    for i, (label, value, frac) in enumerate(items):
        yc = y_top - RANK_HEAD_H - 0.006 - RANK_ROW_H * (i + 0.5)
        ax.text(x + 0.008, yc + 0.009, label, color=TEXT_MUTED, fontsize=6.6,
                weight="bold", transform=ax.transAxes, ha="left", va="center")
        ax.text(x + w - 0.008, yc + 0.009, value, color=TEXT_LIGHT, fontsize=6.8,
                weight="bold", transform=ax.transAxes, ha="right", va="center")
        _rect(ax, x + 0.008, yc - 0.0075, (w - 0.016) * max(frac, 0.03), 0.0026, accent, z=3)
    return box_h


def _status_footer(ax, x, y_bottom, w, title, sub):
    _rect(ax, x, y_bottom, w, STATUS_H, CARD_HI, edge=ACCENT, lw=0.8, r=0.006)
    ax.text(x + w / 2, y_bottom + STATUS_H * 0.64, title, color=ACCENT, fontsize=7.2,
            weight="bold", transform=ax.transAxes, ha="center", va="center")
    ax.text(x + w / 2, y_bottom + STATUS_H * 0.26, sub, color=TEXT_MUTED, fontsize=6.4,
            transform=ax.transAxes, ha="center", va="center")

def main():
    print("Loading data from parquet...")
    df = pd.read_parquet(PARQUET_PATH)

    # Weekly KPIs come from the reconciliation engine (single source of truth).
    weekly = add_wow_variance(aggregate_weekly(df)).rename(
        columns={"gross_revenue": "gross", "net_realized": "net",
                 "total_leakage": "leakage", "total_orders": "orders"}
    )
    weekly["clearance"] = weekly["settled_clearance_rate"]
    kpi = compute_headline_kpis(df, weekly)

    # Deltas are week-over-week on the last two FULL weeks. The previous
    # build compared the first week against the last, which read as a
    # "collapse" that was really just the dataset ramping up.
    full = weekly[~weekly["is_partial_week"]]
    if len(full) < 2:
        full = weekly
    last, prev = full.iloc[-1], full.iloc[-2]
    d_gross = (last["gross"] / prev["gross"] - 1) * 100
    d_net = (last["net"] / prev["net"] - 1) * 100
    d_leak = (last["leakage"] / max(prev["leakage"], 1) - 1) * 100
    d_clr = last["clearance"] - prev["clearance"]
    d_aov = ((last["gross"] / last["orders"]) / (prev["gross"] / prev["orders"]) - 1) * 100

    fig = plt.figure(figsize=(FIG_W_IN, FIG_H_IN), dpi=DPI, facecolor=CANVAS_BG)
    ax_bg = fig.add_axes([0, 0, 1, 1])
    ax_bg.set_facecolor(CANVAS_BG)
    ax_bg.axis("off")

    # ------------------------------------------------------------------
    # 1. App top bar: brand | search | period | avatar
    # ------------------------------------------------------------------
    tb_y, tb_h = 0.958, 0.062
    _rect(ax_bg, 0.010, tb_y - tb_h, 0.980, tb_h, PANEL_BG, edge=BORDER, lw=0.8, r=0.008)

    _rect(ax_bg, 0.020, tb_y - 0.048, 0.013, 0.024, ACCENT, r=0.004)
    ax_bg.text(0.038, tb_y - 0.036, "Revenue Reconciliation", color=TEXT_LIGHT,
               fontsize=10.0, weight="bold", va="center", transform=ax_bg.transAxes)

    # search box - starts after the brand so the two never overlap
    sr_x, sr_w = 0.215, 0.300
    _rect(ax_bg, sr_x, tb_y - 0.048, sr_w, 0.024, CARD_BG, edge=BORDER, lw=0.8, r=0.011)
    ax_bg.text(sr_x + 0.010, tb_y - 0.036, "Search metrics, weeks, states\u2026",
               color=TEXT_MUTED, fontsize=7.6, va="center", transform=ax_bg.transAxes)


    # ------------------------------------------------------------------
    # 2. Navigation sidebar
    # ------------------------------------------------------------------
    sb_x, sb_w = 0.012, 0.142
    sb_top, sb_bottom = 0.880, 0.030
    _rect(ax_bg, sb_x, sb_bottom, sb_w, sb_top - sb_bottom, PANEL_BG, edge=BORDER, lw=0.8, r=0.008)
    ax_bg.text(sb_x + sb_w / 2, sb_top - 0.016, "AUDIT CONTROLS", color=ACCENT,
               fontsize=9.0, weight="bold", ha="center", va="center", transform=ax_bg.transAxes)

    cy = sb_top - 0.030
    cy -= _filter_section(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                           ["W13\u2013W17 (Apr)", "W18\u2013W22 (May)", "W23\u2013W26 (Jun)"],
                           "Fiscal Period", cols=1)
    cy -= 0.005

    fulfil_rows = fulfilment_settlement(df)
    fulfil_lines = [
        f"{r['Fulfilment']} ({r['gross_revenue'] / kpi.gross_revenue * 100:.1f}%)"
        for _, r in fulfil_rows.iterrows()
    ]
    cy -= _filter_section(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                           fulfil_lines, "Fulfilment Mode", cols=1)
    cy -= 0.005

    bucket_counts = df["financial_bucket"].value_counts()
    pipeline_lines = [
        f"In-Transit: {bucket_counts.get('In-Transit', 0) / 1000:.1f}k",
        f"Net Realized: {bucket_counts.get('Net Realized', 0) / 1000:.1f}k",
        f"Cancelled: {bucket_counts.get('Cancellation Leakage', 0) / 1000:.1f}k",
        f"Returned: {bucket_counts.get('Return Leakage', 0) / 1000:.1f}k",
    ]
    cy -= _filter_section(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                           pipeline_lines, "Logistics Pipeline", cols=2)
    cy -= 0.005

    channel_counts = df["Sales Channel"].value_counts() if "Sales Channel" in df.columns else df["Status"].value_counts()
    top_channels = channel_counts.head(3)
    channel_lines = [f"{name} ({val / len(df) * 100:.1f}%)" for name, val in top_channels.items()]
    if "B2B" in df.columns:
        b2b_share = float(df["B2B"].astype(bool).sum()) / len(df) * 100
        channel_lines.append(f"B2B Wholesale ({b2b_share:.1f}%)")
    cy -= _filter_section(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                           channel_lines, "Channel & Tier", cols=1)
    cy -= 0.005

    # Sidebar rank cards: computed from the data, never hardcoded.
    cat_df = category_revenue(df, top_n=5)
    cat_top = float(cat_df["revenue"].iloc[0]) if len(cat_df) else 1.0
    cats_data = [
        (str(r["Category"]), f"\u20b9{r['revenue'] / 1e6:,.1f}M",
         float(r["revenue"]) / cat_top if cat_top else 0.0)
        for _, r in cat_df.iterrows()
    ]
    if cats_data:
        cy -= _rank_card(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                         "Revenue by Category", cats_data)
        cy -= 0.005

    # Audit rules - the thresholds the engine actually applies.
    th = None
    try:
        from src.config import load_settings
        th = load_settings().thresholds
    except Exception:
        th = None
    if th is not None:
        rule_lines = [
            f"Clearance < {th.settled_clearance_critical_below:.0f}% \u2192 CRITICAL",
            f"Leakage > {th.leakage_warning_above:.0f}% \u2192 WARNING",
            f"Cancel > {th.cancellation_warning_above:.0f}% \u2192 WARNING",
            f"WoW drop > {abs(th.wow_drop_alert_below):.0f}% \u2192 ALERT",
        ]
        cy -= _filter_section(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                               rule_lines, "Audit Rules", cols=1)
        cy -= 0.008

    # Audit legend - explains the composition colours used in the charts.
    legend_items = [
        (C_NET, "Net Realized"),
        (C_CANCEL, "Cancellation"),
        (C_RETURN, "Return"),
        (C_LOSS, "Loss"),
        (C_TRANSIT, "In-Transit"),
    ]
    leg_h = SECTION_HEADER_H + 0.004 + len(legend_items) * 0.0155 + 0.004
    _rect(ax_bg, sb_x + 0.004, cy - leg_h, sb_w - 0.008, leg_h, CARD_BG, edge=BORDER, lw=0.8, r=0.006)
    ax_bg.text(sb_x + 0.012, cy - SECTION_HEADER_H / 2, "GROSS \u2192 NET LEGEND",
               color=ACCENT, fontsize=7.4, weight="bold",
               transform=ax_bg.transAxes, ha="left", va="center")
    for i, (col, label) in enumerate(legend_items):
        ly = cy - SECTION_HEADER_H - 0.004 - 0.0155 * (i + 0.5)
        _rect(ax_bg, sb_x + 0.014, ly - 0.0045, 0.012, 0.009, col, z=3)
        ax_bg.text(sb_x + 0.030, ly, label, color=TEXT_MUTED, fontsize=6.6,
                   weight="bold", transform=ax_bg.transAxes, ha="left", va="center")
    cy -= leg_h + 0.004

    # Status footer pinned to the bottom of the sidebar.
    _status_footer(ax_bg, sb_x + 0.006, sb_bottom + 0.006, sb_w - 0.012,
                   "AUDIT STATUS: RECONCILED",
                   f"{kpi.total_lines:,} lines \u00b7 {kpi.weeks_active} weeks active")

    _rect(ax_bg, 0.700, tb_y - 0.048, 0.150, 0.024, CARD_BG, edge=BORDER, lw=0.8, r=0.011)
    ax_bg.text(0.775, tb_y - 0.036, "FY22 \u00b7 W13\u2013W26 (Apr\u2013Jun)",
               color=TEXT_MUTED, fontsize=7.6, va="center", ha="center",
               transform=ax_bg.transAxes)

    ax_bg.add_patch(Circle((0.930, tb_y - 0.036), 0.0088, facecolor=ACCENT,
                           transform=ax_bg.transAxes, clip_on=False))
    ax_bg.text(0.930, tb_y - 0.036, "AT", color="#FFFFFF", fontsize=7.6, weight="bold",
               ha="center", va="center", transform=ax_bg.transAxes)

    # ------------------------------------------------------------------
    # 3. KPI row - Metric-Flow cards: pill top-right, white value
    # ------------------------------------------------------------------
    main_x = 0.162
    main_w = 0.828
    kpi_top = 0.880
    kpi_h = 0.115
    gap = 0.010
    kpi_w = (main_w - gap * 4) / 5

    clearance_ok = kpi.settled_clearance_rate >= 70.0
    cards = [
        ("Gross Invoiced Revenue", f"\u20b9{kpi.gross_revenue / 1e7:,.2f} Cr",
         f"{kpi.total_lines:,} lines", f"{abs(d_gross):.1f}%", d_gross >= 0, KPI_SLATE),
        ("Net Realized Cash", f"\u20b9{kpi.net_realized / 1e7:,.2f} Cr",
         f"{kpi.settled_clearance_rate:.1f}% settled", f"{abs(d_net):.1f}%", d_net >= 0, KPI_TEAL),
        ("Total Revenue Leakage", f"\u20b9{kpi.total_leakage / 1e7:,.2f} Cr",
         f"\u20b9{kpi.cancellation_leakage / 1e5:,.1f}L cancelled", f"{abs(d_leak):.1f}%", d_leak <= 0, KPI_CORAL),
        ("Settled Clearance Rate", f"{kpi.settled_clearance_rate:.1f}%",
         "target 70%", f"{abs(d_clr):.1f}pp", d_clr >= 0, KPI_TEAL if clearance_ok else KPI_AMBER),
        ("Avg Order Value (AOV)", f"\u20b9{kpi.avg_order_value:,.0f}",
         f"peak \u20b9{weekly['avg_order_value'].max():,.0f}", f"{abs(d_aov):.1f}%", d_aov >= 0, KPI_INDIGO),
    ]
    for i, (label, value, sub, delta, up, accent) in enumerate(cards):
        _kpi(ax_bg, main_x + i * (kpi_w + gap), kpi_top, kpi_w, kpi_h,
             label, value, sub, delta, up, accent)

    # ------------------------------------------------------------------
    # 4. Chart grid - 3 rows x 2 columns: wide, roomy cards (16:9 canvas)
    # ------------------------------------------------------------------
    grid_top = 0.748
    row_h = 0.222
    row_gap = 0.014
    col_gap = 0.012
    col_w = (main_w - col_gap) / 2
    c1_x = main_x                      # left column
    c2_x = main_x + col_w + col_gap    # right column
    row1_y = grid_top - row_h
    row2_y = row1_y - row_gap - row_h
    row3_y = row2_y - row_gap - row_h

    def _create_card(x, y, w, h, title, pad_left=0.014, pad_bottom=0.034, pad_right=0.012,
                     pad_top=0.034):
        _rect(ax_bg, x, y, w, h, CARD_BG, edge=BORDER, lw=0.9, r=0.008)
        ax_bg.text(x + 0.014, y + h - 0.026, title.upper(), color=TEXT_LIGHT, fontsize=8.4,
                   weight="bold", transform=ax_bg.transAxes, va="center")
        ax = fig.add_axes([x + pad_left, y + pad_bottom,
                           w - pad_left - pad_right, h - pad_bottom - pad_top])
        ax.set_facecolor(CARD_BG)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(GRID_COLOR)
        ax.spines["bottom"].set_color(GRID_COLOR)
        ax.tick_params(colors=TEXT_MUTED, labelsize=7.4)
        ax.grid(axis="y", linestyle="--", alpha=0.30, color=GRID_COLOR)
        return ax

    x_idx = np.arange(len(weekly))
    partial = weekly["is_partial_week"].to_numpy()
    gross_m = weekly["gross"] / 1e6
    net_m = weekly["net"] / 1e6


    # -- Chart 1: Weekly invoiced vs realized -----------------------------
    ax1 = _create_card(c1_x, row1_y, col_w, row_h,
                       "Weekly Invoiced vs Realized Revenue (\u20b9M)")
    # Partial weeks are drawn hollow and excluded from the area fill, so a
    # truncated window edge can never be read as a real collapse.
    ax1.plot(x_idx[~partial], gross_m[~partial], color=ACCENT, linewidth=2.4,
             marker="o", markersize=4.2, label="Gross Invoiced")
    ax1.plot(x_idx[~partial], net_m[~partial], color=NEUTRAL, linewidth=2.0,
             linestyle="--", marker="s", markersize=3.6, label="Net Realized")
    if partial.any():
        ax1.plot(x_idx[partial], gross_m[partial], color=ACCENT, linewidth=1.6,
                 marker="o", markersize=5.0, markerfacecolor="none", linestyle="none")
        ax1.plot(x_idx[partial], net_m[partial], color=NEUTRAL, linewidth=1.6,
                 marker="s", markersize=4.4, markerfacecolor="none", linestyle="none")
        ax1.plot([], [], color=NEUTRAL, marker="o", markerfacecolor="none",
                 linestyle="none", label="Partial week (excluded)")
    ax1.fill_between(x_idx[~partial], net_m[~partial], 0, color=C_NET, alpha=0.13)
    peak = int(np.argmax(gross_m.values))
    ax1.annotate(f"Peak \u20b9{gross_m.iloc[peak]:,.1f}M",
                 (x_idx[peak], gross_m.iloc[peak]), textcoords="offset points",
                 xytext=(0, -18), ha="center", color=ACCENT, fontsize=7.2, weight="bold")
    ax1.set_xticks(x_idx)
    ax1.set_xticklabels(weekly["week_label"], rotation=45, ha="right", fontsize=7.2)
    ax1.set_ylabel("\u20b9 Millions", color=TEXT_MUTED, fontsize=7.2)
    ax1.set_ylim(0, gross_m.max() * 1.22)
    leg1 = ax1.legend(loc="upper right", frameon=False, fontsize=6.8, ncol=3,
                      columnspacing=0.9, handlelength=1.2)
    for t in leg1.get_texts():
        t.set_color(TEXT_LIGHT)

    # -- Chart 2: Leakage breakdown (donut) ------------------------------
    ax2 = _create_card(c2_x, row1_y, col_w, row_h,
                       "Revenue Leakage Breakdown (Root Causes)")
    leak_parts = [
        ("Order Cancellations", kpi.cancellation_leakage, C_CANCEL),
        ("Customer Returns", kpi.return_leakage, C_RETURN),
        ("Transit Losses", kpi.loss_leakage, C_LOSS),
    ]
    leak_total = sum(p[1] for p in leak_parts) or 1.0
    wedges, _texts, autotexts = ax2.pie(
        [p[1] for p in leak_parts],
        colors=[p[2] for p in leak_parts],
        startangle=90,
        counterclock=False,
        autopct=lambda pct: f"{pct:.1f}%" if pct > 3 else "",
        pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor=CARD_BG, linewidth=2),
        textprops=dict(color=TEXT_LIGHT, fontsize=7.6, weight="bold"),
    )
    # Anchor the (square) donut to the left half of the wide card, so the
    # right half can breathe instead of squeezing the legend.
    ax2.set_anchor("W")
    ax2.text(0, 0.06, "TOTAL LEAK", ha="center", va="center", color=TEXT_MUTED,
             fontsize=7.6, weight="bold")
    ax2.text(0, -0.14, f"\u20b9{kpi.total_leakage / 1e6:,.2f}M", ha="center", va="center",
             color=ACCENT, fontsize=11.5, weight="bold")
    legend_labels = [
        f"{name}  \u20b9{val / 1e6:,.2f}M ({val / leak_total * 100:.1f}%)"
        for name, val, _ in leak_parts
    ]
    ax2.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1.04, 0.5),
               frameon=False, fontsize=7.0, ncol=1, handlelength=1.1, labelspacing=0.55)
    for t in ax2.get_legend().get_texts():
        t.set_color(TEXT_LIGHT)

    # -- Chart 3: Weekly gross -> net composition (stacked) --------------
    # This replaces the old "Settlement Split by Fulfilment Flag" chart.
    # The Fulfilment column is a *dispatch state*, not a business channel, so
    # that chart could never be meaningful (Amazon net is always 0). This
    # stacked view is the actual Gross -> Net bridge the audit is about.
    ax3 = _create_card(c1_x, row3_y, col_w, row_h,
                       "Weekly Gross \u2192 Net Composition (\u20b9M)",
                       pad_left=0.018, pad_top=0.078)
    # Stacked from the bottom up: In-Transit (settlement lag) sits at the
    # base, Net Realized caps the stack, so the eye lands on what was
    # actually realised.
    stack = [
        ("In-Transit", weekly["in_transit_value"] / 1e6, C_TRANSIT),
        ("Loss", weekly["loss_leakage"] / 1e6, C_LOSS),
        ("Return", weekly["return_leakage"] / 1e6, C_RETURN),
        ("Cancellation", weekly["cancellation_leakage"] / 1e6, C_CANCEL),
        ("Net Realized", weekly["net"] / 1e6, C_NET),
    ]
    bottom = np.zeros(len(weekly))
    for label, series, col in stack:
        ax3.bar(x_idx, series, bottom=bottom, color=col, label=label, width=0.72)
        bottom += series.to_numpy()
    ax3.set_xticks(x_idx)
    ax3.set_xticklabels(weekly["week_label"], rotation=45, ha="right", fontsize=7.2)
    ax3.set_ylabel("\u20b9 Millions", color=TEXT_MUTED, fontsize=7.2)
    ax3.set_ylim(0, max(bottom) * 1.10)
    # Legend ABOVE the axes in the reserved strip (pad_top): it can never
    # overlap the tall early bars, no matter how the data changes.
    leg3 = ax3.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), frameon=False,
                      fontsize=6.4, ncol=3, handlelength=0.9,
                      columnspacing=0.8, labelspacing=0.25)
    for t in leg3.get_texts():
        t.set_color(TEXT_LIGHT)

    # -- Chart 4: Top states by financial leakage ------------------------
    ax4 = _create_card(c2_x, row3_y, col_w, row_h,
                       "Top 6 States by Financial Leakage (\u20b9 Lakhs)",
                       pad_left=0.078, pad_bottom=0.040)
    state_df = leakage_by_dimension(df, "ship-state", top_n=6)
    states = [str(r["ship-state"]) if "ship-state" in state_df.columns else str(r.iloc[0])
              for _, r in state_df.iterrows()]
    state_vals = [r["leakage_amount"] / 1e5 for _, r in state_df.iterrows()]
    y_pos = np.arange(len(states))[::-1]
    bars = ax4.barh(y_pos, state_vals, height=0.55, color=C_CANCEL, alpha=0.92)
    for bar, val in zip(bars, state_vals, strict=False):
        ax4.text(val + max(state_vals) * 0.02, bar.get_y() + bar.get_height() / 2,
                 f"\u20b9{val:.1f}L", va="center", fontsize=7.2, weight="bold", color=TEXT_LIGHT)
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels([s[:18] for s in states], fontsize=7.4, color=TEXT_LIGHT)
    ax4.set_xlabel("\u20b9 Lakhs", color=TEXT_MUTED, fontsize=7.4)
    ax4.set_xlim(0, max(state_vals) * 1.22 if state_vals else 1)
    ax4.set_axisbelow(True)
    ax4.grid(axis="x", linestyle="--", alpha=0.30, color=GRID_COLOR)

    # -- Chart 5: Clearance rate vs target -------------------------------
    ax5 = _create_card(c1_x, row2_y, col_w, row_h,
                       "Settled Clearance Rate vs Target (%)", pad_left=0.036, pad_bottom=0.046)
    clr_vals = weekly["clearance"].values
    target = 70.0
    clr_plot = np.where(partial, np.nan, clr_vals)
    ax5.plot(x_idx, clr_plot, color=ACCENT, linewidth=2.4, marker="D", markersize=5,
             label="Settled Rate")
    ax5.axhline(target, color=NEUTRAL, linestyle="--", linewidth=1.5,
                label=f"Audit Target ({target:.0f}%)")
    ax5.fill_between(x_idx, clr_plot, target, where=(clr_plot < target),
                     color=ACCENT, alpha=0.10)
    ax5.set_xticks(x_idx)
    ax5.set_xticklabels(weekly["week_label"], rotation=45, ha="right", fontsize=7.2)
    ax5.set_ylim(0, 105)
    ax5.set_yticks([0, 20, 40, 60, 80, 100])
    leg5 = ax5.legend(loc="lower right", frameon=False, fontsize=7.0)
    for t in leg5.get_texts():
        t.set_color(TEXT_LIGHT)

    # -- Chart 6: Category revenue & volume ------------------------------
    ax6 = _create_card(c2_x, row2_y, col_w, row_h,
                       "Category Gross Revenue & Order Volume", pad_bottom=0.044)
    cat_df = category_revenue(df, top_n=4)
    cats = [str(r["Category"]) for _, r in cat_df.iterrows()]
    cat_rev = [r["revenue"] / 1e6 for _, r in cat_df.iterrows()]
    cat_qty = [r["orders"] / 1e4 for _, r in cat_df.iterrows()]
    c_x = np.arange(len(cats))
    cw = 0.35
    ax6.bar(c_x - cw / 2, cat_rev, width=cw, color=ACCENT, label="Revenue (\u20b9M)")
    ax6.bar(c_x + cw / 2, cat_qty, width=cw, color=C_TRANSIT, label="Orders (10K)")
    for i in range(len(cats)):
        ax6.text(c_x[i] - cw / 2, cat_rev[i] + 0.6, f"\u20b9{cat_rev[i]:.1f}M", ha="center",
                 fontsize=7.2, weight="bold", color=TEXT_LIGHT)
        ax6.text(c_x[i] + cw / 2, cat_qty[i] + 0.6, f"{cat_qty[i]:.1f}k", ha="center",
                 fontsize=7.2, weight="bold", color=TEXT_MUTED)
    ax6.set_xticks(c_x)
    ax6.set_xticklabels([c[:11] for c in cats], fontsize=7.4, weight="bold", color=TEXT_LIGHT)
    ax6.set_ylabel("Metric Scale", color=TEXT_MUTED, fontsize=7.2)
    ax6.set_ylim(0, max(max(cat_rev), max(cat_qty)) * 1.28)
    leg6 = ax6.legend(loc="upper right", frameon=False, fontsize=7.0)
    for t in leg6.get_texts():
        t.set_color(TEXT_LIGHT)

    # ------------------------------------------------------------------
    # 5. Footer
    # ------------------------------------------------------------------
    fig.text(0.50, 0.030, "Created by Ansh Thakur | Data Analyst Portfolio Dashboard",
             ha="center", va="center", color=TEXT_MUTED, fontsize=8.4, weight="bold")
    fig.text(0.50, 0.012,
             "Settled clearance = Net Realized / (Net Realized + true leakage); "
             "In-Transit is settlement lag, not loss. "
             "Partial weeks (hollow markers) are excluded from audit targets.",
             ha="center", va="center", color=NEUTRAL, fontsize=6.4)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # No bbox_inches="tight": that is what inflated the canvas to 3880x2204 and
    # left the PNG with an irregular edge. Save the exact 2560x1440 rectangle.
    fig.savefig(OUT_PATH, dpi=DPI, facecolor=CANVAS_BG)
    plt.close(fig)

    # matplotlib writes RGBA; flatten to opaque RGB so the dashboard is a
    # clean rectangle on any background (a transparent PNG renders as a
    # non-rectangular blob over a light page).
    from PIL import Image

    with Image.open(OUT_PATH) as im:
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, CANVAS_BG)
            bg.paste(im, mask=im.split()[3])
            bg.save(OUT_PATH)
        elif im.mode != "RGB":
            im.convert("RGB").save(OUT_PATH)

    with Image.open(OUT_PATH) as im:
        print(f"Successfully generated cockpit screenshot: {OUT_PATH} ({im.size[0]}x{im.size[1]} {im.mode})")


if __name__ == "__main__":
    main()
