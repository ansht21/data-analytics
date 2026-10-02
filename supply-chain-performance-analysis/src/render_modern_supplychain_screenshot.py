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

def _kpi(ax, x, y, w, h, label, value, color=NAVY_MAIN):
    ax.add_patch(FancyBboxPatch((x, y - h), w, h,
                                boxstyle="round,pad=0.003,rounding_size=0.008",
                                linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
                                transform=ax.transAxes))
    ax.add_patch(Rectangle((x, y - h + 0.004), 0.0035, h - 0.008,
                           facecolor=color, transform=ax.transAxes))
    ax.text(x + 0.010, y - h * 0.28, label.upper(), color=TEXT_MUTED, fontsize=8.5, weight="bold",
            transform=ax.transAxes, va="center", ha="left")
    ax.text(x + 0.010, y - h * 0.70, value, color=TEXT_DARK, fontsize=19, weight="bold",
            transform=ax.transAxes, va="center", ha="left")

def _chip(ax, x, y, w, h, text):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.001,rounding_size=0.008",
                                linewidth=0.6, edgecolor="#BAE6FD", facecolor=CHIP_BG,
                                transform=ax.transAxes))
    ax.text(x + w / 2, y + h / 2, text, color="#FFFFFF", fontsize=7.2, weight="bold",
            transform=ax.transAxes, ha="center", va="center")

def _filter_section(ax, x_top, y_top, w, items, label):
    chip_h = 0.018
    chip_gap_y = 0.003
    chip_pad_x = 0.004
    chip_pad_y = 0.005
    rows = math.ceil(len(items) / 2)
    body_h = chip_pad_y * 2 + rows * chip_h + (rows - 1) * chip_gap_y
    header_h = 0.024
    box_h = header_h + body_h + 0.004
    box_y = y_top - box_h
    ax.add_patch(FancyBboxPatch((x_top, box_y), w, box_h,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0.8, edgecolor=BORDER_COLOR,
                                facecolor=CARD_BG, transform=ax.transAxes))
    ax.add_patch(FancyBboxPatch((x_top, y_top - header_h), w, header_h,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0, facecolor=NAVY_MAIN, transform=ax.transAxes))
    ax.add_patch(Rectangle((x_top, y_top - header_h), w, header_h * 0.55,
                           facecolor=NAVY_MAIN, transform=ax.transAxes))
    ax.text(x_top + 0.008, y_top - header_h / 2, label, color="#FFFFFF", fontsize=9.2, weight="bold",
            transform=ax.transAxes, ha="left", va="center")
    chip_w = (w - 3 * chip_pad_x) / 2
    for i, item in enumerate(items):
        row = i // 2
        col = i % 2
        cx = x_top + chip_pad_x + col * (chip_w + chip_pad_x)
        cy = y_top - header_h - chip_pad_y - chip_h - row * (chip_h + chip_gap_y)
        _chip(ax, cx, cy, chip_w, chip_h, str(item))
    return box_h + 0.016

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
        ("Category", channels),
        ("Delivery Status", ["Late", "On Time"]),
        ("Warehouse Code", wh_codes),
        ("Order Year", order_years),
    ]
    y_cursor = panel_top_y - header_h - 0.010
    inner_x = panel_x + 0.005
    inner_w = panel_w - 0.010
    for label, items in sections:
        used = _filter_section(ax, inner_x, y_cursor, inner_w, items, label)
        y_cursor -= used + 0.002

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
    grid_y0 = 0.05
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
