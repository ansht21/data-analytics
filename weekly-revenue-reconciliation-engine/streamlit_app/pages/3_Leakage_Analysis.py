"""Page 3 — Leakage Analysis: category, fulfilment & state drill-down."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402
from src.reconciliation.metrics import (  # noqa: E402
    category_revenue,
    fulfilment_settlement,
)
from streamlit_app.common import (  # noqa: E402
    LEAKAGE_BUCKETS,
    apply_filters,
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
    category_leakage_bar,
    fulfilment_settlement_bar,
    state_leakage_bar,
)

st.set_page_config(page_title="Leakage Analysis", layout="wide",
                   initial_sidebar_state="expanded")
inject_theme()

with st.spinner("Loading reconciliation data ..."):
    df, weekly, anomalies, settings = load_all()

render_global_sidebar(active_key="leakage", df=df, weekly=weekly)

filters = st.session_state.get("filters", {})
fdf = apply_filters(
    df,
    filters.get("weeks", []),
    filters.get("categories", []),
    filters.get("fulfilments", []),
    filters.get("states", []),
)

st.markdown("### 🕳️ Leakage Deep-Dive")
st.caption(
    "True leakage only — cancellations, returns and loss/damage. "
    "In-Transit and Pending are settlement lag, not loss."
)

buckets = st.sidebar.multiselect("Leakage buckets", LEAKAGE_BUCKETS,
                                  default=LEAKAGE_BUCKETS)
leak = fdf[fdf["financial_bucket"].isin(buckets)]

kpi_row(
    [
        kpi_card("Leakage ₹", f"₹{leak['Amount'].sum():,.0f}",
                 f"{len(leak):,} leakage lines"),
        kpi_card("Leakage Orders",
                 f"{leak['Order ID'].nunique():,}" if "Order ID" in leak.columns else "0",
                 "unique orders affected"),
        kpi_card("Share of Lines",
                 f"{len(leak) / len(fdf) * 100:.2f}%" if len(fdf) else "0%",
                 f"of {len(fdf):,} selected lines"),
        kpi_card("Settled Clearance",
                 f"{headline_kpis(fdf, weekly).settled_clearance_rate:.1f}%",
                 f"Target {settings.thresholds.settled_clearance_critical_below:.0f}%"),
    ],
    columns=4,
)

section_title("Where the Money Leaks")
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(category_leakage_bar(leak), width="stretch")
with c2:
    st.plotly_chart(state_leakage_bar(leak), width="stretch")

section_title("Fulfilment Channel Comparison")
c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(
        fulfilment_settlement_bar(fulfilment_settlement(fdf)), width="stretch"
    )
with c4:
    st.plotly_chart(bucket_mix_donut(fdf), width="stretch")

section_title("Leakage ₹ by Fulfilment & Type")
if len(leak):
    pivot = (
        leak.groupby(["Fulfilment", "financial_bucket"])["Amount"].sum()
        .reset_index().pivot(index="Fulfilment", columns="financial_bucket",
                             values="Amount").fillna(0).round(2)
    )
    st.dataframe(pivot, width="stretch")
else:
    st.info("No leakage rows match the current filters.")

section_title("Category Revenue & Volume")
cat = category_revenue(fdf)
if len(cat):
    st.dataframe(
        cat.rename(columns={
            "Category": "Category", "revenue": "Gross Revenue ₹",
            "orders": "Orders", "qty": "Units",
        }),
        width="stretch", hide_index=True,
    )
else:
    st.info("No rows match the current filters.")

