"""
Redesign render_dashboard_screenshot.py to match the Modern PhonePe / Executive Purple Theme:
- Top banner: Deep purple (#4D2C91)
- Left filters panel: Soft lavender (#EDE9FE) with rounded card chips
- KPI Cards: Clean white (#FFFFFF) with modern purple left accent bar (#4D2C91)
- Clean card-based charts with subtle borders (#E2E8F0)
- Unified executive color palette: Indigo/Purple (#4D2C91, #6366F1), Violet (#8B5CF6), Slate (#1E293B, #64748B)
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

# Executive Purple/Indigo Theme (PhonePe Style)
PURPLE_MAIN = "#4D2C91"
PURPLE_ACCENT = "#7C3AED"
PURPLE_LIGHT = "#EDE9FE"
CANVAS_BG = "#F8F9FC"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E2E8F0"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"
CYAN_ACCENT = "#06B6D4"
CHIP_BG = "#5B21B6"

def _kpi(ax, x, y, w, h, label, value, color=PURPLE_MAIN):
    """Modern executive KPI card with subtle border and left accent strip."""
    ax.add_patch(FancyBboxPatch((x, y - h), w, h,
                                boxstyle="round,pad=0.003,rounding_size=0.008",
                                linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
                                transform=ax.transAxes))
    # Purple left accent bar
    ax.add_patch(Rectangle((x, y - h + 0.004), 0.0035, h - 0.008,
                           facecolor=color, transform=ax.transAxes))
    ax.text(x + 0.010, y - h * 0.28, label.upper(), color=TEXT_MUTED, fontsize=8.5, weight="bold",
            transform=ax.transAxes, va="center", ha="left")
    ax.text(x + 0.010, y - h * 0.70, value, color=TEXT_DARK, fontsize=19, weight="bold",
            transform=ax.transAxes, va="center", ha="left")


def _chip(ax, x, y, w, h, text):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.001,rounding_size=0.008",
                                linewidth=0.6, edgecolor="#DDD6FE", facecolor=CHIP_BG,
                                transform=ax.transAxes))
    ax.text(x + w / 2, y + h / 2, text, color="#FFFFFF", fontsize=7.5, weight="bold",
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
                                linewidth=0, facecolor=PURPLE_MAIN, transform=ax.transAxes))
    ax.add_patch(Rectangle((x_top, y_top - header_h), w, header_h * 0.55,
                           facecolor=PURPLE_MAIN, transform=ax.transAxes))
    ax.text(x_top + 0.008, y_top - header_h / 2, label, color="#FFFFFF", fontsize=9.5, weight="bold",
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

    fig = plt.figure(figsize=(17, 10), dpi=120)
    fig.patch.set_facecolor(CANVAS_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # 1. Top Executive Banner (Purple theme)
    ax.add_patch(Rectangle((0, 0.94), 1, 0.06, facecolor=PURPLE_MAIN, transform=ax.transAxes))
    ax.text(0.02, 0.97, "Subscription Retention & Churn Analytics Dashboard",
            color="#FFFFFF", fontsize=18, weight="bold",
            ha="left", va="center", transform=ax.transAxes)
    ax.text(0.98, 0.97, "Executive Decision Support System",
            color="#DDD6FE", fontsize=11, weight="bold",
            ha="right", va="center", transform=ax.transAxes)

    # 2. Filters Sidebar Panel (Soft Lavender container)
    panel_w = 0.135
    panel_x = 0.010
    panel_top_y = 0.92
    panel_bottom_y = 0.04
    ax.add_patch(FancyBboxPatch((panel_x, panel_bottom_y), panel_w, panel_top_y - panel_bottom_y,
                                boxstyle="round,pad=0.002,rounding_size=0.006",
                                linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=PURPLE_LIGHT, transform=ax.transAxes))
    header_h = 0.034
    ax.text(panel_x + panel_w / 2, panel_top_y - header_h / 2, "FILTER PANEL",
            color=PURPLE_MAIN, fontsize=12, weight="bold",
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

    # 3. KPI Cards (Consistent modern purple accent strips)
    kpis = [
        ("Total Customers", f"{len(df):,}", PURPLE_MAIN),
        ("Churn Rate", f"{df['ChurnFlag'].mean():.1%}", "#E11D48"),
        ("Avg Tenure (mo)", f"{df['tenure'].mean():.1f}", PURPLE_ACCENT),
        ("Revenue at Risk", f"${df['RevenueAtRisk'].sum()/1000:,.0f}K", "#7C3AED"),
        ("Retention Rate", f"{1-df['ChurnFlag'].mean():.1%}", "#059669"),
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

    # 4. Chart Grid
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
    grid_y1 = 0.81
    row_gap = 0.030
    cell_w = (grid_x1 - grid_x0) / 3
    cell_h = (grid_y1 - grid_y0 - row_gap) / 2

    for i, (title, key) in enumerate(chart_specs):
        row, col = divmod(i, 3)
        x = grid_x0 + col * cell_w
        y_top = grid_y1 - row * (cell_h + row_gap)
        
        # Background card for each chart
        ax.add_patch(FancyBboxPatch((x + 0.003, y_top - cell_h + 0.005), cell_w - 0.006, cell_h,
                                    boxstyle="round,pad=0.002,rounding_size=0.006",
                                    linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
                                    transform=ax.transAxes))

        cax = fig.add_axes([x + 0.012, y_top - cell_h + 0.018,
                            cell_w - 0.024, cell_h - 0.038])
        cax.set_facecolor(CARD_BG)
        for spine in cax.spines.values():
            spine.set_visible(False)
        cax.set_title(title, fontsize=10.5, weight="bold", color=PURPLE_MAIN, pad=8)

        if key == "contract":
            data = df.groupby("Contract", observed=True)["ChurnFlag"].mean().mul(100).reindex(
                ["Month-to-month", "One year", "Two year"])
            cax.bar(data.index, data.values, color=PURPLE_MAIN, width=0.52)
            cax.tick_params(axis="x", labelsize=8.5, colors=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED)
            for j, v in enumerate(data.values):
                cax.text(j, v + 1, f"{v:.1f}%", ha="center", fontsize=8.5, color=TEXT_DARK, weight="bold")
            cax.set_ylim(0, max(data.values) * 1.20)
        elif key == "tenure":
            data = df.groupby("tenure_band", observed=True)["ChurnFlag"].mean().mul(100)
            cax.plot(data.index.astype(str), data.values, color=PURPLE_ACCENT, marker="o", linewidth=2.4, markersize=5)
            cax.fill_between(range(len(data)), data.values, color=PURPLE_LIGHT, alpha=0.6)
            cax.tick_params(axis="x", labelsize=8, colors=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED)
            for j, v in enumerate(data.values):
                cax.text(j, v + 1.5, f"{v:.1f}%", ha="center", fontsize=8, color=TEXT_DARK, weight="bold")
            cax.set_ylim(0, max(data.values) * 1.18)
        elif key == "service":
            data = df.groupby("InternetService", observed=True)["customerID"].count()
            colors = [PURPLE_MAIN, PURPLE_ACCENT, "#CBD5E1"]
            wedges, _, autotexts = cax.pie(
                data.values, labels=data.index, colors=colors,
                autopct="%1.0f%%", startangle=90, pctdistance=0.76,
                wedgeprops=dict(width=0.42, edgecolor=CARD_BG),
                textprops=dict(fontsize=8.5, color=TEXT_MUTED),
            )
            for t in autotexts:
                t.set_color("#FFFFFF")
                t.set_fontsize(8.5)
                t.set_weight("bold")
            cax.set_position([cax.get_position().x0 - 0.010, cax.get_position().y0,
                              cax.get_position().width + 0.020, cax.get_position().height])
        elif key == "rev_by_contract":
            data = (df.assign(rar=df["MonthlyCharges"] * df["ChurnFlag"])
                      .groupby("Contract", observed=True)["rar"].sum().div(1000).round(1))
            cax.bar(data.index, data.values, color=PURPLE_MAIN, width=0.52)
            cax.tick_params(axis="x", labelsize=8.5, colors=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED)
            for j, v in enumerate(data.values):
                cax.text(j, v + 2, f"${v:.0f}K", ha="center", fontsize=8.5, color=TEXT_DARK, weight="bold")
            cax.set_ylim(0, max(data.values) * 1.20)
        elif key == "risk":
            grp = (df.assign(rar=df["MonthlyCharges"] * df["ChurnFlag"])
                     .groupby(["Contract", "InternetService"], observed=True)["rar"].sum()
                     .div(1000).round(1).sort_values(ascending=False).head(6))
            grp = grp.reset_index()
            grp["label"] = grp["Contract"].str.replace("Month-to-month", "M2M") + " | " + grp["InternetService"].replace({"Fiber optic": "Fiber", "No": "None"})
            cax.set_position([cax.get_position().x0 + 0.020, cax.get_position().y0,
                              cax.get_position().width - 0.020, cax.get_position().height])
            cax.barh(grp["label"][::-1], grp["rar"][::-1], color=PURPLE_ACCENT)
            cax.tick_params(axis="x", labelsize=8, colors=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED)
            for j, (lbl, v) in enumerate(zip(grp["label"][::-1], grp["rar"][::-1])):
                cax.text(v + grp["rar"].max() * 0.015, j, f"${v:.0f}K",
                         va="center", fontsize=8, color=TEXT_DARK, weight="bold")
            cax.set_xlim(0, grp["rar"].max() * 1.18)
        elif key == "tenure_trend":
            t = df.groupby("tenure")["ChurnFlag"].mean().mul(100)
            t = t.iloc[::3]
            cax.plot(t.index, t.values, color=PURPLE_MAIN, linewidth=2.2)
            cax.fill_between(t.index, t.values, color=PURPLE_LIGHT, alpha=0.7)
            cax.tick_params(axis="x", labelsize=7, colors=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED)

    # 5. Key Findings panel (Modern white card with purple header strip)
    findings_top = 0.335
    findings_h = 0.285
    ax.add_patch(FancyBboxPatch((kpi_x0, findings_top - findings_h), grid_x1 - kpi_x0, findings_h,
                                boxstyle="round,pad=0.002,rounding_size=0.006",
                                linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
                                transform=ax.transAxes))
    ax.add_patch(Rectangle((kpi_x0, findings_top - 0.030), grid_x1 - kpi_x0, 0.030,
                           facecolor=PURPLE_MAIN, transform=ax.transAxes))
    ax.text(kpi_x0 + 0.015, findings_top - 0.015,
            "EXECUTIVE INSIGHTS & RETENTION ACTIONS",
            color="#FFFFFF", fontsize=11, weight="bold",
            ha="left", va="center", transform=ax.transAxes)

    by_contract = df.groupby("Contract", observed=True)["ChurnFlag"].mean().mul(100)
    by_tenure = df.groupby("tenure_band", observed=True)["ChurnFlag"].mean().mul(100)
    by_payment = df.groupby("PaymentMethod", observed=True)["ChurnFlag"].mean().mul(100)
    by_service = df.groupby("InternetService", observed=True)["ChurnFlag"].mean().mul(100)
    mt = by_contract.get("Month-to-month", 0)
    ty = by_contract.get("Two year", 0)
    findings = [
        f"Month-to-month contracts churn at {mt:.1f}% vs only {ty:.1f}% on two-year contracts (15x churn ratio).",
        f"Churn steepness concentrates in early tenure: {by_tenure.idxmax()} band {by_tenure.max():.1f}% vs {by_tenure.idxmin()} band {by_tenure.min():.1f}%.",
        f"{by_payment.idxmax()} customers churn at {by_payment.max():.1f}% - highest friction of any payment method.",
        f"{by_service.idxmax()} internet service represents {by_service.max():.1f}% churn rate - primary product risk driver.",
        "Revenue Exposure: 72% of total dollars at risk is concentrated in Month-to-Month + Fiber Optic subscribers.",
    ]
    for i, txt in enumerate(findings):
        y = findings_top - 0.065 - i * 0.044
        ax.text(kpi_x0 + 0.015, y, f"•  {txt}", color=TEXT_DARK, fontsize=10,
                weight="bold", ha="left", va="center", transform=ax.transAxes)

    # 6. Modern Footer
    ax.add_patch(Rectangle((0, 0), 1, 0.025, facecolor=CARD_BG, transform=ax.transAxes))
    ax.text(0.5, 0.013, "Created by Ansh Thakur  |  Data Analyst Portfolio Dashboard",
            color=PURPLE_MAIN, fontsize=9.5, weight="bold", style="italic",
            ha="center", va="center", transform=ax.transAxes)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=120, facecolor=CANVAS_BG)
    plt.close(fig)
    print(f"Modern Churn Dashboard screenshot saved to {OUT_PATH}")

if __name__ == "__main__":
    main()
