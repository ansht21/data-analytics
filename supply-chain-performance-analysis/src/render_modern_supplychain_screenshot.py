"""
Generate an executive screenshot of Supplychain_Dashboard_screenshot.png
using the Ocean Executive theme (Midnight Navy + Teal):
- Top Banner: Deep Navy (#0B2A4A) with sky accent text
- Left Filters Sidebar: Soft Sky (#E0F2FE), filter chips derived from live data
- KPI Cards: Clean White (#FFFFFF) with navy/teal left accent bars
- Charts: Card-style (#FFFFFF) with subtle borders (#E2E8F0), navy/teal palette
- Delivery donut is order-based so it matches the On-Time Rate KPI exactly
"""
from __future__ import annotations
import math
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "Cleaned_Supplychain_Data.csv"
OUT_PATH = ROOT / "image" / "Supplychain_Dashboard_screenshot.png"

# Ocean Executive Theme (Midnight Navy + Teal)
NAVY_MAIN = "#0B2A4A"
TEAL_ACCENT = "#0E9F8A"
SKY_LIGHT = "#E0F2FE"
CANVAS_BG = "#F7FAFC"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E2E8F0"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"
CYAN_ACCENT = "#06B6D4"
CHIP_BG = "#0B3D66"

LAYOUT_TITLE_H = 0.034
CHIP_H = 0.024
CHIP_PAD_X = 0.004
CHIP_PAD_Y = 0.005
CHIP_GAP_X = 0.004
CHIP_GAP_Y = 0.003
SECTION_HEADER_H = 0.024
SECTION_TAIL = 0.004
FOOTER_GAP = 0.014
FOOTER_MIN_H = 0.115
MAX_SECTION_GAP = 0.070


def _kpi(ax, x, y, w, h, label, value, color=NAVY_MAIN):
    """KPI card with a fixed vertical rhythm shared by every card:
    label baseline, hairline divider, value baseline -- identical offsets so
    all five cards read as one aligned row."""
    ax.add_patch(FancyBboxPatch((x, y - h), w, h,
                                boxstyle="round,pad=0.003,rounding_size=0.008",
                                linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
                                transform=ax.transAxes))
    ax.add_patch(Rectangle((x, y - h + 0.004), 0.0035, h - 0.008,
                           facecolor=color, transform=ax.transAxes))
    ax.text(x + 0.012, y - 0.026, label.upper(), color=TEXT_MUTED, fontsize=8.5, weight="bold",
            transform=ax.transAxes, va="center", ha="left")
    ax.plot([x + 0.012, x + w - 0.012], [y - 0.042, y - 0.042],
            color=BORDER_COLOR, linewidth=0.9, transform=ax.transAxes,
            solid_capstyle="butt")
    ax.text(x + 0.012, y - 0.069, value, color=TEXT_DARK, fontsize=19, weight="bold",
            transform=ax.transAxes, va="center", ha="left")


def _fit_font(text, chip_w, base, fig_w_in=17.0, dpi_pts=72.0):
    """Shrink chip text so it can never spill outside its chip."""
    usable_pt = chip_w * fig_w_in * dpi_pts * 0.86
    est_pt = len(str(text)) * base * 0.62
    return base if est_pt <= usable_pt else max(5.0, base * usable_pt / est_pt)


def _chip(ax, x, y, w, h, text, edge="#BAE6FD", bg=None, base=7.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.001,rounding_size=0.008",
                                linewidth=0.6, edgecolor=edge, facecolor=bg or CHIP_BG,
                                transform=ax.transAxes))
    ax.text(x + w / 2, y + h / 2, text, color="#FFFFFF",
            fontsize=_fit_font(text, w, base), weight="bold",
            transform=ax.transAxes, ha="center", va="center")


def _section_box_h(rows):
    body_h = CHIP_PAD_Y * 2 + rows * CHIP_H + (rows - 1) * CHIP_GAP_Y
    return SECTION_HEADER_H + body_h + SECTION_TAIL


