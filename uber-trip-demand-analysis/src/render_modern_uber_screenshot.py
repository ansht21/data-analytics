"""Uber executive screenshot, Ocean light theme. Part 1."""
from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "Uber_Cleaned_data.csv"
OUT_PATH = ROOT / "image" / "PowerBi_Dashboard.png"
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
PAY_COLORS = ["#0B2A4A", "#0E9F8A", "#06B6D4", "#94A3B8", "#F59E0B"]
VEH_COLOR = "#0E9F8A"

def _kpi(ax, x, y, w, h, label, value, color=NAVY_MAIN):
    ax.add_patch(FancyBboxPatch((x, y - h), w, h,
        boxstyle="round,pad=0.003,rounding_size=0.008",
        linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
        transform=ax.transAxes))
    ax.add_patch(Rectangle((x, y - h + 0.004), 0.0035, h - 0.008,
        facecolor=color, transform=ax.transAxes))
    ax.text(x + 0.012, y - 0.026, label.upper(), color=TEXT_MUTED,
            fontsize=8, weight="bold", transform=ax.transAxes, va="center", ha="left")
    ax.plot([x + 0.012, x + w - 0.012], [y - 0.044, y - 0.044],
        color=BORDER_COLOR, linewidth=0.9, transform=ax.transAxes)
    ax.text(x + 0.012, y - 0.074, value, color=TEXT_DARK, fontsize=17,
        weight="bold", transform=ax.transAxes, va="center", ha="left")

def _card(ax, x, y, w, h):
    ax.add_patch(FancyBboxPatch((x, y - h), w, h,
        boxstyle="round,pad=0.003,rounding_size=0.008",
        linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
        transform=ax.transAxes))

def _card_axes(fig, x, y, w, h):
    return fig.add_axes([x + 0.008, y - h + 0.045, w - 0.016, h - 0.075])


# ---- Sidebar helpers (Ocean Executive theme) ----
CHIP_H = 0.030
CHIP_GAP = 0.006
SEC_HEAD_H = 0.024
SEC_PAD = 0.010


def _chip(ax, x, y, w, h, text, base=7.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.001,rounding_size=0.008",
        linewidth=0.6, edgecolor="#BAE6FD", facecolor=CHIP_BG,
        transform=ax.transAxes))
    ax.text(x + w / 2, y + h / 2, text, color="#FFFFFF",
            fontsize=base, weight="bold",
            transform=ax.transAxes, ha="center", va="center")


def _sec_h(n):
    return SEC_HEAD_H + SEC_PAD + n * CHIP_H + (n - 1) * CHIP_GAP


