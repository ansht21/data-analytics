"""Streamlit entry point: Weekly Revenue Reconciliation cockpit.

Dark "Metric Flow" executive dashboard. The sidebar filters on this page are
global — they drive every page of the multi-page app, because each page
reads the same session-state selections.
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
    kpi_card,
    kpi_row,
    load_all,
    render_sidebar_filters,
    section_title,
    status_banner,
)
from streamlit_app.components.charts import (  # noqa: E402
    bucket_mix_donut,
    settled_clearance_vs_target,
    weekly_combo,
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
weeks, categories, fulfilments, states = render_sidebar_filters(df, weekly)
st.session_state["filters"] = {
    "weeks": weeks,
    "categories": categories,
    "fulfilments": fulfilments,
    "states": states,
}

fdf = apply_filters(df, weeks, categories, fulfilments, states)
fweekly = filtered_weekly(weekly, fdf)
kpi = headline_kpis(fdf, fweekly)

st.markdown("### Revenue Reconciliation Cockpit")
st.markdown(
    "**Amazon India Marketplace** — Gross Invoiced vs Net Realized cash, "
    "leakage categorisation, settled-clearance audit and WoW variance."
)

status_banner(
    "AUDIT STATUS: RECONCILED",
    f"{kpi.total_lines:,} transaction lines · {kpi.unique_orders:,} unique orders · "
    f"{kpi.weeks_active} fiscal weeks ({kpi.full_weeks} full, {kpi.partial_weeks} partial)",
)

st.write("")

kpi_row(
    [
        kpi_card(
            "Gross Invoiced",
            format_inr(kpi.gross_revenue),
            f"{kpi.total_lines:,} transaction lines",
        ),
        kpi_card(
            "Net Realized Cash",
            format_inr(kpi.net_realized),
            f"{kpi.settled_clearance_rate:.1f}% of settled base",
        ),
        kpi_card(
            "Total Leakage",
            format_inr(kpi.total_leakage),
            f"₹{kpi.cancellation_leakage/1e5:,.1f}L cancelled · "
            f"₹{kpi.return_leakage/1e5:,.1f}L returned",
        ),
        kpi_card(
            "Settled Clearance",
            f"{kpi.settled_clearance_rate:.1f}%",
            f"Target {settings.thresholds.settled_clearance_critical_below:.0f}% · "
            f"leakage share {100 - kpi.settled_clearance_rate:.1f}%",
            delta=("▲ " if kpi.settled_clearance_rate >= settings.thresholds.settled_clearance_critical_below else "▼ ")
            + f"{kpi.settled_clearance_rate:.1f}%",
            delta_up=kpi.settled_clearance_rate >= settings.thresholds.settled_clearance_critical_below,
        ),
    ],
    columns=4,
)

section_title("Weekly Performance")
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

section_title("Revenue Composition")
c3, c4 = st.columns([1, 2])
with c3:
    st.plotly_chart(bucket_mix_donut(fdf), use_container_width=True)
with c4:
    st.markdown("**Reconciliation summary**")
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
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        f"Source: Amazon Sale Report (Kaggle CC0) · "
        f"{len(fdf):,} of {len(df):,} lines selected · "
        f"W13–W26 FY22 · settlement lag {kpi.settlement_lag_rate:.1f}% of gross invoiced"
    )

