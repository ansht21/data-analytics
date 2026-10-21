"""Page 4 — Exception Audit: filterable table + one-click CSV export."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402
from streamlit_app.common import (  # noqa: E402
    LEAKAGE_BUCKETS,
    apply_filters,
    inject_theme,
    load_all,
    section_title,
)

st.set_page_config(page_title="Exception Audit", layout="wide",
                   initial_sidebar_state="expanded")
inject_theme()

with st.spinner("Loading reconciliation data ..."):
    df, weekly, anomalies, settings = load_all()

filters = st.session_state.get("filters", {})
fdf = apply_filters(
    df,
    filters.get("weeks", []),
    filters.get("categories", []),
    filters.get("fulfilments", []),
    filters.get("states", []),
)

st.markdown("### 🔍 Exception Audit Log")
st.caption(
    "Every cancelled, returned, lost or damaged order line — the working "
    "paper an accounting team needs to chase the money."
)

exc = fdf[fdf["financial_bucket"].isin(LEAKAGE_BUCKETS)].copy()

b_sel = st.sidebar.multiselect("Bucket", LEAKAGE_BUCKETS, default=LEAKAGE_BUCKETS)
w_sel = st.sidebar.multiselect("Week", sorted(exc["week_label"].unique().tolist()))
max_amt = float(exc["Amount"].max()) if len(exc) else 0.0
min_amt = st.sidebar.number_input("Min Amount ₹", 0.0, max_amt, 0.0)

view = exc[exc["financial_bucket"].isin(b_sel)]
if w_sel:
    view = view[view["week_label"].isin(w_sel)]
view = view[view["Amount"] >= min_amt]

st.caption(
    f"{len(view):,} exception lines · ₹{view['Amount'].sum():,.0f} at risk · "
    f"{view['Order ID'].nunique() if len(view) else 0:,} unique orders"
)

section_title("Exception Detail")
cols = ["Order ID", "parsed_date", "week_label", "Status", "financial_bucket",
        "Amount", "Category", "Fulfilment", "ship-state", "ship-city", "B2B"]
cols = [c for c in cols if c in view.columns]
if len(view):
    st.dataframe(view[cols].head(5000), use_container_width=True, hide_index=True)
    if len(view) > 5000:
        st.caption(f"Showing first 5,000 of {len(view):,} rows — narrow the filters to see more.")
else:
    st.info("No exception rows match the current filters.")

section_title("Export")
csv_bytes = view[cols].to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download filtered exceptions (CSV)",
    data=csv_bytes,
    file_name="exception_audit.csv",
    mime="text/csv",
)

