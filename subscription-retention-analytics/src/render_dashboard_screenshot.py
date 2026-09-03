"""
Render a PNG screenshot of the Subscription Retention Dashboard
that matches the rebuilt Excel layout (Filters left, KPI cards top
right, 3x2 chart grid below, footer).
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "Telco_Customer_Churn.csv"
OUT_PATH = ROOT / "image" / "Churn_Dashboard_screenshot.png"

# Palette - more saturated/darker tones
NAVY = "#1F3864"
NAVY_DARK = "#0F2A4D"
BLUE = "#2F75B5"
BG = "#E9EDF4"
WHITE = "#FFFFFF"
RED = "#B0252A"
ORANGE = "#C65911"
ORANGE_DARK = "#A14E0C"
GREEN = "#3E7C2A"
PANEL_BLUE = "#1F4E79"
TEXT = "#1F2937"
PANEL_BG = "#FFFFFF"


def _kpi(ax, x, y, w, h, label, value, color):
    ax.add_patch(FancyBboxPatch((x, y - h * 0.28), w, h * 0.28,
                                boxstyle="round,pad=0.003,rounding_size=0.008",
                                linewidth=0, facecolor=color, transform=ax.transAxes))
    ax.text(x + w * 0.018, y - h * 0.14, label, color=WHITE, fontsize=10, weight="bold",
            transform=ax.transAxes, va="center", ha="left")
    ax.add_patch(FancyBboxPatch((x, y - h * 0.92), w, h * 0.64,
                                boxstyle="round,pad=0.003,rounding_size=0.008",
                                linewidth=0.8, edgecolor="#A8B0C0", facecolor=WHITE,
                                transform=ax.transAxes))
    ax.text(x + w * 0.018, y - h * 0.60, value, color=NAVY_DARK, fontsize=18, weight="bold",
            transform=ax.transAxes, va="center", ha="left")


def _chip(ax, x, y, w, h, text):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.001,rounding_size=0.008",
                                linewidth=0.6, edgecolor=NAVY_DARK, facecolor=PANEL_BLUE,
                                transform=ax.transAxes))
    ax.text(x + w / 2, y + h / 2, text, color=WHITE, fontsize=8, weight="bold",
            transform=ax.transAxes, ha="center", va="center")


def _filter_section(ax, x, y, w, items, label, section_w):
    bar_h = 0.022
    ax.add_patch(Rectangle((x, y - bar_h), section_w, bar_h,
                           facecolor=NAVY_DARK, transform=ax.transAxes))
    ax.text(x + 0.008, y - bar_h / 2, label, color=WHITE, fontsize=9.5, weight="bold",
            transform=ax.transAxes, ha="left", va="center")
    chip_h = 0.022
    chip_gap_y = 0.005
    chip_pad_x = 0.003
    chip_w = (section_w - 3 * chip_pad_x) / 2
    for i, item in enumerate(items):
        row = i // 2
        col = i % 2
        cx = x + chip_pad_x + col * (chip_w + chip_pad_x)
        cy = y - bar_h - chip_h - chip_gap_y - row * (chip_h + chip_gap_y)
        _chip(ax, cx, cy, chip_w, chip_h, item)
    rows_used = math.ceil(len(items) / 2)
    total_h = bar_h + rows_used * chip_h + (rows_used - 1) * chip_gap_y + chip_gap_y
    return total_h


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).copy()
    df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)
    df["RevenueAtRisk"] = df["MonthlyCharges"] * df["ChurnFlag"]
    df["tenure_band"] = pd.cut(df["tenure"], bins=[-1, 6, 12, 24, 48, 72],
                                labels=["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"])

    fig = plt.figure(figsize=(17, 10), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title bar
    ax.add_patch(Rectangle((0, 0.94), 1, 0.06, facecolor=NAVY, transform=ax.transAxes))
    ax.text(0.5, 0.97, "Executive Supply Chain Analytics  Dashboard", color=WHITE,
            fontsize=22, weight="bold", ha="center", va="center", transform=ax.transAxes)

    # Filters panel
    panel_w = 0.165
    panel_x = 0.010
    panel_top_y = 0.91
    panel_bottom_y = 0.05
    panel_h = panel_top_y - panel_bottom_y
    ax.add_patch(FancyBboxPatch((panel_x, panel_bottom_y), panel_w, panel_h,
                                boxstyle="round,pad=0.002,rounding_size=0.006",
                                linewidth=0, facecolor=NAVY_DARK, transform=ax.transAxes))
    header_h = 0.04
    ax.text(panel_x + panel_w / 2, panel_top_y - header_h / 2, "Filters",
            color=WHITE, fontsize=14, weight="bold",
            ha="center", va="center", transform=ax.transAxes)

    sections = [
        ("Category", ["Month-to-month", "One year", "Two year"]),
        ("Supplier", ["DSL", "Fiber optic", "No Internet"]),
        ("Delivery Status", ["Churned", "Retained"]),
        ("Warehouse Code", ["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"]),
    ]
    y_cursor = panel_top_y - header_h - 0.012
    inner_x = panel_x + 0.006
    inner_w = panel_w - 0.012
    for label, items in sections:
        used = _filter_section(ax, inner_x, y_cursor, inner_w, items, label, inner_w)
        y_cursor -= used + 0.010

    # KPI cards
    kpis = [
        ("Total Customers", f"{len(df):,}", GREEN),
        ("Churn Rate", f"{df['ChurnFlag'].mean():.1%}", RED),
        ("Avg Tenure", f"{df['tenure'].mean():.1f} mo", ORANGE_DARK),
        ("Revenue at Risk", f"${df['RevenueAtRisk'].sum()/1000:,.0f}K", RED),
        ("Retention Rate", f"{1-df['ChurnFlag'].mean():.1%}", GREEN),
    ]
    kpi_x0 = panel_x + panel_w + 0.012
    kpi_total_w = 1 - kpi_x0 - 0.012
    kpi_w = (kpi_total_w - 0.012) / 5
    kpi_h = 0.10
    kpi_top = 0.92
    for i, (label, value, color) in enumerate(kpis):
        x = kpi_x0 + i * (kpi_w + 0.003)
        _kpi(ax, x, kpi_top, kpi_w, kpi_h, label, value, color)

    # Chart grid
    chart_specs = [
        ("Churn Rate by Contract", "contract"),
        ("Churn Rate by Tenure Band", "tenure"),
        ("Customer Mix by Internet Service", "service"),
        ("Top Revenue-at-Risk Segments", "risk"),
        ("Churn Rate by Payment Method", "payment"),
        ("Churn Rate by Tenure (months)", "tenure_trend"),
    ]
    grid_x0 = kpi_x0
    grid_x1 = 1 - 0.012
    grid_y0 = 0.07
    grid_y1 = 0.80
    cell_w = (grid_x1 - grid_x0) / 3
    cell_h = (grid_y1 - grid_y0) / 2

    for i, (title, key) in enumerate(chart_specs):
        row, col = divmod(i, 3)
        x = grid_x0 + col * cell_w + 0.006
        # Stack top and bottom row with a visible gap between them
        y = grid_y1 - (row + 1) * cell_h + 0.040 if row == 0 else grid_y1 - (row + 1) * cell_h + 0.005
        cax = fig.add_axes([x, y, cell_w - 0.012, cell_h - 0.050])
        cax.set_facecolor(PANEL_BG)
        for spine in cax.spines.values():
            spine.set_color("#B8C0D0")
            spine.set_linewidth(0.8)
        cax.set_title(title, fontsize=10, weight="bold", color=NAVY_DARK, pad=8)

        if key == "contract":
            data = df.groupby("Contract", observed=True)["ChurnFlag"].mean().mul(100).reindex(
                ["Month-to-month", "One year", "Two year"])
            cax.bar(data.index, data.values, color=BLUE, width=0.55)
            cax.set_ylabel("Churn Rate %", fontsize=8, color=TEXT)
            cax.tick_params(axis="x", labelsize=8, rotation=0)
            cax.tick_params(axis="y", labelsize=8)
            for s in cax.spines.values():
                s.set_visible(False)
            for j, v in enumerate(data.values):
                cax.text(j, v + 1, f"{v:.1f}", ha="center", fontsize=8, color=TEXT, weight="bold")
            cax.set_ylim(0, max(data.values) * 1.20)
        elif key == "tenure":
            data = df.groupby("tenure_band", observed=True)["ChurnFlag"].mean().mul(100)
            cax.plot(data.index.astype(str), data.values, color=BLUE, marker="o", linewidth=2.2, markersize=5)
            cax.fill_between(range(len(data)), data.values, color=BLUE, alpha=0.18)
            cax.set_ylabel("Churn Rate %", fontsize=8, color=TEXT)
            cax.tick_params(axis="x", labelsize=8)
            cax.tick_params(axis="y", labelsize=8)
            for j, v in enumerate(data.values):
                cax.text(j, v + 1, f"{v:.1f}", ha="center", fontsize=8, color=TEXT, weight="bold")
            for s in cax.spines.values():
                s.set_visible(False)
        elif key == "service":
            data = df.groupby("InternetService", observed=True)["customerID"].count()
            colors = ["#2F75B5", "#F4B183", "#7E3F98"]
            wedges, _, autotexts = cax.pie(
                data.values, labels=data.index, colors=colors,
                autopct="%1.0f%%", startangle=90,
                wedgeprops=dict(width=0.42, edgecolor=WHITE),
                textprops=dict(fontsize=8, color=TEXT),
            )
            for t in autotexts:
                t.set_color(WHITE)
                t.set_fontsize(8)
                t.set_weight("bold")
        elif key == "payment":
            data = df.groupby("PaymentMethod", observed=True)["ChurnFlag"].mean().mul(100).sort_values()
            cax.barh(data.index, data.values, color=BLUE)
            cax.set_xlabel("Churn Rate %", fontsize=8, color=TEXT)
            cax.tick_params(axis="x", labelsize=8)
            cax.tick_params(axis="y", labelsize=8)
            for j, v in enumerate(data.values):
                cax.text(v + 0.6, j, f"{v:.1f}", va="center", fontsize=8, color=TEXT, weight="bold")
            for s in cax.spines.values():
                s.set_visible(False)
            cax.set_xlim(0, max(data.values) * 1.18)
        elif key == "risk":
            grp = (df.groupby(["Contract", "InternetService"], observed=True)
                     .agg(rev=("RevenueAtRisk", "sum"))
                     .sort_values("rev", ascending=False).head(8))
            grp["label"] = [f"{c} | {i}" for c, i in grp.index]
            grp["rev"] = grp["rev"] / 1000
            cax.barh(grp["label"][::-1], grp["rev"][::-1], color=GREEN)
            cax.set_xlabel("Revenue at Risk ($K)", fontsize=8, color=TEXT)
            cax.tick_params(axis="x", labelsize=8)
            cax.tick_params(axis="y", labelsize=7)
            for s in cax.spines.values():
                s.set_visible(False)
        elif key == "tenure_trend":
            t = df.groupby("tenure")["ChurnFlag"].mean().mul(100)
            t = t.iloc[::3]
            cax.plot(t.index, t.values, color=ORANGE, linewidth=2.2)
            cax.fill_between(t.index, t.values, color=ORANGE, alpha=0.30)
            cax.set_ylabel("Churn Rate %", fontsize=8, color=TEXT)
            cax.set_xlabel("Tenure (months)", fontsize=8, color=TEXT)
            cax.tick_params(axis="x", labelsize=7)
            cax.tick_params(axis="y", labelsize=8)
            for s in cax.spines.values():
                s.set_visible(False)

    # Footer
    ax.add_patch(Rectangle((0, 0), 1, 0.035, facecolor=WHITE, transform=ax.transAxes))
    ax.text(0.5, 0.018, "Created by Ansh Thakur  |  Data Analyst Portfolio Dashboard",
            color=NAVY_DARK, fontsize=11, weight="bold", style="italic",
            ha="center", va="center", transform=ax.transAxes)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=100, facecolor=BG)
    plt.close(fig)
    print(f"Dashboard screenshot saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