def _section(ax, x, y_top, w, label, items):
    """Sidebar filter section: navy header bar + one chip per item."""
    h = _sec_h(len(items))
    ax.add_patch(FancyBboxPatch((x, y_top - h), w, h,
        boxstyle="round,pad=0.001,rounding_size=0.006",
        linewidth=0.8, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
        transform=ax.transAxes))
    ax.add_patch(FancyBboxPatch((x, y_top - SEC_HEAD_H), w, SEC_HEAD_H,
        boxstyle="round,pad=0.001,rounding_size=0.006",
        linewidth=0, facecolor=NAVY_MAIN, transform=ax.transAxes))
    ax.text(x + 0.008, y_top - SEC_HEAD_H / 2, label, color="#FFFFFF",
            fontsize=8.2, weight="bold", transform=ax.transAxes,
            ha="left", va="center")
    cy = y_top - SEC_HEAD_H - SEC_PAD - CHIP_H
    for it in items:
        _chip(ax, x + 0.006, cy, w - 0.012, CHIP_H, str(it))
        cy -= (CHIP_H + CHIP_GAP)
    return h


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    trips = len(df)
    revenue = df["Fare_Amount"].sum()
    avg_fare = df["Fare_Amount"].mean()
    avg_rating = df["Rating"].mean()

    fig = plt.figure(figsize=(11.29, 7.83), dpi=100)
    fig.patch.set_facecolor(CANVAS_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # 1. Top Executive Banner
    ax.add_patch(Rectangle((0, 0.93), 1, 0.07, facecolor=NAVY_MAIN, transform=ax.transAxes))
    ax.text(0.015, 0.968, "Uber Trip Demand & Revenue Analytics Dashboard",
            color="#FFFFFF", fontsize=15.5, weight="bold",
            ha="left", va="center", transform=ax.transAxes)
    ax.text(0.985, 0.968, "Power BI Executive View",
            color="#BAE6FD", fontsize=9.5, weight="bold",
            ha="right", va="center", transform=ax.transAxes)

    # 2. Filters Sidebar (chips derived from live data)
    panel_x, panel_w = 0.010, 0.145
    panel_top, panel_bot = 0.915, 0.045
    ax.add_patch(FancyBboxPatch((panel_x, panel_bot), panel_w, panel_top - panel_bot,
        boxstyle="round,pad=0.002,rounding_size=0.006",
        linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=SKY_LIGHT, transform=ax.transAxes))
    header_h = 0.030
    ax.text(panel_x + panel_w / 2, panel_top - header_h / 2, "FILTER PANEL",
            color=NAVY_MAIN, fontsize=10.5, weight="bold",
            ha="center", va="center", transform=ax.transAxes)

    vehicles = list(df["Vehicle_Type"].value_counts().index)
    payments = list(df["Payment_Method"].value_counts().index)
    periods = list(df["Time_Period"].value_counts().index)
    sections = [
        ("Vehicle Type", vehicles),
        ("Payment Method", payments),
        ("Time Period", periods),
        ("Trip Zone", ["Airport", "Local"]),
    ]
    inner_x = panel_x + 0.006
    inner_w = panel_w - 0.012
    footer_h = 0.042
    content_top = panel_top - header_h - 0.006
    heights = [_sec_h(len(items)) for _, items in sections]
    avail = content_top - (panel_bot + footer_h)
    gap = max(0.006, (avail - sum(heights)) / (len(sections) + 1))
    y = content_top - gap
    for (label, items), h in zip(sections, heights):
        _section(ax, inner_x, y, inner_w, label, items)
        y -= h + gap
    ax.add_patch(FancyBboxPatch((inner_x, panel_bot + 0.004), inner_w, footer_h - 0.008,
        boxstyle="round,pad=0.001,rounding_size=0.006",
        linewidth=0.8, edgecolor=BORDER_COLOR, facecolor=NAVY_MAIN, transform=ax.transAxes))
    ax.text(panel_x + panel_w / 2, panel_bot + 0.025, "ALL FILTERS ACTIVE",
            color="#FFFFFF", fontsize=7.8, weight="bold",
            ha="center", va="center", transform=ax.transAxes)
    ax.text(panel_x + panel_w / 2, panel_bot + 0.011, f"{trips:,} trips in view",
            color="#BAE6FD", fontsize=6.8, ha="center", va="center", transform=ax.transAxes)

    # 3. KPI Cards
    kpis = [
        ("Total Trips", f"{trips/1000:.0f}K", NAVY_MAIN),
        ("Revenue", f"Rs {revenue/1e6:.2f}M", TEAL_ACCENT),
        ("Avg Fare", f"Rs {avg_fare:.0f}", CYAN_ACCENT),
        ("Avg Rating", f"{avg_rating:.2f}", "#F59E0B"),
    ]
    kpi_x0 = 0.170
    kpi_gap = 0.010
    kpi_w = (1 - 0.012 - kpi_x0 - 3 * kpi_gap) / 4
    kpi_h = 0.095
    kpi_top = 0.915
    for i, (label, value, color) in enumerate(kpis):
        _kpi(ax, kpi_x0 + i * (kpi_w + kpi_gap), kpi_top, kpi_w, kpi_h, label, value, color)

    # 4. Chart Grid (2x2)
    grid_x0, grid_x1 = kpi_x0, 1 - 0.012
    grid_y1 = kpi_top - kpi_h - 0.024
    grid_y0 = 0.045
    row_gap = 0.028
    cell_w = (grid_x1 - grid_x0 - 0.020) / 2
    cell_h = (grid_y1 - grid_y0 - row_gap) / 2
    chart_titles = [
        "Hourly Trip Demand (trips)",
        "Trips by Vehicle Type",
        "Payment Mix",
        "Fare vs Trip Distance",
    ]
    hourly = df.groupby("Hour").size().reindex(range(24), fill_value=0)
    for i, title in enumerate(chart_titles):
        row, col = divmod(i, 2)
        x = grid_x0 + col * (cell_w + 0.020)
        y_top = grid_y1 - row * (cell_h + row_gap)
        ax.add_patch(FancyBboxPatch((x + 0.003, y_top - cell_h + 0.005), cell_w - 0.006, cell_h,
            boxstyle="round,pad=0.002,rounding_size=0.006",
            linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG, transform=ax.transAxes))
        cax = fig.add_axes([x + 0.014, y_top - cell_h + 0.017, cell_w - 0.028, cell_h - 0.047])
        cax.set_facecolor(CARD_BG)
        for spine in cax.spines.values():
            spine.set_visible(False)
        cax.set_title(title, fontsize=10, weight="bold", color=NAVY_MAIN, pad=7)

        if i == 0:  # Hourly demand: navy bars, peak @18 emphasized, teal @17
            colors = ["#AFC0D4"] * 24
            colors[18] = NAVY_MAIN
            colors[17] = TEAL_ACCENT
            cax.bar(hourly.index, hourly.values, color=colors, width=0.78)
            cax.set_xticks(range(0, 24, 2))
            cax.tick_params(axis="both", labelsize=7.5, colors=TEXT_MUTED)
            cax.set_ylim(0, hourly.max() * 1.18)
            for xi in (17, 18):
                cax.annotate(f"{hourly[xi]:,}",
                             xy=(xi, hourly[xi]), xytext=(0, 4),
                             textcoords="offset points", ha="center",
                             fontsize=7.5, weight="bold",
                             color=TEAL_ACCENT if xi == 17 else NAVY_MAIN)
            cax.axhline(hourly.mean(), color="#CBD5E1", linestyle="--", linewidth=1.0)
            cax.text(23.4, hourly.mean(), " avg", va="bottom", ha="right",
                     fontsize=6.8, color=TEXT_MUTED, weight="bold")
        elif i == 1:  # Vehicle types: teal hbar
            vc = df["Vehicle_Type"].value_counts().sort_values()
            cax.barh(vc.index, vc.values, color=VEH_COLOR, height=0.58)
            cax.tick_params(axis="both", labelsize=7.5, colors=TEXT_MUTED)
            cax.set_xlim(0, vc.max() * 1.16)
            for name, v in vc.items():
                cax.text(v + vc.max() * 0.02, name, f"{v:,}", va="center",
                         fontsize=7.5, weight="bold", color=TEXT_DARK)
        elif i == 2:  # Payment donut, center = total trips
            pm = df["Payment_Method"].value_counts()
            wedges, _, autotexts = cax.pie(
                pm.values, labels=pm.index, colors=PAY_COLORS[:len(pm)],
                autopct="%1.0f%%", startangle=90, pctdistance=0.78,
                wedgeprops=dict(width=0.42, edgecolor=CARD_BG),
                textprops=dict(fontsize=7.2, color=TEXT_MUTED),
            )
            for t in autotexts:
                t.set_color("#FFFFFF")
                t.set_fontsize(7.0)
                t.set_weight("bold")
            cax.text(0, 0.08, f"{trips/1000:.0f}K", ha="center", va="center",
                     fontsize=14, weight="bold", color=NAVY_MAIN)
            cax.text(0, -0.16, "trips", ha="center", va="center",
                     fontsize=7.5, color=TEXT_MUTED, weight="bold")
        elif i == 3:  # Fare vs distance scatter (sample 2500, seed 42)
            smp = df.sample(n=min(2500, len(df)), random_state=42)
            cax.scatter(smp["Trip_Distance_km"], smp["Fare_Amount"],
                        s=12, alpha=0.45, color=CYAN_ACCENT, edgecolors="none")
            cax.tick_params(axis="both", labelsize=7.5, colors=TEXT_MUTED)
            cax.set_xlabel("Trip Distance (km)", fontsize=8, color=TEXT_MUTED)
            cax.set_ylabel("Fare (Rs)", fontsize=8, color=TEXT_MUTED)

    # 5. Footer
    ax.add_patch(Rectangle((0, 0), 1, 0.030, facecolor=CARD_BG, transform=ax.transAxes))
    ax.text(0.5, 0.015, "Created by Ansh Thakur  |  Data Analyst Portfolio Dashboard",
            color=NAVY_MAIN, fontsize=9, weight="bold", style="italic",
            ha="center", va="center", transform=ax.transAxes)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=100, facecolor=CANVAS_BG)
    plt.close(fig)
    print(f"Saved {OUT_PATH} ({trips:,} trips, Rs {revenue/1e6:.2f}M revenue)")


if __name__ == "__main__":
    main()

