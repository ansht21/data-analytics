"""Page 2 — Weekly Trends: combo chart, leakage stack and WoW metrics table."""

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
    inject_theme,
    load_all,
    render_global_sidebar,
    section_title,
)
from streamlit_app.components.charts import (  # noqa: E402
    leakage_stacked,
    settled_clearance_vs_target,
    weekly_combo,
)

st.set_page_config(page_title="Weekly Trends", layout="wide",
                   initial_sidebar_state="expanded")
inject_theme()

with st.spinner("Loading reconciliation data ..."):
    df, weekly, anomalies, settings = load_all()

render_global_sidebar(active_key="trends", df=df, weekly=weekly)

filters = st.session_state.get("filters", {})
fdf = apply_filters(
    df,
    filters.get("weeks", []),
    filters.get("categories", []),
    filters.get("fulfilments", []),
    filters.get("states", []),
)
fweekly = filtered_weekly(weekly, fdf)

st.markdown("### 📈 Weekly Trends")
st.caption(
    "Gross invoiced vs net realized cash per fiscal week, with the settled "
    "clearance audit metric plotted against target."
)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(weekly_combo(fweekly), use_container_width=True)
with c2:
    st.plotly_chart(
        settled_clearance_vs_target(
            fweekly, settings.thresholds.settled_clearance_critical_below
        ),
        use_container_width=True,
    )

section_title("Leakage by Week")
st.plotly_chart(leakage_stacked(fweekly), use_container_width=True)

section_title("Week-over-Week Metrics")
tbl = fweekly[[
    "week_label", "gross_revenue", "net_realized", "total_leakage",
    "settled_clearance_rate", "clearance_rate", "cancellation_rate",
    "wow_net_growth", "total_orders", "avg_order_value", "days_observed",
    "is_partial_week",
]].copy()
tbl.columns = [
    "Week", "Gross ₹", "Net ₹", "Leakage ₹", "Settled Clearance %",
    "Gross Coverage %", "Cancel %", "WoW Net %", "Lines", "AOV ₹",
    "Days", "Partial",
]
st.dataframe(tbl.round(2), use_container_width=True, hide_index=True)

neg = tbl[tbl["WoW Net %"] < 0]
partial = tbl[tbl["Partial"]]
if len(neg):
    st.warning(
        f"{len(neg)} week(s) with negative WoW net growth — drill into "
        "Leakage Analysis for root cause."
    )
if len(partial):
    st.info(
        f"{len(partial)} partial week(s) (fewer than 7 observed days) are "
        "excluded from anomaly detection to avoid false alarms."
    )