def _filter_section(ax, x_top, y_top, w, items, label, cols, accent,
                    chip_edge="#BAE6FD", chip_bg=None):
    rows = math.ceil(len(items) / cols)
    box_h = _section_box_h(rows)
    box_y = y_top - box_h
    ax.add_patch(FancyBboxPatch((x_top, box_y), w, box_h,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0.8, edgecolor=BORDER_COLOR,
                                facecolor=CARD_BG, transform=ax.transAxes))
    ax.add_patch(FancyBboxPatch((x_top, y_top - SECTION_HEADER_H), w, SECTION_HEADER_H,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0, facecolor=accent, transform=ax.transAxes))
    ax.add_patch(Rectangle((x_top, y_top - SECTION_HEADER_H), w, SECTION_HEADER_H * 0.55,
                           facecolor=accent, transform=ax.transAxes))
    ax.text(x_top + 0.008, y_top - SECTION_HEADER_H / 2, label, color="#FFFFFF",
            fontsize=9.2, weight="bold", transform=ax.transAxes, ha="left", va="center")
    chip_w = (w - (cols + 1) * CHIP_PAD_X) / cols
    for i, item in enumerate(items):
        row, col = divmod(i, cols)
        cx = x_top + CHIP_PAD_X + col * (chip_w + CHIP_PAD_X)
        cy = y_top - SECTION_HEADER_H - CHIP_PAD_Y - CHIP_H - row * (CHIP_H + CHIP_GAP_Y)
        _chip(ax, cx, cy, chip_w, CHIP_H, str(item), edge=chip_edge, bg=chip_bg)
    return box_h


def _panel_footer(ax, x, y_bottom, w, h, title, rows, accent):
    """Bottom-anchored data-scope card. It absorbs whatever vertical slack the
    filter stack leaves, so the sidebar always ends level with the dashboard."""
    ax.add_patch(FancyBboxPatch((x, y_bottom), w, h,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0.8, edgecolor=BORDER_COLOR,
                                facecolor=CARD_BG, transform=ax.transAxes))
    head_h = 0.022
    ax.add_patch(FancyBboxPatch((x, y_bottom + h - head_h), w, head_h,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0, facecolor=accent, transform=ax.transAxes))
    ax.add_patch(Rectangle((x, y_bottom + h - head_h), w, head_h * 0.55,
                           facecolor=accent, transform=ax.transAxes))
    ax.text(x + 0.008, y_bottom + h - head_h / 2, title, color="#FFFFFF", fontsize=8.2,
            weight="bold", transform=ax.transAxes, ha="left", va="center")
    top = y_bottom + h - head_h - 0.006
    step = (h - head_h - 0.012) / max(len(rows), 1)
    for i, (k, v) in enumerate(rows):
        y = top - step * (i + 0.5)
        ax.text(x + 0.008, y, k, color=TEXT_MUTED, fontsize=7.4,
                transform=ax.transAxes, va="center", ha="left")
        ax.text(x + w - 0.008, y, v, color=TEXT_DARK, fontsize=7.4, weight="bold",
                transform=ax.transAxes, va="center", ha="right")


def _layout_filter_panel(ax, x, panel_top_y, panel_bottom_y, w, sections,
                         accent, footer_title, footer_rows,
                         chip_edge="#BAE6FD", chip_bg=None):
    """Fill the sidebar exactly: sections get an even gap, and the leftover
    space goes to the bottom-anchored scope card. Nothing floats or overflows."""
    content_top = panel_top_y - LAYOUT_TITLE_H - 0.008
    heights = [_section_box_h(math.ceil(len(items) / cols)) for _, items, cols in sections]
    avail = content_top - panel_bottom_y
    n_gaps = max(len(sections) - 1, 1)
    gap = (avail - sum(heights) - FOOTER_GAP - FOOTER_MIN_H) / n_gaps
    gap = max(0.007, min(gap, MAX_SECTION_GAP))
    footer_h = max(FOOTER_MIN_H, avail - sum(heights) - gap * n_gaps - FOOTER_GAP)

    y = content_top
    for i, ((label, items, cols), box_h) in enumerate(zip(sections, heights)):
        _filter_section(ax, x, y, w, items, label, cols, accent,
                        chip_edge=chip_edge, chip_bg=chip_bg)
        y -= box_h + (gap if i < len(sections) - 1 else 0.0)
    _panel_footer(ax, x, panel_bottom_y, w, footer_h, footer_title, footer_rows, accent)
    return gap, footer_h

