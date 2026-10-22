"""Page 1 — Executive Summary: KPI cards + Gross-to-Net waterfall + anomalies."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402
from streamlit_app.common import (  # noqa: E402
    apply_filters,
    filtered_weekly,
    format_inr,
    headline_kpis,
    inject_theme,
    kpi_card,
    kpi_row,
    load_all,
    render_global_sidebar,
    section_title,
)
from streamlit_app.components.charts import (  # noqa: E402
    bucket_mix_donut,
    settled_clearance_vs_target,
    waterfall_gross_net,
    weekly_combo,
)
from streamlit_app.components.cockpit import panel  # noqa: E402

st.set_page_config(page_title="Executive Summary", layout="wide",
                   initial_sidebar_state="expanded")
inject_theme()

with st.spinner("Loading reconciliation data ..."):
    df, weekly, anomalies, settings = load_all()

render_global_sidebar(active_key="executive", df=df, weekly=weekly)

filters = st.session_state.get("filters", {})
fdf = apply_filters(
    df,
    filters.get("weeks", []),
    filters.get("categories", []),
    filters.get("fulfilments", []),
    filters.get("states", []),
)
fweekly = filtered_weekly(weekly, fdf)
kpi = headline_kpis(fdf, fweekly)

st.markdown("### 📊 Executive Summary")
st.caption(
    "Every figure below respects the Channels filters in the sidebar "
    "(applied on the dashboard home page)."
)

kpi_row(
    [
        kpi_card("Gross Invoiced", format_inr(kpi.gross_revenue),
                 f"{kpi.total_lines:,} lines · {kpi.unique_orders:,} orders"),
        kpi_card("Net Realized", format_inr(kpi.net_realized),
                 f"{kpi.settled_clearance_rate:.1f}% of settled base"),
        kpi_card("Total Leakage", format_inr(kpi.total_leakage),
                 f"₹{kpi.cancellation_leakage/1e5:,.1f}L cancel · "
                 f"₹{kpi.return_leakage/1e5:,.1f}L return"),
        kpi_card("Settled Clearance", f"{kpi.settled_clearance_rate:.1f}%",
                 f"Target {settings.thresholds.settled_clearance_critical_below:.0f}%",
                 delta=("▲ " if kpi.settled_clearance_rate >= settings.thresholds.settled_clearance_critical_below else "▼ ")
                 + f"{kpi.settled_clearance_rate:.1f}%",
                 delta_up=kpi.settled_clearance_rate >= settings.thresholds.settled_clearance_critical_below),
        kpi_card("Settlement Lag", f"{kpi.settlement_lag_rate:.1f}%",
                 f"₹{(kpi.in_transit_value + kpi.pending_value)/1e7:,.2f} Cr In-Transit / Pending"),
        kpi_card("Avg Order Value", f"₹{kpi.avg_order_value:,.2f}",
                 f"{kpi.weeks_active} weeks ({kpi.full_weeks} full)"),
    ],
    columns=3,
)

with panel("Gross → Net Waterfall", "Where the invoiced money went"):
    st.plotly_chart(waterfall_gross_net(fweekly, fdf), use_container_width=True)

c1, c2 = st.columns(2, gap="medium")
with c1:
    with panel("Weekly Trend", "Gross vs net realized cash"):
        st.plotly_chart(weekly_combo(fweekly), use_container_width=True)
with c2:
    with panel("Settled Clearance vs Target",
               f"Audit target {settings.thresholds.settled_clearance_critical_below:.0f}%"
               " of the settled base"):
        st.plotly_chart(
            settled_clearance_vs_target(
                fweekly, settings.thresholds.settled_clearance_critical_below
            ),
            use_container_width=True,
        )

with panel("Revenue by Financial Bucket", "Where every rupee landed"):
    st.plotly_chart(bucket_mix_donut(fdf), use_container_width=True)

with panel("🚨 Anomaly Log", "Weeks that breached an audit threshold"):
    if len(anomalies):
        st.dataframe(anomalies, use_container_width=True, hide_index=True)
        st.caption(
            f"CRITICAL: settled clearance < {settings.thresholds.settled_clearance_critical_below:.0f}% · "
            f"WARNING: leakage share > {settings.thresholds.leakage_warning_above:.0f}% or "
            f"cancellation > {settings.thresholds.cancellation_warning_above:.0f}% · "
            f"ALERT: WoW net drop < {settings.thresholds.wow_drop_alert_below:.0f}%. "
            "Partial weeks are excluded."
        )
    else:
        st.success("No anomaly triggers — every full week is within thresholds.")

