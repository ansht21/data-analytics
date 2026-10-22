"""Streamlit entry point: the Revenue Reconciliation cockpit.

A dark "Midnight Deck" executive dashboard laid out like a modern CRM
console: bespoke grouped sidebar navigation, two large gradient KPI heroes,
an annotated revenue-trend area chart, a right-hand rail of supporting
panels, and a bottom row with the revenue-mix donut and the settlement
gauge.

The sidebar filters are global — they drive every page of the multi-page
app, because each page reads the same session-state selections.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.common import (  # noqa: E402
    apply_filters,
    filtered_weekly,
    format_inr,
    headline_kpis,
    inject_theme,
    load_all,
    render_global_sidebar,
    status_banner,
)
from streamlit_app.components.charts import (  # noqa: E402
    bucket_legend_rows,
    cockpit_area_trend,
    cockpit_bucket_donut,
    cockpit_gauge,
    cockpit_mini_area,
    cockpit_volume_bars,
)
from streamlit_app.components.cockpit import (  # noqa: E402
    hero_card,
    legend_row,
    panel,
    stat_pill,
)

st.set_page_config(
    page_title="Revenue Reconciliation Cockpit",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

with st.spinner("Loading reconciliation data ..."):
    df, weekly, anomalies, settings = load_all()

# Global filters (shared with every page via session state).
render_global_sidebar(active_key="overview", df=df, weekly=weekly)

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

target = settings.thresholds.settled_clearance_critical_below

# ---------------------------------------------------------------- headline row
h1, h2, h3 = st.columns([1.15, 1.15, 0.85], gap="medium")
with h1:
    st.markdown(
        hero_card(
            "Total Revenue Invoiced",
            format_inr(kpi.gross_revenue),
            f"{kpi.total_lines:,} transaction lines audited",
            foot=f"Across {kpi.weeks_active} fiscal weeks · "
                 f"{kpi.full_weeks} full / {kpi.partial_weeks} partial",
        ),
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        hero_card(
            "Net Realized Cash",
            format_inr(kpi.net_realized),
            f"{kpi.settled_clearance_rate:.1f}% of the settled base retained",
            foot=f"Settlement lag {kpi.settlement_lag_rate:.1f}% of gross · "
                 f"₹{(kpi.in_transit_value + kpi.pending_value)/1e7:,.2f} Cr in flight",
            alt=True,
        ),
        unsafe_allow_html=True,
    )
with h3:
    st.markdown(
        stat_pill("L", "Total Leakage", format_inr(kpi.total_leakage), "neg"),
        unsafe_allow_html=True,
    )
    st.markdown(
        stat_pill(
            "C",
            "Cancelled Orders",
            f"{kpi.cancelled_orders:,}",
            "neg" if kpi.cancelled_orders else "pos",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        stat_pill(
            "S",
            "Settled Clearance",
            f"{kpi.settled_clearance_rate:.1f}%",
            "pos" if kpi.settled_clearance_rate >= target else "warn",
        ),
        unsafe_allow_html=True,
    )

status_banner(
    "AUDIT STATUS: RECONCILED",
    f"{kpi.total_lines:,} transaction lines · {kpi.unique_orders:,} unique orders · "
    f"{kpi.weeks_active} fiscal weeks ({kpi.full_weeks} full, {kpi.partial_weeks} partial)",
)

# ------------------------------------------------- trend + right-hand rail
st.write("")
main, rail = st.columns([1.9, 1], gap="medium")

with main:
    with panel(
        "Revenue Trend — Gross Invoiced vs Net Realized",
        "Weekly fiscal calendar · W13–W26 FY22",
    ):
        st.plotly_chart(cockpit_area_trend(fweekly), width="stretch")

with rail:
    with panel("Net Realized Velocity", "Rolling weekly shape"):
        st.plotly_chart(cockpit_mini_area(fweekly), width="stretch")

    with panel("Transaction Volume / Week", "Line count per fiscal week"):
        st.plotly_chart(cockpit_volume_bars(fweekly), width="stretch")

# ----------------------------------------------------- donut + gauge + table
st.write("")
d1, d2 = st.columns([1.15, 0.85], gap="medium")

with d1:
    with panel("Revenue by Financial Bucket", "Where every rupee landed"):
        donut_col, legend_col = st.columns([1.15, 1], gap="medium")
        with donut_col:
            st.plotly_chart(cockpit_bucket_donut(fdf), width="stretch")
        with legend_col:
            legend_rows = bucket_legend_rows(fdf)
            legend_total = sum(amount for _, _, amount in legend_rows) or 1.0
            st.markdown(
                "".join(
                    legend_row(
                        color,
                        label,
                        f"₹{amount/1e7:,.2f} Cr",
                        f"{amount / legend_total * 100:.1f}%",
                    )
                    for label, color, amount in legend_rows
                ),
                unsafe_allow_html=True,
            )

with d2:
    with panel("Settlement Health", f"Audit target {target:.0f}% of settled base"):
        st.plotly_chart(
            cockpit_gauge(kpi.settled_clearance_rate, "of settled base retained"),
            width="stretch",
        )

st.write("")
with panel("Weekly Reconciliation Detail", "Every figure below is filter-aware"):
    st.dataframe(
        fweekly[[
            "week_label", "gross_revenue", "net_realized", "total_leakage",
            "settled_clearance_rate", "wow_net_growth", "total_orders",
            "is_partial_week",
        ]].rename(columns={
            "week_label": "Week",
            "gross_revenue": "Gross ₹",
            "net_realized": "Net ₹",
            "total_leakage": "Leakage ₹",
            "settled_clearance_rate": "Settled Clearance %",
            "wow_net_growth": "WoW Net %",
            "total_orders": "Lines",
            "is_partial_week": "Partial",
        }),
        width="stretch",
        hide_index=True,
    )

st.caption(
    f"Source: Amazon Sale Report (Kaggle CC0) · "
    f"{len(fdf):,} of {len(df):,} lines selected · "
    f"W13–W26 FY22 · settlement lag {kpi.settlement_lag_rate:.1f}% of gross invoiced"
)


