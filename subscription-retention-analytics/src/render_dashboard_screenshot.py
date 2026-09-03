"""
Render a PNG screenshot of the Subscription Retention Dashboard
that matches the rebuilt Excel layout (Filters left, KPI cards top
right, 3x2 chart grid below, footer).

This complements the live xlsx file because it gives a quick visual
preview for the README without requiring Excel/LibreOffice to render.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "Telco_Customer_Churn.csv"
OUT_PATH = ROOT / "image" / "Churn_Dashboard_screenshot.png"

NAVY = "#1F3864"
NAVY_DARK = "#172B4D"
BLUE = "#2F75B5"
TEAL = "#00A6A6"
LIGHT_BLUE = "#DDEBF7"
BG = "#F4F6FA"
WHITE = "#FFFFFF"
RED = "#C00000"
ORANGE = "#F4B183"
ORANGE_DARK = "#C65911"
GREEN = "#548235"
PANEL_BLUE = "#5B7BB7"
TEXT = "#1F2937"


def _kpi(ax, x, y, w, h, label, value, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h * 0.32, boxstyle="round,pad=0.005,rounding_size=0.01",
                                linewidth=0, facecolor=color, transform=ax.transAxes))
    ax.text(x + w * 0.02, y + h * 0.20, label, color=WHITE, fontsize=10, weight="bold",
            transform=ax.transAxes, va="center", ha="left")
    ax.add_patch(FancyBboxPatch((x, y - h * 0.20), w, h * 0.32, boxstyle="round,pad=0.005,rounding_size=0.01",
                                linewidth=0.5, edgecolor="#D0D0D0", facecolor=WHITE, transform=ax.transAxes))
    ax.text(x + w * 0.02, y - h * 0.04, value, color=NAVY, fontsize=20, weight="bold",
            transform=ax.transAxes, va="center", ha="left")


def _chip(ax, x, y, w, h, text):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.002,rounding_size=0.01",
                                linewidth=0, facecolor=PANEL_BLUE, transform=ax.transAxes))
    ax.text(x + w / 2, y + h / 2, text, color=WHITE, fontsize=8.5, weight="bold",
            transform=ax.transAxes, ha="center", va="center")


def _filter_section(ax, x, y, w, h_header, h_chips, label, items):
    ax.add_patch(Rectangle((x, y - h_header - h_chips), w, h_header, facecolor=NAVY_DARK,
                           transform=ax.transAxes))
    ax.text(x + 0.01, y - h_header / 2, label, color=WHITE, fontsize=10, weight="bold",
            transform=ax.transAxes, ha="left", va="center")
    chips_per_row = 4
    chip_w = w / chips_per_row
    for i, item in enumerate(items):
        cx = x + (i % chips_per_row) * chip_w
        cy = y - h_header - h_chips + (i // chips_per_row) * 0.035
        _chip(ax, cx + 0.002, cy + 0.005, chip_w - 0.004, 0.028, item)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).copy()
    df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)
    df["RevenueAtRisk"] = df["MonthlyCharges"] * df["ChurnFlag"]
    df["tenure_band"] = pd.cut(df["tenure"], bins=[-1, 6, 12, 24, 48, 72],
                                labels=["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"])

    fig = plt.figure(figsize=(16, 9.2), dpi=110)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # --- Title bar ---
    ax.add_patch(Rectangle((0, 0.93), 1, 0.07, facecolor=NAVY, transform=ax.transAxes))
    ax.text(0.5, 0.965, "Executive Supply Chain Analytics  Dashboard", color=WHITE,
            fontsize=20, weight="bold", ha="center", va="center", transform=ax.transAxes)

    # --- Filters panel (left) ---
    panel_x, panel_w = 0.012, 0.155
    # Panel header
    ax.add_patch(FancyBboxPatch((panel_x, 0.83), panel_w, 0.06,
                                boxstyle="round,pad=0.002,rounding_size=0.01",
                                facecolor=NAVY_DARK, transform=ax.transAxes))
    ax.text(panel_x + panel_w / 2, 0.86, "Filters", color=WHITE, fontsize=14, weight="bold",
            ha="center", va="center", transform=ax.transAxes)

    sections = [
        ("Category", ["Month-to-month", "One year", "Two year"]),
        ("Supplier", ["DSL", "Fiber optic", "No"]),
        ("Delivery Status", ["Churned", "Retained"]),
        ("Warehouse Code", ["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"]),
    ]
    y = 0.78
    for label, items in sections:
        _filter_section(ax, panel_x, y, panel_w, 0.025, 0.07, label, items)
        rows_used = math.ceil(len(items) / 4)
        y -= 0.025 + 0.035 * rows_used + 0.012

    # --- KPI cards (top right) ---
    kpis = [
        ("Total Customers", f"{len(df):,}", GREEN),
        ("Churn Rate", f"{df['ChurnFlag'].mean():.1%}", RED),
        ("Avg Tenure", f"{df['tenure'].mean():.1f} mo", ORANGE_DARK),
        ("Revenue at Risk", f"${df['RevenueAtRisk'].sum()/1000:,.0f}K", RED),
        ("Retention Rate", f"{1-df['ChurnFlag'].mean():.1%}", GREEN),
    ]
    kpi_x0 = 0.183
    kpi_w = (1 - kpi_x0 - 0.012) / 5
    kpi_h = 0.13
    for i, (label, value, color) in enumerate(kpis):
        x = kpi_x0 + i * kpi_w + 0.003
        _kpi(ax, x, 0.89, kpi_w - 0.006, kpi_h, label, value, color)

    # --- Chart grid (3 cols x 2 rows) ---
    chart_specs = [
        ("Churn Rate by Contract", "col", "contract"),
        ("Churn Rate by Tenure Band", "line", "tenure"),
        ("Customer Mix by Internet Service", "doughnut", "service"),
        ("Top Revenue-at-Risk Segments", "bar", "risk"),
        ("Churn Rate by Payment Method", "col", "payment"),
        ("Churn Rate by Tenure (months)", "line", "tenure_trend"),
    ]

    grid_x0, grid_y0 = 0.183, 0.05
    grid_w, grid_h = 1 - grid_x0 - 0.012, 0.78
    cell_w = grid_w / 3
    cell_h = grid_h / 2

    for i, (title, kind, key) in enumerate(chart_specs):
        row, col = divmod(i, 3)
        x = grid_x0 + col * cell_w + 0.006
        y = grid_y0 + (1 - row) * cell_h + 0.006
        cax = fig.add_axes([x, y, cell_w - 0.012, cell_h - 0.012])
        cax.set_facecolor(WHITE)
        for spine in cax.spines.values():
            spine.set_color("#D0D0D0")
        cax.set_title(title, fontsize=10, weight="bold", color=NAVY, pad=6)

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
                cax.text(j, v + 1, f"{v:.1f}", ha="center", fontsize=8, color=TEXT)
            cax.set_ylim(0, max(data.values) * 1.2)
        elif key == "tenure":
            data = df.groupby("tenure_band", observed=True)["ChurnFlag"].mean().mul(100)
            cax.plot(data.index.astype(str), data.values, color=BLUE, marker="o", linewidth=2)
            cax.fill_between(range(len(data)), data.values, color=BLUE, alpha=0.15)
            cax.set_ylabel("Churn Rate %", fontsize=8, color=TEXT)
            cax.tick_params(axis="x", labelsize=8)
            cax.tick_params(axis="y", labelsize=8)
            for j, v in enumerate(data.values):
                cax.text(j, v + 1, f"{v:.1f}", ha="center", fontsize=8, color=TEXT)
            for s in cax.spines.values():
                s.set_visible(False)
        elif key == "service":
            data = df.groupby("InternetService", observed=True)["customerID"].count()
            colors = ["#5B7BB7", "#F4B183", "#9C27B0"]
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
                cax.text(v + 0.6, j, f"{v:.1f}", va="center", fontsize=8, color=TEXT)
            for s in cax.spines.values():
                s.set_visible(False)
            cax.set_xlim(0, max(data.values) * 1.18)
        elif key == "risk":
            grp = (df.groupby(["Contract", "InternetService"], observed=True)
                     .agg(customers=("customerID", "count"),
                          rev=("RevenueAtRisk", "sum"),
                          churn=("ChurnFlag", "mean"))
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

    # --- Footer ---
    ax.text(0.5, 0.025, "Created by Ansh Thakur  |  Data Analyst Portfolio Dashboard",
            color=NAVY, fontsize=11, weight="bold", style="italic",
            ha="center", va="center", transform=ax.transAxes)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=150, facecolor=BG, bbox_inches="tight", pad_inches=0.05)
    print(f"Dashboard screenshot saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
