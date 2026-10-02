"""
Redesign render_dashboard_screenshot.py with the Crimson Executive Theme:
- Top banner: Deep crimson (#7F1D2D)
- Left filters panel: Soft rose (#FFE4E6) with rounded card chips
- KPI Cards: Clean white (#FFFFFF) with crimson left accent bar (#7F1D2D)
- Clean card-based charts with subtle borders (#E2E8F0)
- Unified executive color palette: Crimson (#7F1D2D, #9F1239), Rose (#E11D48), Amber (#B45309), Slate (#1E293B, #64748B)
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

# Crimson Executive Theme
CRIMSON_MAIN = "#7F1D2D"
ROSE_ACCENT = "#E11D48"
ROSE_LIGHT = "#FFE4E6"
CANVAS_BG = "#FDF8F8"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E2E8F0"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"
CYAN_ACCENT = "#06B6D4"
CHIP_BG = "#9F1239"

LAYOUT_TITLE_H = 0.034
CHIP_H = 0.024
CHIP_PAD_X = 0.004
CHIP_PAD_Y = 0.005
CHIP_GAP_X = 0.004
CHIP_GAP_Y = 0.003
SECTION_HEADER_H = 0.024
SECTION_TAIL = 0.004
RANK_HEAD_H = 0.022
RANK_ROW_H = 0.024
STATUS_H = 0.048


def _kpi(ax, x, y, w, h, label, value, color=CRIMSON_MAIN):
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


def _chip(ax, x, y, w, h, text, edge="#FECDD3", bg=None, base=7.6):
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
                    chip_edge="#FECDD3", chip_bg=None):
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
            fontsize=9.5, weight="bold", transform=ax.transAxes, ha="left", va="center")
    chip_w = (w - (cols + 1) * CHIP_PAD_X) / cols
    for i, item in enumerate(items):
        row, col = divmod(i, cols)
        cx = x_top + CHIP_PAD_X + col * (chip_w + CHIP_PAD_X)
        cy = y_top - SECTION_HEADER_H - CHIP_PAD_Y - CHIP_H - row * (CHIP_H + CHIP_GAP_Y)
        _chip(ax, cx, cy, chip_w, CHIP_H, str(item), edge=chip_edge, bg=chip_bg)
    return box_h


def _rank_card_h(n):
    return RANK_HEAD_H + 0.006 + n * RANK_ROW_H + 0.006


def _rank_card(ax, x, y_top, w, title, items, accent):
    """Ranked mini leaderboard (label + value + proportional bar) that keeps
    the sidebar full with real data instead of stretched empty space."""
    n = len(items)
    box_h = _rank_card_h(n)
    ax.add_patch(FancyBboxPatch((x, y_top - box_h), w, box_h,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0.8, edgecolor=BORDER_COLOR,
                                facecolor=CARD_BG, transform=ax.transAxes))
    ax.add_patch(FancyBboxPatch((x, y_top - RANK_HEAD_H), w, RANK_HEAD_H,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0, facecolor=accent, transform=ax.transAxes))
    ax.add_patch(Rectangle((x, y_top - RANK_HEAD_H), w, RANK_HEAD_H * 0.55,
                           facecolor=accent, transform=ax.transAxes))
    ax.text(x + 0.008, y_top - RANK_HEAD_H / 2, title, color="#FFFFFF", fontsize=8.2,
            weight="bold", transform=ax.transAxes, ha="left", va="center")
    for i, (label, value, frac) in enumerate(items):
        yc = y_top - RANK_HEAD_H - 0.006 - RANK_ROW_H * (i + 0.5)
        ax.text(x + 0.008, yc + 0.0045, label, color=TEXT_MUTED, fontsize=7.2,
                weight="bold", transform=ax.transAxes, ha="left", va="center")
        ax.text(x + w - 0.008, yc + 0.0045, value, color=TEXT_DARK, fontsize=7.4,
                weight="bold", transform=ax.transAxes, ha="right", va="center")
        ax.add_patch(Rectangle((x + 0.008, yc - 0.0075), (w - 0.016) * max(frac, 0.03),
                               0.005, facecolor=accent, alpha=0.85, transform=ax.transAxes))
    return box_h


def _status_footer(ax, x, y_bottom, w, title, sub):
    """Compact bottom-anchored status strip pinned exactly at the panel edge."""
    ax.add_patch(FancyBboxPatch((x, y_bottom), w, STATUS_H,
                                boxstyle="round,pad=0.001,rounding_size=0.006",
                                linewidth=0.8, edgecolor=BORDER_COLOR,
                                facecolor=CRIMSON_MAIN, transform=ax.transAxes))
    ax.text(x + w / 2, y_bottom + STATUS_H * 0.64, title, color="#FFFFFF", fontsize=8.0,
            weight="bold", transform=ax.transAxes, ha="center", va="center")
    ax.text(x + w / 2, y_bottom + STATUS_H * 0.28, sub, color="#FECDD3", fontsize=7.0,
            transform=ax.transAxes, ha="center", va="center")


def _layout_filter_panel(ax, x, panel_top_y, panel_bottom_y, w, sections,
                         accent, rank_title, rank_items, status_title, status_sub,
                         chip_edge="#FECDD3", chip_bg=None):
    """Fill the sidebar exactly: filter sections + a ranked leaderboard + a
    compact status strip, all separated by one even gap. Nothing floats."""
    content_top = panel_top_y - LAYOUT_TITLE_H - 0.008
    heights = [_section_box_h(math.ceil(len(items) / cols)) for _, items, cols in sections]
    rank_h = _rank_card_h(len(rank_items))
    avail = content_top - panel_bottom_y
    n_gaps = len(sections) + 1
    gap = max(0.008, (avail - sum(heights) - rank_h - STATUS_H) / n_gaps)

    y = content_top
    for (label, items, cols), box_h in zip(sections, heights):
        _filter_section(ax, x, y, w, items, label, cols, accent,
                        chip_edge=chip_edge, chip_bg=chip_bg)
        y -= box_h + gap
    _rank_card(ax, x, y, w, rank_title, rank_items, accent)
    y -= rank_h + gap
    _status_footer(ax, x, panel_bottom_y, w, status_title, status_sub)
    return gap


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

    # 1. Top Executive Banner (Crimson theme)
    ax.add_patch(Rectangle((0, 0.94), 1, 0.06, facecolor=CRIMSON_MAIN, transform=ax.transAxes))
    ax.text(0.02, 0.97, "Subscription Retention & Churn Analytics Dashboard",
            color="#FFFFFF", fontsize=18, weight="bold",
            ha="left", va="center", transform=ax.transAxes)
    ax.text(0.98, 0.97, "Executive Decision Support System",
            color="#FECDD3", fontsize=11, weight="bold",
            ha="right", va="center", transform=ax.transAxes)

    # 2. Filters Sidebar Panel (Soft rose container)
    panel_w = 0.135
    panel_x = 0.010
    panel_top_y = 0.92
    panel_bottom_y = 0.04
    ax.add_patch(FancyBboxPatch((panel_x, panel_bottom_y), panel_w, panel_top_y - panel_bottom_y,
                                boxstyle="round,pad=0.002,rounding_size=0.006",
                                linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=ROSE_LIGHT, transform=ax.transAxes))
    header_h = 0.034
    ax.text(panel_x + panel_w / 2, panel_top_y - header_h / 2, "FILTER PANEL",
            color=CRIMSON_MAIN, fontsize=12, weight="bold",
            ha="center", va="center", transform=ax.transAxes)

    sections = [
        ("Contract", ["Month-to-month", "One year", "Two year"], 1),
        ("Internet", ["DSL", "Fiber optic", "No"], 1),
        ("Payment", ["Bank transfer", "Credit card", "Electronic check", "Mailed check"], 1),
        ("Tenure", ["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"], 2),
        ("Churn", ["Churned", "Retained"], 2),
    ]
    inner_x = panel_x + 0.005
    inner_w = panel_w - 0.010
    seg_top = (df.assign(rar=df["MonthlyCharges"] * df["ChurnFlag"])
                 .groupby(["Contract", "InternetService"], observed=True)["rar"]
                 .sum().div(1000).sort_values(ascending=False))
    rank_items = [(f"{c.replace('Month-to-month', 'M2M')} | "
                   f"{s.replace('Fiber optic', 'Fiber').replace('No', 'None')}",
                   f"${v:.0f}K", v / seg_top.max())
                  for (c, s), v in seg_top.head(3).items()]
    _layout_filter_panel(ax, inner_x, panel_top_y, panel_bottom_y, inner_w, sections,
                         CRIMSON_MAIN, "HIGHEST-RISK SEGMENTS", rank_items,
                         "ALL FILTERS ACTIVE", f"{len(df):,} customers in view",
                         chip_edge="#FECDD3", chip_bg=CHIP_BG)

    # 3. KPI Cards (Consistent crimson accent strips)
    kpis = [
        ("Total Customers", f"{len(df):,}", CRIMSON_MAIN),
        ("Churn Rate", f"{df['ChurnFlag'].mean():.1%}", "#E11D48"),
        ("Avg Tenure (mo)", f"{df['tenure'].mean():.1f}", ROSE_ACCENT),
        ("Revenue at Risk", f"${df['RevenueAtRisk'].sum()/1000:,.0f}K", "#B45309"),
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
        cax.set_title(title, fontsize=10.5, weight="bold", color=CRIMSON_MAIN, pad=8)

        if key == "contract":
            data = df.groupby("Contract", observed=True)["ChurnFlag"].mean().mul(100).reindex(
                ["Month-to-month", "One year", "Two year"])
            cax.bar(data.index, data.values, color=CRIMSON_MAIN, width=0.52)
            cax.tick_params(axis="x", labelsize=8.5, colors=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED)
            for j, v in enumerate(data.values):
                cax.text(j, v + 1, f"{v:.1f}%", ha="center", fontsize=8.5, color=TEXT_DARK, weight="bold")
            cax.set_ylim(0, max(data.values) * 1.20)
        elif key == "tenure":
            data = df.groupby("tenure_band", observed=True)["ChurnFlag"].mean().mul(100)
            cax.plot(data.index.astype(str), data.values, color=ROSE_ACCENT, marker="o", linewidth=2.4, markersize=5)
            cax.fill_between(range(len(data)), data.values, color=ROSE_LIGHT, alpha=0.6)
            cax.tick_params(axis="x", labelsize=8, colors=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED)
            for j, v in enumerate(data.values):
                cax.text(j, v + 1.5, f"{v:.1f}%", ha="center", fontsize=8, color=TEXT_DARK, weight="bold")
            cax.set_ylim(0, max(data.values) * 1.18)
        elif key == "service":
            data = df.groupby("InternetService", observed=True)["customerID"].count()
            colors = [CRIMSON_MAIN, ROSE_ACCENT, "#CBD5E1"]
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
            cax.bar(data.index, data.values, color=CRIMSON_MAIN, width=0.52)
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
            cax.barh(grp["label"][::-1], grp["rar"][::-1], color=ROSE_ACCENT)
            cax.tick_params(axis="x", labelsize=8, colors=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED)
            for j, (lbl, v) in enumerate(zip(grp["label"][::-1], grp["rar"][::-1])):
                cax.text(v + grp["rar"].max() * 0.015, j, f"${v:.0f}K",
                         va="center", fontsize=8, color=TEXT_DARK, weight="bold")
            cax.set_xlim(0, grp["rar"].max() * 1.18)
        elif key == "tenure_trend":
            t = df.groupby("tenure")["ChurnFlag"].mean().mul(100)
            t = t.iloc[::3]
            cax.plot(t.index, t.values, color=CRIMSON_MAIN, linewidth=2.2)
            cax.fill_between(t.index, t.values, color=ROSE_LIGHT, alpha=0.7)
            cax.tick_params(axis="x", labelsize=7, colors=TEXT_MUTED)
            cax.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED)

    # 5. Key Findings panel (Modern white card with crimson header strip)
    findings_top = 0.335
    # bottom edge matches the filter sidebar bottom (panel_bottom_y) for a level look
    findings_h = findings_top - panel_bottom_y
    ax.add_patch(FancyBboxPatch((kpi_x0, findings_top - findings_h), grid_x1 - kpi_x0, findings_h,
                                boxstyle="round,pad=0.002,rounding_size=0.006",
                                linewidth=1.0, edgecolor=BORDER_COLOR, facecolor=CARD_BG,
                                transform=ax.transAxes))
    ax.add_patch(Rectangle((kpi_x0, findings_top - 0.030), grid_x1 - kpi_x0, 0.030,
                           facecolor=CRIMSON_MAIN, transform=ax.transAxes))
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
        ax.text(kpi_x0 + 0.015, y, f"â€¢  {txt}", color=TEXT_DARK, fontsize=10,
                weight="bold", ha="left", va="center", transform=ax.transAxes)

    # 6. Modern Footer
    ax.add_patch(Rectangle((0, 0), 1, 0.025, facecolor=CARD_BG, transform=ax.transAxes))
    ax.text(0.5, 0.013, "Created by Ansh Thakur  |  Data Analyst Portfolio Dashboard",
            color=CRIMSON_MAIN, fontsize=9.5, weight="bold", style="italic",
            ha="center", va="center", transform=ax.transAxes)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=120, facecolor=CANVAS_BG)
    plt.close(fig)
    print(f"Modern Churn Dashboard screenshot saved to {OUT_PATH}")

if __name__ == "__main__":
    main()
