"""Render the Executive E-Commerce Revenue Reconciliation Cockpit.

Generates docs/images/Revenue_Reconciliation_Dashboard_Cockpit.png at 2560x1440.
Aesthetic: "Metric Flow" style dark dashboard -- single coral accent theme,
fully rounded cards/pills everywhere, app top bar (brand + search + date +
avatar), navigation sidebar, dark KPI cards with delta badges.

Every number is computed from the cleaned parquet via
``src.reconciliation.metrics`` -- the same single source of truth the
Streamlit dashboard and the Excel workbook use. (The previous version of
this script hardcoded several series, which had silently drifted from the
engine output.)
"""
from __future__ import annotations
import math
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

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

PARQUET_PATH = ROOT / "data" / "processed" / "cleaned_transactions.parquet"
OUT_PATH = ROOT / "docs" / "images" / "Revenue_Reconciliation_Dashboard_Cockpit.png"

# ---- Single-accent dark theme (Metric Flow style) ----
CANVAS_BG = "#131316"
PANEL_BG = "#1B1B1F"
CARD_BG = "#202024"
CARD_HI = "#26262B"
BORDER = "#31313A"
TEXT_LIGHT = "#F4F4F5"
TEXT_MUTED = "#9CA0A8"
GRID_COLOR = "#34343C"

ACCENT = "#F4573D"        # coral primary
ACCENT_SOFT = "#F79C8D"   # soft coral
ACCENT_DEEP = "#C23F2C"   # deep coral
ACCENT_PALE = "#FBD5CE"   # pale coral
NEUTRAL = "#7C8089"       # neutral series
CHIP_BG = "#2B2B31"
CHIP_EDGE = "#3C3C45"

R_BIG = 0.014   # big rounded corners for cards
R_MED = 0.010   # medium rounding for inner boxes
R_PILL = 0.500  # pill = fully rounded

LAYOUT_TITLE_H = 0.030
CHIP_H = 0.021
CHIP_PAD_X = 0.004
CHIP_PAD_Y = 0.003
CHIP_GAP_X = 0.003
CHIP_GAP_Y = 0.002
SECTION_HEADER_H = 0.018
SECTION_TAIL = 0.003
RANK_HEAD_H = 0.016
RANK_ROW_H = 0.017
STATUS_H = 0.038


def _pill(ax, x, y, w, h, face, edge=None, lw=0.7, z=2):
    """Draw a fully-rounded pill.

    The rounding radius is derived from the box size. A fixed radius in
    axes-fraction units (e.g. 0.5) is larger than the box itself and makes
    matplotlib draw enormous sweeping curves across the whole figure, so the
    radius must scale with the pill.
    """
    radius = max(min(w, h) * 0.5, 1e-6)
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       linewidth=lw, edgecolor=edge or face, facecolor=face,
                       transform=ax.transAxes, zorder=z)
    ax.add_patch(p)
    return p


def _kpi(ax, x, y, w, h, label, value, subtext, delta, delta_up):
    """Dark rounded KPI card: muted label, big value, coral delta badge, subtext."""
    ax.add_patch(FancyBboxPatch((x, y - h), w, h,
                                boxstyle=f"round,pad=0.003,rounding_size={R_BIG}",
                                linewidth=0.8, edgecolor=BORDER, facecolor=CARD_BG,
                                transform=ax.transAxes, zorder=1))
    ax.text(x + 0.012, y - 0.024, label.upper(), color=TEXT_MUTED, fontsize=7.8,
            weight="bold", transform=ax.transAxes, va="center", ha="left", zorder=3)
    ax.text(x + 0.012, y - 0.062, value, color=TEXT_LIGHT, fontsize=19, weight="bold",
            transform=ax.transAxes, va="center", ha="left", zorder=3)
    # delta badge (pill)
    bw = 0.050
    bcol = ACCENT if delta_up else NEUTRAL
    arrow = "\u25b2" if delta_up else "\u25bc"
    _pill(ax, x + 0.012, y - 0.090, bw, 0.017, "#2E2320", edge=bcol, lw=0.7, z=3)
    ax.text(x + 0.012 + bw / 2, y - 0.0815, f"{arrow} {delta}", color=bcol, fontsize=6.8,
            weight="bold", transform=ax.transAxes, va="center", ha="center", zorder=4)
    ax.text(x + 0.012 + bw + 0.006, y - 0.0815, subtext, color=TEXT_MUTED, fontsize=6.8,
            transform=ax.transAxes, va="center", ha="left", zorder=4)


