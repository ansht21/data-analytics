"""
Interactive Subscription Retention dashboard (Crimson/Rose theme).

Every sidebar filter is LIVE: changing Contract, Internet, Payment, Tenure
or Churn status re-filters the 7,032 customers and recomputes ALL KPI cards
and ALL charts instantly.

Run from subscription-retention-analytics/:
    streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "Telco_Customer_Churn.csv"

CRIMSON = "#7F1D2D"
ROSE = "#E11D48"
ROSE_LIGHT = "#FFE4E6"
AMBER = "#B45309"
GREEN = "#059669"
GRAY = "#CBD5E1"
DARK = "#0F172A"
MUTED = "#64748B"

st.set_page_config(page_title="Retention & Churn Analytics", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).copy()
    df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)
    df["tenure_band"] = pd.cut(df["tenure"], bins=[-1, 6, 12, 24, 48, 72],
                               labels=["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"])
    return df


def base_style(ax, title: str):
    ax.set_title(title, fontsize=12, weight="bold", color=CRIMSON, pad=8)
    ax.tick_params(axis="both", labelsize=8, colors=MUTED)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)


df = load_data()

# ---------------- Sidebar filters (LIVE) ----------------
st.sidebar.header("Filter Panel")
sel_contract = st.sidebar.multiselect(
    "Contract", sorted(df["Contract"].unique()), default=sorted(df["Contract"].unique()))
sel_net = st.sidebar.multiselect(
    "Internet", sorted(df["InternetService"].unique()), default=sorted(df["InternetService"].unique()))
sel_pay = st.sidebar.multiselect(
    "Payment", sorted(df["PaymentMethod"].unique()), default=sorted(df["PaymentMethod"].unique()))
sel_ten = st.sidebar.multiselect(
    "Tenure", ["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"],
    default=["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"])
sel_churn = st.sidebar.multiselect(
    "Churn", ["Churned", "Retained"], default=["Churned", "Retained"])

mask = (
    df["Contract"].isin(sel_contract)
    & df["InternetService"].isin(sel_net)
    & df["PaymentMethod"].isin(sel_pay)
    & df["tenure_band"].astype(str).isin(sel_ten)
)
if "Churned" not in sel_churn:
    mask &= df["ChurnFlag"] == 0
if "Retained" not in sel_churn:
    mask &= df["ChurnFlag"] == 1
fdf = df[mask]

st.title("Subscription Retention & Churn Analytics Dashboard")
st.caption("Executive Decision Support System — every filter above recomputes all KPIs and charts")

if fdf.empty:
    st.warning("No customers match the current filter selection. Widen the filters.")
    st.stop()

# ---------------- KPIs (recomputed live) ----------------
n = len(fdf)
churn = fdf["ChurnFlag"].mean()
tenure = fdf["tenure"].mean()
rar = (fdf["MonthlyCharges"] * fdf["ChurnFlag"]).sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Customers", f"{n:,}")
k2.metric("Churn Rate", f"{churn:.1%}")
k3.metric("Avg Tenure (mo)", f"{tenure:.1f}")
k4.metric("Revenue at Risk", f"${rar / 1000:,.0f}K")
k5.metric("Retention Rate", f"{1 - churn:.1%}")

# ---------------- Charts row 1 ----------------
c1, c2, c3 = st.columns(3)

with c1:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    order = ["Month-to-month", "One year", "Two year"]
    data = fdf.groupby("Contract")["ChurnFlag"].mean().mul(100).reindex(order).dropna()
    bars = ax.bar(data.index, data.values, color=CRIMSON, width=0.52)
    for j, v in enumerate(data.values):
        ax.text(j, v * 1.03 + 0.5, f"{v:.1f}%", ha="center", fontsize=8.5, color=DARK, weight="bold")
    base_style(ax, "Churn Rate by Contract")
    ax.set_ylim(0, data.max() * 1.25 if data.max() > 0 else 10)
    st.pyplot(fig)
    plt.close(fig)

with c2:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    bands = ["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"]
    data = fdf.groupby("tenure_band", observed=True)["ChurnFlag"].mean().mul(100).reindex(bands).dropna()
    ax.plot(range(len(data)), data.values, color=ROSE, marker="o", linewidth=2.4, markersize=5)
    ax.fill_between(range(len(data)), data.values, color=ROSE_LIGHT, alpha=0.6)
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels(list(data.index), fontsize=8)
    for j, v in enumerate(data.values):
        ax.text(j, v * 1.03 + 0.5, f"{v:.1f}%", ha="center", fontsize=8, color=DARK, weight="bold")
    base_style(ax, "Churn Rate by Tenure Band")
    ax.set_ylim(0, data.max() * 1.25 if data.max() > 0 else 10)
    st.pyplot(fig)
    plt.close(fig)

with c3:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    data = fdf.groupby("InternetService")["customerID"].count()
    wedges, _, autotexts = ax.pie(
        data.values, labels=data.index, colors=[CRIMSON, ROSE, GRAY],
        autopct="%1.0f%%", startangle=90, pctdistance=0.76,
        wedgeprops=dict(width=0.42, edgecolor="white"),
        textprops=dict(fontsize=8.5, color=MUTED))
    for t in autotexts:
        t.set_color("white")
        t.set_weight("bold")
    base_style(ax, "Customer Mix by Internet Service")
    st.pyplot(fig)
    plt.close(fig)

# ---------------- Charts row 2 ----------------
c4, c5, c6 = st.columns(3)

with c4:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    grp = (fdf.assign(rar=fdf["MonthlyCharges"] * fdf["ChurnFlag"])
           .groupby(["Contract", "InternetService"], observed=True)["rar"].sum()
           .div(1000).sort_values(ascending=False).head(6).reset_index())
    grp["label"] = (grp["Contract"].str.replace("Month-to-month", "M2M")
                    + " | " + grp["InternetService"].replace({"Fiber optic": "Fiber", "No": "None"}))
    bars = ax.barh(grp["label"][::-1], grp["rar"][::-1], color=ROSE)
    for j, v in enumerate(grp["rar"][::-1].values):
        ax.text(v * 1.02, j, f"${v:.0f}K", va="center", fontsize=8, color=DARK, weight="bold")
    base_style(ax, "Top Revenue-at-Risk Segments ($K)")
    ax.set_xlim(0, grp["rar"].max() * 1.25 if grp["rar"].max() > 0 else 1)
    st.pyplot(fig)
    plt.close(fig)

with c5:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    data = (fdf.assign(rar=fdf["MonthlyCharges"] * fdf["ChurnFlag"])
            .groupby("Contract", observed=True)["rar"].sum().div(1000))
    order = [c for c in ["Month-to-month", "One year", "Two year"] if c in data.index]
    data = data.reindex(order)
    bars = ax.bar(data.index, data.values, color=CRIMSON, width=0.52)
    for j, v in enumerate(data.values):
        ax.text(j, v * 1.03 + 1, f"${v:.0f}K", ha="center", fontsize=8.5, color=DARK, weight="bold")
    base_style(ax, "Revenue at Risk by Contract")
    ax.set_ylim(0, data.max() * 1.25 if data.max() > 0 else 10)
    st.pyplot(fig)
    plt.close(fig)

with c6:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    t = fdf.groupby("tenure")["ChurnFlag"].mean().mul(100)
    ax.plot(t.index, t.values, color=CRIMSON, linewidth=2.2)
    ax.fill_between(t.index, t.values, color=ROSE_LIGHT, alpha=0.7)
    base_style(ax, "Churn Rate by Tenure (months)")
    st.pyplot(fig)
    plt.close(fig)

st.caption("Created by Ansh Thakur | Data Analyst Portfolio Dashboard")
