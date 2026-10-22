"""Render a static HTML preview of the cockpit for visual QA.

Builds the exact same markup and Plotly figures the Streamlit app produces,
but writes them to a standalone ``.html`` file so the design can be
screenshotted (or opened in a browser) without running the app.

Usage:
    python scripts/preview_cockpit_html.py [output.html]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_settings  # noqa: E402
from src.data_loader import load_processed  # noqa: E402
from src.reconciliation.engine import aggregate_weekly  # noqa: E402
from src.reconciliation.metrics import compute_headline_kpis  # noqa: E402
from src.reconciliation.variance_analyzer import add_wow_variance  # noqa: E402
from streamlit_app.common import format_inr  # noqa: E402
from streamlit_app.components.charts import (  # noqa: E402
    bucket_legend_rows,
    cockpit_area_trend,
    cockpit_bucket_donut,
    cockpit_gauge,
    cockpit_mini_area,
    cockpit_volume_bars,
)
from streamlit_app.components.cockpit import (  # noqa: E402
    cta_button,
    hero_card,
    legend_row,
    nav_brand,
    nav_item,
    nav_section,
    panel_close,
    panel_open,
    profile_block,
    stat_pill,
)
from streamlit_app.theme import CSS  # noqa: E402


def _fig_html(fig, height: int) -> str:
    """Return an embeddable ``<div>`` for a Plotly figure.

    Args:
        fig: A Plotly figure.
        height: Rendered height in pixels.

    Returns:
        HTML fragment embedding the figure.
    """
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
        default_height=f"{height}px",
    )


def _plotly_bundle() -> str:
    """Return the local Plotly.js bundle as an inline ``<script>`` tag.

    The bundle ships with the ``plotly`` package, so the preview renders
    offline (no CDN round-trip) and screenshots deterministically.

    Returns:
        HTML string containing the inlined Plotly runtime.
    """
    import os

    import plotly

    bundle = os.path.join(
        os.path.dirname(plotly.__file__), "package_data", "plotly.min.js"
    )
    with open(bundle, encoding="utf-8") as fh:
        return f"<script>{fh.read()}</script>"


def _bucket_legend(df) -> str:
    """Build the HTML colour key for the revenue-mix donut.

    Args:
        df: Cleaned transaction frame.

    Returns:
        HTML string with one legend row per financial bucket.
    """
    rows = bucket_legend_rows(df)
    total = sum(amount for _, _, amount in rows) or 1.0
    return "".join(
        legend_row(color, label, f"₹{amount/1e7:,.2f} Cr",
                   f"{amount / total * 100:.1f}%")
        for label, color, amount in rows
    )


def _build_parts(settings, df, weekly, kpi) -> tuple[str, str, str]:
    """Build the sidebar, hero-row and pill-row markup.

    Args:
        settings: Loaded settings.
        df: Cleaned transaction frame.
        weekly: Weekly KPI frame.
        kpi: Headline KPIs.

    Returns:
        Tuple of (sidebar_html, heroes_html, pills_html).
    """
    target = settings.thresholds.settled_clearance_critical_below
    nav = "".join([
        nav_brand("Revenue", "Cockpit"),
        nav_section("Profile"),
        nav_item("Overview", "◈", active=True),
        nav_section("Workspace"),
        nav_item("Executive Summary", "▤"),
        nav_item("Weekly Trends", "◹"),
        nav_item("Leakage Analysis", "◈"),
        nav_item("Exception Audit", "▣"),
        nav_section("Channels"),
        nav_item("Fiscal Week", "◷"),
        nav_item("Category", "◰"),
        nav_item("Fulfilment", "◱"),
        nav_item("Ship State", "◲"),
        profile_block("Ansh Thakur", "Revenue Analytics", "AT"),
        cta_button("Export Report"),
    ])

    heroes = "".join([
        hero_card(
            "Total Revenue Invoiced", format_inr(kpi.gross_revenue),
            f"{kpi.total_lines:,} transaction lines audited",
            foot=f"Across {kpi.weeks_active} fiscal weeks · "
                 f"{kpi.full_weeks} full / {kpi.partial_weeks} partial",
        ),
        hero_card(
            "Net Realized Cash", format_inr(kpi.net_realized),
            f"{kpi.settled_clearance_rate:.1f}% of the settled base retained",
            foot=f"Settlement lag {kpi.settlement_lag_rate:.1f}% of gross · "
                 f"₹{(kpi.in_transit_value + kpi.pending_value)/1e7:,.2f} Cr in flight",
            alt=True,
        ),
    ])

    pills = "".join([
        stat_pill("L", "Total Leakage", format_inr(kpi.total_leakage), "neg"),
        stat_pill("C", "Cancelled Orders", f"{kpi.cancelled_orders:,}", "neg"),
        stat_pill("S", "Settled Clearance",
                  f"{kpi.settled_clearance_rate:.1f}%",
                  "pos" if kpi.settled_clearance_rate >= target else "warn"),
    ])
    return nav, heroes, pills


def build_preview() -> str:
    """Build the full static cockpit preview HTML.

    Returns:
        The HTML document as a string.
    """
    settings = load_settings()
    df = load_processed(settings)
    weekly = add_wow_variance(aggregate_weekly(
        df, min_days_for_full_week=settings.thresholds.min_days_for_full_week))
    kpi = compute_headline_kpis(df, weekly)
    target = settings.thresholds.settled_clearance_critical_below
    nav, heroes, pills = _build_parts(settings, df, weekly, kpi)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Revenue Cockpit — Preview</title>
{_plotly_bundle()}
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#070B14; display:flex;
          font-family:"Segoe UI", Inter, sans-serif; }}
  .sidebar {{ width:264px; flex:0 0 264px; background:#0B1220;
              border-right:1px solid #1E2C45; padding:16px 14px; }}
  .main {{ flex:1 1 auto; padding:18px 20px; min-width:0; }}
  .row {{ display:flex; gap:16px; align-items:flex-start; }}
  .row > * {{ min-width:0; }}
  .hero {{ flex:1 1 0; display:flex; gap:16px; }}
  .hero > * {{ flex:1 1 0; }}
  .pills {{ flex:0 0 250px; }}
  .mainpanel {{ flex:1 1 0; }}
  .rail {{ flex:0 0 340px; }}
  .half {{ flex:1 1 0; }}
  .panel {{ overflow:hidden; }}
  .banner {{ background:#0B1B24; border:1px solid #22D3EE; border-radius:12px;
             padding:12px 16px; text-align:center; margin:16px 0; }}
  .sb-title {{ color:#22D3EE; font-weight:800; letter-spacing:.06em; font-size:13px; }}
  .sb-sub {{ color:#8FA3BF; font-size:12px; margin-top:3px; }}
  .cap {{ color:#8FA3BF; font-size:11px; margin-top:10px; }}
  .figbox {{ min-width:0; overflow:hidden; }}
  .figbox .js-plotly-plot {{ width:100% !important; max-width:100%; }}
</style>
{CSS}
</head><body>
<div class="sidebar">{nav}</div>
<div class="main">
  <div class="row">
    <div class="hero">{heroes}</div>
    <div class="pills">{pills}</div>
  </div>  <div class="banner">
    <div class="sb-title">AUDIT STATUS: RECONCILED</div>
    <div class="sb-sub">{kpi.total_lines:,} transaction lines ·
      {kpi.unique_orders:,} unique orders · {kpi.weeks_active} fiscal weeks</div>
  </div>
  <div class="row">
    <div class="mainpanel">
      {panel_open("Revenue Trend — Gross Invoiced vs Net Realized",
                  "Weekly fiscal calendar · W13–W26 FY22")}
      <div class="figbox">{_fig_html(cockpit_area_trend(weekly), 380)}</div>
      {panel_close()}
    </div>
    <div class="rail">
      {panel_open("Net Realized Velocity", "Rolling weekly shape")}
      <div class="figbox">{_fig_html(cockpit_mini_area(weekly), 200)}</div>
      {panel_close()}
      {panel_open("Transaction Volume / Week", "Line count per fiscal week")}
      <div class="figbox">{_fig_html(cockpit_volume_bars(weekly), 300)}</div>
      {panel_close()}
    </div>
  </div>
  <div class="row" style="margin-top:16px">
    <div class="half">
      {panel_open("Revenue by Financial Bucket", "Where every rupee landed")}
      <div class="row">
        <div style="flex:1 1 0"><div class="figbox">{_fig_html(cockpit_bucket_donut(df), 300)}</div></div>
        <div style="flex:1 1 0">{_bucket_legend(df)}</div>
      </div>
      {panel_close()}
    </div>
    <div class="half">
      {panel_open("Settlement Health", f"Audit target {target:.0f}% of settled base")}
      {_fig_html(cockpit_gauge(kpi.settled_clearance_rate,
                               "of settled base retained"), 300)}
      {panel_close()}
    </div>
  </div>
  <div class="cap">Source: Amazon Sale Report (Kaggle CC0) · W13–W26 FY22</div>
</div>
</body></html>"""


def main() -> None:
    """Write the preview HTML to disk."""
    out = (Path(sys.argv[1]) if len(sys.argv) > 1
           else ROOT / "reports" / "cockpit_preview.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_preview(), encoding="utf-8")
    print(f"Preview written -> {out}")


if __name__ == "__main__":
    main()