def _fit_font(text, chip_w, base, fig_w_in=19.2, dpi_pts=72.0):
    usable_pt = chip_w * fig_w_in * dpi_pts * 0.86
    est_pt = len(str(text)) * base * 0.62
    return base if est_pt <= usable_pt else max(5.0, base * usable_pt / est_pt)


def _chip(ax, x, y, w, h, text, base=7.8):
    _pill(ax, x, y, w, h, CHIP_BG, edge=CHIP_EDGE, lw=0.7)
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
    ax.add_patch(FancyBboxPatch((x_top, box_y), w, box_h,
                                boxstyle=f"round,pad=0.001,rounding_size={R_MED}",
                                linewidth=0.8, edgecolor=BORDER,
                                facecolor=CARD_BG, transform=ax.transAxes))
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
    ax.add_patch(FancyBboxPatch((x, y_top - box_h), w, box_h,
                                boxstyle=f"round,pad=0.001,rounding_size={R_MED}",
                                linewidth=0.8, edgecolor=BORDER,
                                facecolor=CARD_BG, transform=ax.transAxes))
    ax.text(x + 0.008, y_top - RANK_HEAD_H / 2, title.upper(), color=ACCENT,
            fontsize=7.8, weight="bold", transform=ax.transAxes, ha="left", va="center")
    for i, (label, value, frac) in enumerate(items):
        yc = y_top - RANK_HEAD_H - 0.006 - RANK_ROW_H * (i + 0.5)
        ax.text(x + 0.008, yc + 0.0045, label, color=TEXT_MUTED, fontsize=7.2,
                weight="bold", transform=ax.transAxes, ha="left", va="center")
        ax.text(x + w - 0.008, yc + 0.0045, value, color=TEXT_LIGHT, fontsize=7.4,
                weight="bold", transform=ax.transAxes, ha="right", va="center")
        ax.add_patch(FancyBboxPatch((x + 0.008, yc - 0.0075), (w - 0.016) * max(frac, 0.03),
                                    0.005, boxstyle="round,pad=0.0005,rounding_size=0.0025",
                                    linewidth=0, facecolor=accent, transform=ax.transAxes))
    return box_h


