"""
Render a PNG screenshot of the Subscription Retention & Churn Dashboard.
Restyled to match the Supply Chain executive layout:
  - KPI cards: white cards with colored left accent bars
  - Consistent blue/teal palette across all charts
  - Compact Key Findings panel with bold navy text
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

NAVY = "#1F3864"
NAVY_DARK = "#0F2A4D"
BLUE = "#2E5496"
TEAL = "#00A6A6"
BG = "#E9EDF4"
WHITE = "#FFFFFF"
RED = "#B0252A"
ORANGE_DARK = "#A14E0C"
GREEN = "#3E7C2A"
PURPLE = "#7030A0"
PANEL_BLUE = "#1F4E79"
TEXT = "#1F2937"
LIGHT_BLUE = "#DDEBF7"
PANEL_BG = "#FFFFFF"
GRAY_SLICE = "#8496B0"


def _kpi(ax, x, y, w, h, label, value, color):
    """White KPI card with a colored left accent bar (supply-chain style)."""
    ax.add_patch(FancyBboxPatch((x, y - h), w, h,
                                boxstyle="round,pad=0.003,rounding_size=0.008",
                                linewidth=0.8, edgecolor="#A8B0C0", facecolor=WHITE,
                                transform=ax.transAxes))
    ax.add_patch(Rectangle((x, y - h + 0.004), 0.0035, h - 0.008,
                           facecolor=color, transform=ax.transAxes))
    ax.text(x + 0.008, y - h * 0.28, label, color=NAVY, fontsize=10, weight="bold",
            transform=ax.transAxes, va="center", ha="left")
    ax.text(x + 0.008, y - h * 0.70, value, color=NAVY_DARK, fontsize=19, weight="bold",
            transform=ax.transAxes, va="center", ha="left")


def _chip(ax, x, y, w, h, text):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.001,rounding_size=0.008",
                                linewidth=0.6, edgecolor="#4A6FA8", facecolor=PANEL_BLUE,
                                transform=ax.transAxes))
    ax.text(x + w / 2, y + h / 2, text, color=WHITE, fontsize=7.5, weight="bold",
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
                                linewidth=0.6, edgecolor="#C0C8D8",
                                facecolor=WHITE, transform=ax.transAxes))
    ax.add_patch(FancyBboxPatch((x_top, y_top - header_h), w, header_h,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0, facecolor=NAVY_DARK, transform=ax.transAxes))
    ax.add_patch(Rectangle((x_top, y_top - header_h), w, header_h * 0.55,
                           facecolor=NAVY_DARK, transform=ax.transAxes))
    ax.text(x_top + 0.008, y_top - header_h / 2, label, color=WHITE, fontsize=9.5, weight="bold",
            transform=ax.transAxes, ha="left", va="center")
    chip_w = (w - 3 * chip_pad_x) / 2
    for i, item in enumerate(items):
        row = i // 2
        col = i % 2
        cx = x_top + chip_pad_x + col * (chip_w + chip_pad_x)
        cy = y_top - header_h - chip_pad_y - chip_h - row * (chip_h + chip_gap_y)
        _chip(ax, cx, cy, chip_w, chip_h, item)
    return box_h + 0.016


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
    ax.text(0.5, 0.97, "Subscription Retention & Churn Analytics  Dashboard",
            color=WHITE, fontsize=22, weight="bold",
            ha="center", va="center", transform=ax.transAxes)

    # Filters panel
    panel_w = 0.135
    panel_x = 0.010
    panel_top_y = 0.91
    panel_bottom_y = 0.32
    ax.add_patch(FancyBboxPatch((panel_x, panel_bottom_y), panel_w, panel_top_y - panel_bottom_y,
                                boxstyle="round,pad=0.002,rounding_size=0.006",
                                linewidth=0, facecolor=NAVY_DARK, transform=ax.transAxes))
    header_h = 0.034
    ax.text(panel_x + panel_w / 2, panel_top_y - header_h / 2, "Filters",
            color=WHITE, fontsize=14, weight="bold",
            ha="center", va="center", transform=ax.transAxes)

    sections = [
        ("Contract", ["Month-to-month", "One year", "Two year"]),
        ("Internet", ["DSL", "Fiber optic", "No"]),
        ("Payment", ["Bank transfer", "Credit card", "Electronic check", "Mailed check"]),
        ("Tenure", ["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"]),
        ("Churn", ["Churned", "Retained"]),
    ]
    y_cursor = panel_top_y - header_h - 0.010
    inner_x = panel_x + 0.005
    inner_w = panel_w - 0.010
    for label, items in sections:
        used = _filter_section(ax, inner_x, y_cursor, inner_w, items, label)
        y_cursor -= used + 0.002

    # KPI cards - distinct accent colors, supply-chain style
    kpis = [
        ("Total Customers", f"{len(df):,}", GREEN),
        ("Churn Rate", f"{df['ChurnFlag'].mean():.1%}", RED),
        ("Avg Tenure (mo)", f"{df['tenure'].mean():.1f}", ORANGE_DARK),
        ("Revenue at Risk", f"${df['RevenueAtRisk'].sum()/1000:,.0f}K", PURPLE),
        ("Retention Rate", f"{1-df['ChurnFlag'].mean():.1%}", TEAL),
    ]
    kpi_x0 = panel_x + panel_w + 0.045
    kpi_total_w = 1 - kpi_x0 - 0.012
    kpi_gap = 0.010
    kpi_w = (kpi_total_w - 4 * kpi_gap) / 5
    kpi_h = 0.10
    kpi_top = 0.92
    for i, (label, value, color) in enumerate(kpis):
        x = kpi_x0 + i * (kpi_w + kpi_gap)
        _kpi(ax, x, kpi_top, kpi_w, kpi_h, label, value, color)

    # Chart grid
    chart_specs = [
        ("Churn Rate by Contract", "contract"),
        ("Churn Rate by Tenure Band", "tenure"),
        ("Customer Mix by Internet Service", "service"),
        ("Top Revenue-at-Risk Segments ($K)", "risk"),
        ("Revenue at Risk by Contract", "rev_by_contract"),
        ("Churn Rate by Tenure (months)", "tenure_trend"),
    ]
    grid_x0 = kpi_x0
    grid_x1 = 1 - 0.012
    grid_y0 = 0.36
    grid_y1 = 0.80
    row_gap = 0.030
    cell_w = (grid_x1 - grid_x0) / 3
    cell_h = (grid_y1 - grid_y0 - row_gap) / 2

    for i, (title, key) in enumerate(chart_specs):
        row, col = divmod(i, 3)
        x = grid_x0 + col * cell_w
        y_top = grid_y1 - row * (cell_h + row_gap)
        cax = fig.add_axes([x + 0.004, y_top - cell_h + 0.012,
                            cell_w - 0.014, cell_h - 0.030])
        cax.set_facecolor(PANEL_BG)
        for spine in cax.spines.values():
            spine.set_color("#B8C0D0")
            spine.set_linewidth(0.8)
        cax.set_title(title, fontsize=10.5, weight="bold", color=NAVY_DARK, pad=8)

        if key == "contract":
            data = df.groupby("Contract", observed=True)["ChurnFlag"].mean().mul(100).reindex(
                ["Month-to-month", "One year", "Two year"])
            cax.bar(data.index, data.values, color=BLUE, width=0.55)
            cax.tick_params(axis="x", labelsize=8.5, rotation=0)
            cax.tick_params(axis="y", labelsize=8)
            for s in cax.spines.values():
                s.set_visible(False)
            for j, v in enumerate(data.values):
                cax.text(j, v + 1, f"{v:.1f}%", ha="center", fontsize=8.5, color=NAVY, weight="bold")
            cax.set_ylim(0, max(data.values) * 1.20)
        elif key == "tenure":
            data = df.groupby("tenure_band", observed=True)["ChurnFlag"].mean().mul(100)
            cax.plot(data.index.astype(str), data.values, color=BLUE, marker="o", linewidth=2.2, markersize=5)
            cax.fill_between(range(len(data)), data.values, color=BLUE, alpha=0.15)
            cax.tick_params(axis="x", labelsize=8)
            cax.tick_params(axis="y", labelsize=8)
            for j, v in enumerate(data.values):
                cax.text(j, v + 1.5, f"{v:.1f}%", ha="center", fontsize=8, color=NAVY, weight="bold")
            cax.set_ylim(0, max(data.values) * 1.18)
            for s in cax.spines.values():
                s.set_visible(False)
        elif key == "service":
            data = df.groupby("InternetService", observed=True)["customerID"].count()
            colors = [BLUE, TEAL, GRAY_SLICE]
            wedges, _, autotexts = cax.pie(
                data.values, labels=data.index, colors=colors,
                autopct="%1.0f%%", startangle=90, pctdistance=0.76,
                wedgeprops=dict(width=0.42, edgecolor=WHITE),
                textprops=dict(fontsize=8.5, color=TEXT),
            )
            for t in autotexts:
                t.set_color(WHITE)
                t.set_fontsize(8.5)
                t.set_weight("bold")
            cax.set_position([cax.get_position().x0 - 0.010, cax.get_position().y0,
                              cax.get_position().width + 0.020, cax.get_position().height])
        elif key == "rev_by_contract":
            data = (df.assign(rar=df["MonthlyCharges"] * df["ChurnFlag"])
                      .groupby("Contract", observed=True)["rar"].sum().div(1000).round(1))
            cax.bar(data.index, data.values, color=BLUE, width=0.55)
            cax.tick_params(axis="x", labelsize=8.5, rotation=0)
            cax.tick_params(axis="y", labelsize=8)
            for s in cax.spines.values():
                s.set_visible(False)
            for j, v in enumerate(data.values):
                cax.text(j, v + 2, f"${v:.0f}K", ha="center", fontsize=8.5, color=NAVY, weight="bold")
            cax.set_ylim(0, max(data.values) * 1.20)
        elif key == "risk":
            grp = (df.assign(rar=df["MonthlyCharges"] * df["ChurnFlag"])
                     .groupby(["Contract", "InternetService"], observed=True)["rar"].sum()
                     .div(1000).round(1).sort_values(ascending=False).head(6))
            grp = grp.reset_index()
            grp["label"] = grp["Contract"].str.replace("Month-to-month", "M2M") + " | " + grp["InternetService"].replace({"Fiber optic": "Fiber", "No": "None"})
            cax.set_position([cax.get_position().x0 + 0.020, cax.get_position().y0,
                              cax.get_position().width - 0.020, cax.get_position().height])
            cax.barh(grp["label"][::-1], grp["rar"][::-1], color=GREEN)
            cax.tick_params(axis="x", labelsize=8)
            cax.tick_params(axis="y", labelsize=8)
            for s in cax.spines.values():
                s.set_visible(False)
            for j, (lbl, v) in enumerate(zip(grp["label"][::-1], grp["rar"][::-1])):
                cax.text(v + grp["rar"].max() * 0.015, j, f"${v:.0f}K",
                         va="center", fontsize=8, color=NAVY, weight="bold")
            cax.set_xlim(0, grp["rar"].max() * 1.18)
        elif key == "tenure_trend":
            t = df.groupby("tenure")["ChurnFlag"].mean().mul(100)
            t = t.iloc[::3]
            cax.plot(t.index, t.values, color=NAVY, linewidth=2.2)
            cax.fill_between(t.index, t.values, color=BLUE, alpha=0.18)
            cax.tick_params(axis="x", labelsize=7)
            cax.tick_params(axis="y", labelsize=8)
            for s in cax.spines.values():
                s.set_visible(False)

    # Key Findings panel - fills the lower band, bold navy text
    findings_top = 0.335
    findings_h = 0.255
    ax.add_patch(FancyBboxPatch((kpi_x0, findings_top - findings_h), grid_x1 - kpi_x0, findings_h,
                                boxstyle="round,pad=0.002,rounding_size=0.006",
                                linewidth=0.6, edgecolor="#C0C8D8", facecolor=WHITE,
                                transform=ax.transAxes))
    ax.add_patch(Rectangle((kpi_x0, findings_top - 0.030), grid_x1 - kpi_x0, 0.030,
                           facecolor=NAVY, transform=ax.transAxes))
    ax.text(kpi_x0 + (grid_x1 - kpi_x0) / 2, findings_top - 0.015,
            "Key Findings  |  Executive Insights",
            color=WHITE, fontsize=11.5, weight="bold",
            ha="center", va="center", transform=ax.transAxes)

    by_contract = df.groupby("Contract", observed=True)["ChurnFlag"].mean().mul(100)
    by_tenure = df.groupby("tenure_band", observed=True)["ChurnFlag"].mean().mul(100)
    by_payment = df.groupby("PaymentMethod", observed=True)["ChurnFlag"].mean().mul(100)
    by_service = df.groupby("InternetService", observed=True)["ChurnFlag"].mean().mul(100)
    mt = by_contract.get("Month-to-month", 0)
    ty = by_contract.get("Two year", 0)
    findings = [
        f"Month-to-month contracts churn at {mt:.1f}% vs only {ty:.1f}% on two-year contracts.",
        f"Churn falls with tenure: {by_tenure.idxmax()} band {by_tenure.max():.1f}% -> {by_tenure.idxmin()} band {by_tenure.min():.1f}%.",
        f"{by_payment.idxmax()} customers churn at {by_payment.max():.1f}% - highest of any payment method.",
        f"{by_service.idxmax()} internet service shows {by_service.max():.1f}% churn - dominant service risk.",
        "Top revenue-at-risk segment: Month-to-month + Fiber optic - protect by contract conversion.",
    ]
    for i, txt in enumerate(findings):
        y = findings_top - 0.062 - i * 0.040
        ax.text(kpi_x0 + 0.015, y, f"-  {txt}", color=NAVY_DARK, fontsize=10,
                weight="bold", ha="left", va="center", transform=ax.transAxes)

    # Footer
    ax.add_patch(Rectangle((0, 0), 1, 0.025, facecolor=WHITE, transform=ax.transAxes))
    ax.text(0.5, 0.013, "Created by Ansh Thakur  |  Data Analyst Portfolio Dashboard",
            color=NAVY_DARK, fontsize=10, weight="bold", style="italic",
            ha="center", va="center", transform=ax.transAxes)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=100, facecolor=BG)
    plt.close(fig)
    print(f"Dashboard screenshot saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
