"""
🤖 Business Intelligence AI Agent
==================================
Interactive Streamlit app over the three committed portfolio datasets
(Supply Chain, Uber Trips, Customer Churn) plus custom CSV/Excel upload.

Modes:
- Offline insight mode (default): quick-insight chips + executive brief +
  KPI cards + Plotly charts — all deterministic pandas, zero API key.
- Live AI chat (Groq + LangGraph ReAct agent): unlocks by adding
  GROQ_API_KEY to .env. The sidebar banner always shows the active mode.

Author: Ansh Thakur
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from src import agent as agent_layer
from src.analytics import chip_labels, run_chip
from src.brief import brief_markdown, build_brief
from src.datasets import DATASETS, dataset_kpis, load_dataset

st.set_page_config(page_title="Business Intelligence AI Agent", page_icon="🤖", layout="wide")

defaults = {"dataset_key": "supply", "chat": [], "custom_df": None,
            "custom_name": None, "brief_open": False}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

with st.sidebar:
    st.header("📂 Dataset")
    choices = [(k, f"{v['icon']} {v['label']} — {v['scale']}") for k, v in DATASETS.items()]
    keys = [k for k, _ in choices]
    labels = [lbl for _, lbl in choices] + ["📁 Upload your own CSV / Excel"]
    pick = st.radio("Choose a dataset", labels,
                    index=keys.index(st.session_state.dataset_key)
                    if st.session_state.dataset_key in keys else 0)
    if pick.startswith("📁"):
        up = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
        if up is not None:
            name = up.name.lower()
            st.session_state.custom_df = pd.read_csv(up) if name.endswith(".csv") else pd.read_excel(up)
            st.session_state.custom_name = up.name
            st.session_state.dataset_key = "__custom__"
            st.session_state.chat = []
    elif st.session_state.dataset_key != keys[labels.index(pick)]:
        st.session_state.dataset_key = keys[labels.index(pick)]
        st.session_state.chat = []
        st.session_state.brief_open = False

    st.divider()
    banner, mode = agent_layer.mode_banner()
    st.info(banner, icon="ℹ️")
    st.caption("Built with Streamlit · pandas · Plotly · LangGraph · Groq · 👤 Ansh Thakur")

key = st.session_state.dataset_key


@st.cache_data(show_spinner="Loading dataset…")
def _cached_load(dataset_key: str) -> pd.DataFrame:
    return load_dataset(dataset_key)


if key == "__custom__":
    df = st.session_state.custom_df
    title = f"📁 {st.session_state.custom_name or 'Custom upload'}"
    scale = f"{len(df):,} rows" if df is not None else ""
else:
    df = _cached_load(key)
    title, scale = f"{DATASETS[key]['icon']} {DATASETS[key]['label']}", DATASETS[key]["scale"]

if df is None:
    st.warning("Upload a CSV/Excel file to begin.")
    st.stop()

agent_layer.set_dataframe(df)

# ------------------------------------------------------------------ #
# Render one insight card: finding -> explanation -> suggestion + chart + logic
# ------------------------------------------------------------------ #
def _fig(spec: dict):
    import plotly.graph_objects as go

    fig = (go.Figure(go.Scatter(x=spec["x"], y=spec["y"], mode="lines+markers"))
           if spec["kind"] == "line" else go.Figure(go.Bar(x=spec["x"], y=spec["y"])))
    if spec.get("annotate_max"):
        i = max(range(len(spec["y"])), key=lambda j: spec["y"][j])
        fig.add_annotation(x=spec["x"][i], y=spec["y"][i], text=f"★ {spec['y'][i]}",
                           showarrow=True, arrowhead=2)
    fig.update_layout(title=spec["title"], xaxis_title=spec.get("x_label", ""),
                      yaxis_title=spec.get("y_label", ""), height=360,
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


def render_insight(ins, prefix: str) -> None:
    st.markdown(f"**📊 Finding:** {ins.finding}")
    st.markdown(f"**💡 Why it matters:** {ins.explanation}")
    st.markdown(f"**🎯 Suggested decision:** {ins.suggestion}")
    if ins.chart:
        st.plotly_chart(_fig(ins.chart), use_container_width=True, key=f"{prefix}-chart")
    with st.expander("🔍 Inspect logic & query"):
        st.code(ins.pandas_snippet, language="python")
        st.caption(f"Executed in {ins.runtime_ms:.1f} ms · dataset: {ins.dataset} · "
                   "recomputed live from the CSV above.")


# ------------------------------------------------------------------ #
# Quick-insight chips (deterministic; work offline)
# ------------------------------------------------------------------ #
if key != "__custom__":
    st.subheader("⚡ Quick insights — one click, zero typing")
    for label in chip_labels(key):
        if st.button(f"▶ {label}", key=f"chip-{key}-{label}"):
            with st.spinner("Computing live from the data…"):
                ins = run_chip(key, label, df)
            with st.chat_message("assistant"):
                render_insight(ins, prefix=f"{key}-{label}")
            st.session_state.chat.append(("chip", label, ins))
    st.divider()

    if st.button("📄 Generate Executive Brief", key="brief-btn"):
        st.session_state.brief_open = True
    if st.session_state.brief_open:
        with st.spinner("Assembling brief…"):
            brief = build_brief(key, df)
        st.subheader(f"📄 Executive Brief — {DATASETS[key]['label']}")
        st.write(brief["intro"])
        kcols = st.columns(len(brief["kpis"]))
        for col, (label, value) in zip(kcols, brief["kpis"]):
            col.metric(label, value)
        for i, ins in enumerate(brief["insights"], 1):
            st.markdown(f"#### {i}. {ins.finding}")
            st.markdown(f"*Why it matters:* {ins.explanation}")
            st.markdown(f"*Recommended decision:* {ins.suggestion}")
            if ins.chart:
                st.plotly_chart(_fig(ins.chart), use_container_width=True, key=f"brief-{key}-{i}")
        st.markdown("**Top risks**")
        for t, d in brief["risks"]:
            st.markdown(f"- **{t}:** {d}")
        st.markdown("**Recommended decisions**")
        for i, d in enumerate(brief["decisions"], 1):
            st.markdown(f"{i}. {d}")
        st.download_button("⬇ Download brief (Markdown)",
                           data=brief_markdown(brief, DATASETS[key]["label"]),
                           file_name=f"executive_brief_{key}.md", mime="text/markdown",
                           key="brief-dl")
        st.divider()

agent_layer.set_dataframe(df)
st.title("🤖 Business Intelligence AI Agent")
st.caption(f"{title} · {scale} — every number below is computed live from the data.")
if key != "__custom__":
    st.caption(DATASETS[key]["blurb"])

if key == "__custom__":
    kpis = [("Rows", f"{len(df):,}"), ("Columns", f"{df.shape[1]}"),
            ("Numeric cols", f"{df.select_dtypes('number').shape[1]}"),
            ("Missing cells", f"{int(df.isna().sum().sum()):,}")]
else:
    kpis = dataset_kpis(key, df)
cols = st.columns(len(kpis))
for col, (label, value) in zip(cols, kpis):
    col.metric(label, value)
st.dataframe(df.head(), use_container_width=True)

# ------------------------------------------------------------------ #
# Chat history + live/offline chat
# ------------------------------------------------------------------ #
st.subheader("💬 Ask the agent")
for role, content, extra in st.session_state.chat:
    if role == "chip":
        continue
    with st.chat_message(role):
        st.markdown(content if isinstance(content, str) else str(content))

query = st.chat_input("Ask a business question about this dataset…")
if query:
    st.session_state.chat.append(("user", query, ""))
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Analysing…"):
            res = agent_layer.chat(query)
        tag = "🟢 Live AI" if res.mode == "live" else "🟡 Offline"
        st.markdown(f"*{tag} answer:* {res.answer}")
    st.session_state.chat.append(("assistant", res.answer, ""))