def _status_footer(ax, x, y_bottom, w, title, sub):
    ax.add_patch(FancyBboxPatch((x, y_bottom), w, STATUS_H,
                                boxstyle=f"round,pad=0.001,rounding_size={R_MED}",
                                linewidth=0.8, edgecolor=ACCENT, facecolor="#2A1D1A",
                                transform=ax.transAxes))
    ax.text(x + w / 2, y_bottom + STATUS_H * 0.64, title, color=ACCENT, fontsize=8.0,
            weight="bold", transform=ax.transAxes, ha="center", va="center")
    ax.text(x + w / 2, y_bottom + STATUS_H * 0.28, sub, color=TEXT_MUTED, fontsize=7.0,
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

    # Deltas compare the last full week against the first full week, so a
    # truncated window edge (W26) cannot distort them.
    full = weekly[~weekly["is_partial_week"]]
    if len(full) < 2:
        full = weekly
    d_gross = (full["gross"].iloc[-1] / full["gross"].iloc[0] - 1) * 100
    d_net = (full["net"].iloc[-1] / full["net"].iloc[0] - 1) * 100
    d_leak = (full["leakage"].iloc[-1] / max(full["leakage"].iloc[0], 1) - 1) * 100
    d_clr = full["clearance"].iloc[-1] - full["clearance"].iloc[0]
    d_aov = ((full["gross"].iloc[-1] / full["orders"].iloc[-1]) /
             (full["gross"].iloc[0] / full["orders"].iloc[0]) - 1) * 100

    fig = plt.figure(figsize=(19.2, 10.8), dpi=200, facecolor=CANVAS_BG)
    ax_bg = fig.add_axes([0, 0, 1, 1])
    ax_bg.set_facecolor(CANVAS_BG)
    ax_bg.axis("off")

    # ------------------------------------------------------------------
    # 1. App Top Bar: brand + search pill + date pill + avatar (all rounded)
    # ------------------------------------------------------------------
    tb_y, tb_h = 0.955, 0.070
    ax_bg.add_patch(FancyBboxPatch((0.010, tb_y - tb_h), 0.980, tb_h,
                                   boxstyle=f"round,pad=0.002,rounding_size={R_MED}",
                                   linewidth=0.8, edgecolor=BORDER, facecolor=PANEL_BG,
                                   transform=ax_bg.transAxes))
    # brand: coral rounded square + name
    ax_bg.add_patch(FancyBboxPatch((0.020, tb_y - 0.052), 0.014, 0.026,
                                   boxstyle="round,pad=0.001,rounding_size=0.006",
                                   linewidth=0, facecolor=ACCENT, transform=ax_bg.transAxes))
    ax_bg.text(0.040, tb_y - 0.039, "Revenue Reconciliation", color=TEXT_LIGHT, fontsize=12,
               weight="bold", va="center", transform=ax_bg.transAxes)
    # search pill
    sr_x, sr_w = 0.135, 0.300
    _pill(ax_bg, sr_x, tb_y - 0.052, sr_w, 0.026, CARD_BG, edge=BORDER, lw=0.8)
    ax_bg.text(sr_x + 0.012, tb_y - 0.039, "\U0001F50D  Search metrics, weeks, states\u2026",
               color=TEXT_MUTED, fontsize=8.0, va="center", transform=ax_bg.transAxes)
    # date pill
    _pill(ax_bg, 0.700, tb_y - 0.052, 0.150, 0.026, CARD_BG, edge=BORDER, lw=0.8)
    ax_bg.text(0.775, tb_y - 0.039, "FY22 \u00b7 W13\u2013W26 (Apr\u2013Jun)",
               color=TEXT_MUTED, fontsize=7.8, va="center", ha="center",
               transform=ax_bg.transAxes)
    # avatar circle
    ax_bg.add_patch(Circle((0.930, tb_y - 0.039), 0.0095, facecolor=ACCENT,
                           transform=ax_bg.transAxes, clip_on=False))
    ax_bg.text(0.930, tb_y - 0.039, "AT", color="#FFFFFF", fontsize=8.0, weight="bold",
               ha="center", va="center", transform=ax_bg.transAxes)

    # ------------------------------------------------------------------
    # 2. Navigation Sidebar
    # ------------------------------------------------------------------
    sb_x, sb_w = 0.012, 0.142
    sb_top = 0.880
    sb_bottom = 0.035
    ax_bg.add_patch(FancyBboxPatch((sb_x, sb_bottom), sb_w, sb_top - sb_bottom,
                                   boxstyle=f"round,pad=0.001,rounding_size={R_BIG}",
                                   linewidth=0.8, edgecolor=BORDER, facecolor=PANEL_BG,
                                   transform=ax_bg.transAxes))
    ax_bg.text(sb_x + sb_w / 2, sb_top - 0.016, "AUDIT CONTROLS", color=ACCENT,
               fontsize=9.5, weight="bold", ha="center", va="center", transform=ax_bg.transAxes)

    cy = sb_top - 0.032
    cy -= _filter_section(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                          ["W13\u2013W17 (Apr)", "W18\u2013W22 (May)", "W23\u2013W26 (Jun)"],
                          "Fiscal Period", cols=1)
    cy -= 0.006
    # Sidebar filters: all values computed from the data.
    fulfil_rows = fulfilment_settlement(df)
    fulfil_lines = [
        f"{r['Fulfilment']} ({r['gross_revenue'] / kpi.gross_revenue * 100:.1f}%)"
        for _, r in fulfil_rows.iterrows()
    ]
    cy -= _filter_section(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                          fulfil_lines, "Fulfilment Mode", cols=1)
    cy -= 0.006

    bucket_counts = df["financial_bucket"].value_counts()
    pipeline_lines = [
        f"In-Transit: {bucket_counts.get('In-Transit', 0) / 1000:.1f}k",
        f"Net Realized: {bucket_counts.get('Net Realized', 0) / 1000:.1f}k",
        f"Cancelled: {bucket_counts.get('Cancellation Leakage', 0) / 1000:.1f}k",
        f"Returned: {bucket_counts.get('Return Leakage', 0) / 1000:.1f}k",
    ]
    cy -= _filter_section(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                          pipeline_lines, "Logistics Pipeline", cols=2)
    cy -= 0.006

    channel_counts = df["Sales Channel"].value_counts() if "Sales Channel" in df.columns else df["Status"].value_counts()
    top_channels = channel_counts.head(3)
    channel_lines = [
        f"{name} ({val / len(df) * 100:.1f}%)" for name, val in top_channels.items()
    ]
    if "B2B" in df.columns:
        b2b_share = float(df["B2B"].astype(bool).sum()) / len(df) * 100
        channel_lines.append(f"B2B Wholesale ({b2b_share:.1f}%)")
    cy -= _filter_section(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                          channel_lines, "Channel & Tier", cols=1)
    cy -= 0.006

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
        cy -= 0.006

    city_df = leakage_by_dimension(df, "ship-city", top_n=4)
    city_top = float(city_df["leakage_amount"].iloc[0]) if len(city_df) else 1.0
    metro_leak = [
        (str(r["ship-city"]), f"\u20b9{r['leakage_amount'] / 1e5:,.1f}L",
         float(r["leakage_amount"]) / city_top if city_top else 0.0)
        for _, r in city_df.iterrows()
    ]
    if metro_leak:
        cy -= _rank_card(ax_bg, sb_x + 0.004, cy, sb_w - 0.008,
                         "Top Leakage Cities", metro_leak)

    _status_footer(ax_bg, sb_x + 0.004, sb_bottom + 0.004, sb_w - 0.008,
                   "AUDIT STATUS: RECONCILED",
                   f"{kpi.total_lines:,} lines | {kpi.weeks_active} Weeks Active")

    # ------------------------------------------------------------------
    # 3. KPI Row (dark rounded cards + coral delta badges)
    # ------------------------------------------------------------------
    kpi_y = 0.880
    kpi_h = 0.098
    kpi_x_start = 0.165
    kpi_total_w = 0.823
    kpi_gap = 0.010
    kpi_w = (kpi_total_w - 4 * kpi_gap) / 5

    # KPI values are computed from the data, never hardcoded.
    peak_row = weekly.loc[weekly["avg_order_value"].idxmax()]
    _kpi(ax_bg, kpi_x_start + 0 * (kpi_w + kpi_gap), kpi_y, kpi_w, kpi_h,
         "Gross Invoiced Revenue", f"\u20b9{kpi.gross_revenue / 1e6:,.2f}M",
         f"{kpi.total_lines:,} transactions",
         f"{abs(d_gross):.1f}%", d_gross >= 0)
    _kpi(ax_bg, kpi_x_start + 1 * (kpi_w + kpi_gap), kpi_y, kpi_w, kpi_h,
         "Net Realized Cash", f"\u20b9{kpi.net_realized / 1e6:,.2f}M",
         f"{kpi.unique_orders - kpi.cancelled_orders:,} settled orders",
         f"{abs(d_net):.1f}%", d_net >= 0)
    _kpi(ax_bg, kpi_x_start + 2 * (kpi_w + kpi_gap), kpi_y, kpi_w, kpi_h,
         "Total Revenue Leakage", f"\u20b9{kpi.total_leakage / 1e6:,.2f}M",
         "Cancellations + Returns",
         f"{abs(d_leak):.1f}%", d_leak <= 0)
    _kpi(ax_bg, kpi_x_start + 3 * (kpi_w + kpi_gap), kpi_y, kpi_w, kpi_h,
         "Settled Clearance Rate", f"{kpi.settled_clearance_rate:.2f}%",
         f"\u20b9{(kpi.in_transit_value + kpi.pending_value) / 1e6:,.1f}M still In-Transit",
         f"{abs(d_clr):.1f}pp", d_clr >= 0)
    _kpi(ax_bg, kpi_x_start + 4 * (kpi_w + kpi_gap), kpi_y, kpi_w, kpi_h,
         "Avg Order Value (AOV)", f"\u20b9{kpi.avg_order_value:,.2f}",
         f"Peak: {peak_row['week_label']} @ \u20b9{peak_row['avg_order_value']:,.2f}",
         f"{abs(d_aov):.1f}%", d_aov >= 0)

    # ------------------------------------------------------------------
    # 4. Chart Grid (2 rows x 3 columns, fully rounded cards)
    # ------------------------------------------------------------------
    grid_top = 0.767
    grid_bottom = 0.045
    grid_h = (grid_top - grid_bottom - 0.025) / 2
    row1_y = grid_top - grid_h
    row2_y = grid_bottom

    col_w = (kpi_total_w - 2 * 0.014) / 3
    c1_x = kpi_x_start
    c2_x = kpi_x_start + col_w + 0.014
    c3_x = kpi_x_start + 2 * (col_w + 0.014)

    def _create_card(x, y, w, h, title, pad_left=0.012):
        ax_bg.add_patch(FancyBboxPatch((x, y), w, h,
                                       boxstyle=f"round,pad=0.003,rounding_size={R_BIG}",
                                       linewidth=0.8, edgecolor=BORDER, facecolor=CARD_BG,
                                       transform=ax_bg.transAxes))
        ax_bg.text(x + 0.012, y + h - 0.024, title.upper(), color=TEXT_MUTED, fontsize=8.4,
                   weight="bold", transform=ax_bg.transAxes, va="center")
        ax = fig.add_axes([x + pad_left, y + 0.016, w - pad_left - 0.010, h - 0.046])
        ax.set_facecolor(CARD_BG)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(GRID_COLOR)
        ax.spines["bottom"].set_color(GRID_COLOR)
        ax.tick_params(colors=TEXT_MUTED, labelsize=7.5)
        ax.grid(axis="y", linestyle="--", alpha=0.30, color=GRID_COLOR)
        return ax

    # Chart 1: Weekly Gross vs Net Revenue
    ax1 = _create_card(c1_x, row1_y, col_w, grid_h, "Weekly Invoiced vs Realized Revenue (\u20b9M)")
    x_idx = np.arange(len(weekly))
    gross_m = weekly["gross"] / 1e6
    net_m = weekly["net"] / 1e6
    # W26 is a truncated window edge (3 observed days). Plot it as a hollow
    # marker and break the line so it never reads as a collapse to zero.
    partial = weekly["is_partial_week"].astype(bool).values
    gross_plot = np.where(partial, np.nan, gross_m)
    net_plot = np.where(partial, np.nan, net_m)

    ax1.plot(x_idx, gross_plot, color=ACCENT, linewidth=2.4, marker="o", markersize=4, label="Gross Invoiced")
    ax1.fill_between(x_idx, gross_plot, alpha=0.14, color=ACCENT)
    ax1.plot(x_idx, net_plot, color=NEUTRAL, linewidth=2.0, marker="s", markersize=4,
             linestyle="--", label="Net Realized")
    ax1.fill_between(x_idx, net_plot, alpha=0.10, color=NEUTRAL)
    if bool(partial.any()):
        ax1.plot(x_idx[partial], gross_m[partial], linestyle="none", marker="o",
                 markersize=7, markerfacecolor="none", markeredgecolor=ACCENT,
                 markeredgewidth=1.6, label="Partial week")

    peak_i = int(np.nanargmax(gross_plot))
    ax1.annotate(f"Peak: \u20b9{gross_m[peak_i]:.2f}M", (peak_i, gross_m[peak_i]),
                 textcoords="offset points", xytext=(0, 7),
                 ha="center", fontsize=7.2, weight="bold", color=ACCENT)
    drops = weekly["wow_net_growth"].astype(float).values
    worst_i = int(np.nanargmin(drops)) if len(drops) else 0
    if np.isfinite(drops[worst_i]) and drops[worst_i] < 0 and not partial[worst_i]:
        ax1.annotate(f"WoW Drop: {drops[worst_i]:.0f}%", (worst_i, gross_m[worst_i]),
                     textcoords="offset points", xytext=(0, -12),
                     ha="center", fontsize=7.0, weight="bold", color=ACCENT_SOFT)

    ax1.set_xticks(x_idx)
    ax1.set_xticklabels(weekly["week_label"], rotation=45, ha="right", fontsize=7.0)
    ax1.set_ylabel("\u20b9 Millions", color=TEXT_MUTED, fontsize=7.5)
    leg = ax1.legend(loc="upper right", frameon=False, fontsize=7.5)
    for t in leg.get_texts():
        t.set_color(TEXT_LIGHT)

    # Chart 2: Leakage Donut (coral shades + neutral)
    ax2 = _create_card(c2_x, row1_y, col_w, grid_h, "Revenue Leakage Breakdown (Root Causes)")
    leak_legs = [
        ("Order Cancellations", kpi.cancellation_leakage),
        ("Customer Returns", kpi.return_leakage),
        ("Transit Losses", kpi.loss_leakage),
    ]
    leak_amounts = [v / 1e6 for _, v in leak_legs]
    leak_labels = [
        f"{name}\n\u20b9{val / 1e6:,.2f}M ({val / kpi.total_leakage * 100:.1f}%)"
        for name, val in leak_legs
    ]
    leak_colors = [ACCENT, ACCENT_SOFT, "#4A4A52"]
    wedges, texts = ax2.pie(leak_amounts, labels=leak_labels, colors=leak_colors, startangle=140,
                            wedgeprops=dict(width=0.42, edgecolor=CARD_BG, linewidth=2.0),
                            textprops=dict(fontsize=7.8, weight="bold", color=TEXT_LIGHT))
    ax2.text(0, 0, f"TOTAL LEAK\n\u20b9{kpi.total_leakage / 1e6:,.2f}M", ha="center", va="center", fontsize=8.8,
             weight="bold", color=ACCENT)

    # Chart 3: Fulfillment Channel Breakdown
    ax3 = _create_card(c3_x, row1_y, col_w, grid_h, "Settlement Split by Fulfilment Flag", pad_left=0.036)
    fulfil = fulfilment_settlement(df)
    channels = [f"{r['Fulfilment']}" for _, r in fulfil.iterrows()]
    ch_gross = [r["gross_revenue"] / 1e6 for _, r in fulfil.iterrows()]
    ch_net = [r["net_realized"] / 1e6 for _, r in fulfil.iterrows()]
    ch_leak = [r["total_leakage"] / 1e6 for _, r in fulfil.iterrows()]

    bar_y = np.arange(len(channels))
    bh = 0.22
    ax3.barh(bar_y + bh, ch_gross, height=bh, color=ACCENT_SOFT, label="Gross Invoiced")
    ax3.barh(bar_y, ch_net, height=bh, color=ACCENT, label="Net Realized")
    ax3.barh(bar_y - bh, ch_leak, height=bh, color=NEUTRAL, label="Leakage")

    for i in range(len(channels)):
        ax3.text(ch_gross[i] + 0.8, bar_y[i] + bh, f"\u20b9{ch_gross[i]:.1f}M", va="center", fontsize=7.2, weight="bold", color=TEXT_LIGHT)
        ax3.text(ch_net[i] + 0.8, bar_y[i], f"\u20b9{ch_net[i]:.1f}M", va="center", fontsize=7.2, weight="bold", color=ACCENT)
        ax3.text(ch_leak[i] + 0.8, bar_y[i] - bh, f"\u20b9{ch_leak[i]:.1f}M", va="center", fontsize=7.2, weight="bold", color=TEXT_MUTED)

    ax3.set_yticks(bar_y)
    ax3.set_yticklabels(channels, fontsize=8.0, weight="bold", color=TEXT_LIGHT)
    ax3.set_xlabel("\u20b9 Millions", color=TEXT_MUTED, fontsize=7.5)
    leg3 = ax3.legend(loc="lower right", frameon=False, fontsize=7.2)
    for t in leg3.get_texts():
        t.set_color(TEXT_LIGHT)
    ax3.grid(axis="x", linestyle="--", alpha=0.30, color=GRID_COLOR)

    # Chart 4: Top 6 Leakage States
    ax4 = _create_card(c1_x, row2_y, col_w, grid_h, "Top 6 States by Financial Leakage (\u20b9 Lakhs)", pad_left=0.038)
    state_df = leakage_by_dimension(df, "ship-state", top_n=6)
    states = [str(r["ship-state"]).title() for _, r in state_df.iterrows()]
    state_vals = [r["leakage_amount"] / 1e5 for _, r in state_df.iterrows()]

    y_pos = np.arange(len(states))[::-1]
    bars = ax4.barh(y_pos, state_vals, height=0.55, color=ACCENT, alpha=0.92)
    for bar, val in zip(bars, state_vals):
        ax4.text(val + max(state_vals) * 0.02, bar.get_y() + bar.get_height() / 2, f"\u20b9{val:.1f}L",
                 va="center", fontsize=7.4, weight="bold", color=TEXT_LIGHT)

    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(states, fontsize=7.8, color=TEXT_LIGHT)
    ax4.set_xlabel("\u20b9 Lakhs", color=TEXT_MUTED, fontsize=7.5)
    ax4.set_xlim(0, max(state_vals) * 1.22 if state_vals else 1)
    ax4.grid(axis="x", linestyle="--", alpha=0.30, color=GRID_COLOR)

    # Chart 5: Clearance Rate vs Target
    ax5 = _create_card(c2_x, row2_y, col_w, grid_h, "Settled Clearance Rate vs Target (%)")
    clr_vals = weekly["clearance"].values
    target = 70.0
    clr_plot = np.where(partial, np.nan, clr_vals)

    ax5.plot(x_idx, clr_plot, color=ACCENT, linewidth=2.4, marker="D", markersize=4, label="Settled Rate")
    ax5.axhline(target, color=NEUTRAL, linestyle="--", linewidth=1.5, label=f"Audit Target ({target:.0f}%)")
    ax5.fill_between(x_idx, clr_plot, target, where=(clr_plot < target), color=ACCENT, alpha=0.10)

    ax5.set_xticks(x_idx)
    ax5.set_xticklabels(weekly["week_label"], rotation=45, ha="right", fontsize=7.0)
    ax5.set_ylabel("Clearance %", color=TEXT_MUTED, fontsize=7.5)
    ax5.set_ylim(0, 100)
    leg5 = ax5.legend(loc="upper right", frameon=False, fontsize=7.2)
    for t in leg5.get_texts():
        t.set_color(TEXT_LIGHT)

    # Chart 6: Category Revenue & Volume
    ax6 = _create_card(c3_x, row2_y, col_w, grid_h, "Category Gross Revenue & Order Volume")
    cat_df = category_revenue(df, top_n=5)
    cats = [str(r["Category"]) for _, r in cat_df.iterrows()]
    cat_rev = [r["revenue"] / 1e6 for _, r in cat_df.iterrows()]
    cat_qty = [r["orders"] / 1e4 for _, r in cat_df.iterrows()]

    c_x = np.arange(len(cats))
    cw = 0.35
    ax6.bar(c_x - cw / 2, cat_rev, width=cw, color=ACCENT, label="Revenue (\u20b9M)")
    ax6.bar(c_x + cw / 2, cat_qty, width=cw, color="#5A5A64", label="Orders (10K)")

    for i in range(len(cats)):
        ax6.text(c_x[i] - cw / 2, cat_rev[i] + 0.6, f"\u20b9{cat_rev[i]:.1f}M", ha="center", fontsize=7.0, weight="bold", color=TEXT_LIGHT)
        ax6.text(c_x[i] + cw / 2, cat_qty[i] + 0.6, f"{cat_qty[i]:.1f}k", ha="center", fontsize=7.0, weight="bold", color=TEXT_MUTED)

    ax6.set_xticks(c_x)
    ax6.set_xticklabels(cats, fontsize=7.5, weight="bold", color=TEXT_LIGHT)
    ax6.set_ylabel("Metric Scale", color=TEXT_MUTED, fontsize=7.5)
    leg6 = ax6.legend(loc="upper right", frameon=False, fontsize=7.2)
    for t in leg6.get_texts():
        t.set_color(TEXT_LIGHT)

    # Footer
    fig.text(0.50, 0.012, "Created by Ansh Thakur | Data Analyst Portfolio Dashboard",
             ha="center", va="center", color=TEXT_MUTED, fontsize=9.0, weight="bold")
    fig.text(0.50, 0.002,
             "Settled clearance = Net Realized / (Net Realized + true leakage); "
             "In-Transit is settlement lag, not loss. "
             "W26 is a partial week (3 days) and is excluded from audit targets.",
             ha="center", va="center", color=NEUTRAL, fontsize=6.4)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Successfully generated cockpit screenshot: {OUT_PATH}")


if __name__ == "__main__":
    main()