def main() -> None:
    df = pd.read_csv(DATA_PATH)
    
    fig = plt.figure(figsize=(17, 10), dpi=120)
    fig.patch.set_facecolor(CANVAS_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # 1. Top Executive Banner
    ax.add_patch(Rectangle((0, 0.94), 1, 0.06, facecolor=NAVY_MAIN, transform=ax.transAxes))
    ax.text(0.02, 0.97, "Executive Supply Chain Performance & Inventory Cockpit",
            color="#FFFFFF", fontsize=18, weight="bold",
            ha="left", va="center", transform=ax.transAxes)
    ax.text(0.98, 0.97, "Fulfillment & Network Diagnostics",
            color="#BAE6FD", fontsize=11, weight="bold",
            ha="right", va="center", transform=ax.transAxes)

    # 2. Filters Sidebar Panel
    panel_w = 0.135
    panel_x = 0.010
    panel_top_y = 0.92
    panel_bottom_y = 0.04
    ax.add_patch(FancyBboxPatch((panel_x, panel_bottom_y), panel_w, panel_top_y - panel_bottom_y,
                                boxstyle="round,pad=0.002,rounding_size=0.006",
                                linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=SKY_LIGHT, transform=ax.transAxes))
    header_h = 0.034
    ax.text(panel_x + panel_w / 2, panel_top_y - header_h / 2, "FILTER PANEL",
            color=NAVY_MAIN, fontsize=12, weight="bold",
            ha="center", va="center", transform=ax.transAxes)

    # Filter chips are derived from live data so the panel always
    # matches the charts (warehouse codes, years, channels).
    wh_codes = sorted(df["WarehouseCode"].str.replace("WARE-", "", regex=False).unique())
    order_years = sorted(pd.to_datetime(df["OrderDate"]).dt.year.astype(str).unique())
    channels = sorted(df["Sales_Channel"].unique())
    sections = [
        ("Category", channels, 2),
        ("Delivery Status", ["Late", "On Time"], 2),
        ("Warehouse Code", wh_codes, 2),
        ("Order Year", order_years, 2),
    ]
    inner_x = panel_x + 0.005
    inner_w = panel_w - 0.010
    footer_rows = [
        ("Orders in view", f"{len(df):,}"),
        ("Channels", f"{df['Sales_Channel'].nunique()}"),
        ("Warehouses", f"{df['WarehouseCode'].nunique()}"),
        ("Years", f"{order_years[0]}\u2013{order_years[-1]}"),
        ("Filter status", "All active"),
    ]
    _layout_filter_panel(ax, inner_x, panel_top_y, panel_bottom_y, inner_w, sections,
                         NAVY_MAIN, "DATA SCOPE", footer_rows,
                         chip_edge="#BAE6FD", chip_bg=CHIP_BG)

    # 3. KPI Cards
    tot_rev = df['revenue'].sum() / 1e6
    tot_prof = df['profit'].sum() / 1e6
    avg_del = df['delivery_days'].mean()
    tot_orders = len(df)
    ontime_pct = df['on_time'].mean() * 100

    kpis = [
        ("Total Net Revenue", f"${tot_rev:.2f}M", NAVY_MAIN),
        ("Total Net Profit", f"${tot_prof:.2f}M", "#059669"),
        ("Avg Delivery Days", f"{avg_del:.1f} Days", TEAL_ACCENT),
        ("Total Orders", f"{tot_orders/1000:.1f}K", "#0284C7"),
        ("On-Time Rate", f"{ontime_pct:.1f}%", "#2563EB"),
    ]
    kpi_x0 = panel_x + panel_w + 0.018
    kpi_total_w = 1 - kpi_x0 - 0.012
    kpi_gap = 0.010
    kpi_w = (kpi_total_w - 4 * kpi_gap) / 5
    kpi_h = 0.095
    kpi_top = 0.92
    for i, (label, value, color) in enumerate(kpis):
        x = kpi_x0 + i * (kpi_w + kpi_gap)
        _kpi(ax, x, kpi_top, kpi_w, kpi_h, label, value, color)

    # 4. Chart Grid (2x3)
    grid_x0 = kpi_x0
    grid_x1 = 1 - 0.012
    # bottom of the lowest chart card lands exactly on the sidebar bottom edge
    grid_y0 = panel_bottom_y - 0.005
    grid_y1 = 0.81
    row_gap = 0.032
    cell_w = (grid_x1 - grid_x0) / 3
    cell_h = (grid_y1 - grid_y0 - row_gap) / 2

    chart_titles = [
        "Revenue Trend Over Time ($M)",
        "Net Profit by Channel ($M)",
        "Delivery Status Distribution",
        "Revenue by Warehouse ($M)",
        "Avg Delivery Days Timeline",
        "Profit by Warehouse ($M)"
    ]

    for i, title in enumerate(chart_titles):
        row, col = divmod(i, 3)
        x = grid_x0 + col * cell_w
        y_top = grid_y1 - row * (cell_h + row_gap)
        
        # Background card
        ax.add_patch(FancyBboxPatch((x + 0.003, y_top - cell_h + 0.005), cell_w - 0.006, cell_h,
                                    boxstyle="round,pad=0.002,rounding_size=0.006",
                                    linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
                                    transform=ax.transAxes))

        cax = fig.add_axes([x + 0.012, y_top - cell_h + 0.016,
                            cell_w - 0.024, cell_h - 0.038])
        cax.set_facecolor(CARD_BG)
        for spine in cax.spines.values():
            spine.set_visible(False)
        cax.set_title(title, fontsize=10, weight="bold", color=NAVY_MAIN, pad=8)

        if i == 0: # Monthly Trend
            monthly = df.groupby("order_month")["revenue"].sum().div(1e6)
            cax.plot(range(len(monthly)), monthly.values, color=NAVY_MAIN, marker="o", markersize=3, linewidth=2.0)
            cax.fill_between(range(len(monthly)), monthly.values, color=SKY_LIGHT, alpha=0.7)
            cax.set_xticks(range(0, len(monthly), 5))
            cax.set_xticklabels(monthly.index[::5], rotation=30, fontsize=7, color=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=7.5, colors=TEXT_MUTED)
        elif i == 1: # Profit by Channel
            chan = df.groupby("Sales_Channel")["profit"].sum().div(1e6).sort_values()
            bars = cax.barh(chan.index, chan.values, color=TEAL_ACCENT, height=0.55)
            for b in bars:
                w = b.get_width()
                cax.text(w + 0.2, b.get_y() + b.get_height()/2, f"${w:.1f}M", va="center", fontsize=8, weight="bold", color=TEXT_DARK)
            cax.tick_params(axis="both", labelsize=7.5, colors=TEXT_MUTED)
            cax.set_xlim(0, chan.max() * 1.25)
        elif i == 2: # Delivery Status donut (order-based: matches On-Time Rate KPI)
            flags = df["on_time"].astype(bool)
            late_n, on_n = int((~flags).sum()), int(flags.sum())
            total_n = late_n + on_n
            colors = [NAVY_MAIN, "#CBD5E1"]
            wedges, _, autotexts = cax.pie(
                [late_n, on_n],
                labels=[f"Late ({late_n/total_n:.1%})", f"On-Time ({on_n/total_n:.1%})"],
                colors=colors,
                autopct="%1.0f%%", startangle=90, pctdistance=0.75,
                wedgeprops=dict(width=0.42, edgecolor=CARD_BG),
                textprops=dict(fontsize=8, color=TEXT_MUTED),
            )
            for t in autotexts:
                t.set_color("#FFFFFF")
                t.set_fontsize(8)
                t.set_weight("bold")
            cax.text(0, 0, f"{on_n/total_n:.1%}", ha="center", va="center",
                     fontsize=12, weight="bold", color=NAVY_MAIN)
        elif i == 3: # Revenue by Warehouse
            wh_rev = df.groupby("WarehouseCode")["revenue"].sum().div(1e6).sort_values(ascending=False)
            bars = cax.bar(wh_rev.index.str.replace("WARE-", ""), wh_rev.values, color=NAVY_MAIN, width=0.55)
            for b in bars:
                h = b.get_height()
                cax.text(b.get_x() + b.get_width()/2, h + 0.4, f"${h:.1f}M", ha="center", fontsize=7.5, weight="bold", color=TEXT_DARK)
            cax.tick_params(axis="both", labelsize=7.5, colors=TEXT_MUTED)
            cax.set_ylim(0, wh_rev.max() * 1.18)
        elif i == 4: # Delivery days flat line
            del_m = df.groupby("order_month")["delivery_days"].mean()
            cax.plot(range(len(del_m)), del_m.values, color=CYAN_ACCENT, linewidth=2.0)
            cax.fill_between(range(len(del_m)), del_m.values, color="#E0F2FE", alpha=0.7)
            cax.set_ylim(0, 8)
            cax.set_xticks(range(0, len(del_m), 5))
            cax.set_xticklabels(del_m.index[::5], rotation=30, fontsize=7, color=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=7.5, colors=TEXT_MUTED)
            cax.axhline(5.5, color=NAVY_MAIN, linestyle="--", linewidth=1.0, alpha=0.7)
        elif i == 5: # Profit by Warehouse
            wh_prof = df.groupby("WarehouseCode")["profit"].sum().div(1e6).sort_values(ascending=False)
            bars = cax.bar(wh_prof.index.str.replace("WARE-", ""), wh_prof.values, color=TEAL_ACCENT, width=0.55)
            for b in bars:
                h = b.get_height()
                cax.text(b.get_x() + b.get_width()/2, h + 0.15, f"${h:.1f}M", ha="center", fontsize=7.5, weight="bold", color=TEXT_DARK)
            cax.tick_params(axis="both", labelsize=7.5, colors=TEXT_MUTED)
            cax.set_ylim(0, wh_prof.max() * 1.18)

    # Footer
    ax.add_patch(Rectangle((0, 0), 1, 0.025, facecolor=CARD_BG, transform=ax.transAxes))
    ax.text(0.5, 0.013, "Created by Ansh Thakur  |  Data Analyst Portfolio Dashboard",
            color=NAVY_MAIN, fontsize=9.5, weight="bold", style="italic",
            ha="center", va="center", transform=ax.transAxes)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=120, facecolor=CANVAS_BG)
    plt.close(fig)
    print(f"Modernized Supply Chain screenshot saved to {OUT_PATH}")

if __name__ == "__main__":
    main()
