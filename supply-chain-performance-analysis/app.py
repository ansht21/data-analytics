"""
Interactive Supply Chain dashboard (Ocean Navy/Teal theme).

Every sidebar filter is LIVE: changing Category, Delivery Status, Warehouse
or Year re-filters the 7,991 cleaned orders and recomputes ALL KPI cards and
ALL charts instantly.

Run from supply-chain-performance-analysis/:
    streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "Cleaned_Supplychain_Data.csv"

NAVY = "#0B2A4A"
TEAL = "#0E9F8A"
SKY = "#E0F2FE"
CYAN = "#06B6D4"
GRAY = "#CBD5E1"
DARK = "#0F172A"
MUTED = "#64748B"

st.set_page_config(page_title="Supply Chain Cockpit", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["wh_short"] = df["WarehouseCode"].str.replace("WARE-", "", regex=False)
    df["year"] = df["OrderDate"].dt.year.astype(str)
    return df


def base_style(ax, title: str):
    ax.set_title(title, fontsize=12, weight="bold", color=NAVY, pad=8)
    ax.tick_params(axis="both", labelsize=8, colors=MUTED)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)


df = load_data()

# ---------------- Sidebar filters (LIVE) ----------------
st.sidebar.header("Filter Panel")
sel_channels = st.sidebar.multiselect(
    "Category", sorted(df["Sales_Channel"].unique()),
    default=sorted(df["Sales_Channel"].unique()))
sel_delivery = st.sidebar.multiselect(
    "Delivery Status", ["Late", "On Time"], default=["Late", "On Time"])
sel_wh = st.sidebar.multiselect(
    "Warehouse Code", sorted(df["wh_short"].unique()),
    default=sorted(df["wh_short"].unique()))
sel_years = st.sidebar.multiselect(
    "Order Year", sorted(df["year"].unique()),
    default=sorted(df["year"].unique()))

mask = (
    df["Sales_Channel"].isin(sel_channels)
    & df["wh_short"].isin(sel_wh)
    & df["year"].isin(sel_years)
)
if "Late" not in sel_delivery:
    mask &= df["on_time"].astype(bool)
if "On Time" not in sel_delivery:
    mask &= ~df["on_time"].astype(bool)
fdf = df[mask]

st.title("Executive Supply Chain Performance & Inventory Cockpit")
st.caption("Fulfillment & Network Diagnostics — every filter above recomputes all KPIs and charts")

if fdf.empty:
    st.warning("No orders match the current filter selection. Widen the filters.")
    st.stop()

# ---------------- KPIs (recomputed live) ----------------
tot_rev = fdf["revenue"].sum() / 1e6
tot_prof = fdf["profit"].sum() / 1e6
avg_del = fdf["delivery_days"].mean()
n_orders = len(fdf)
ontime = fdf["on_time"].astype(bool).mean() * 100

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Net Revenue", f"${tot_rev:.2f}M")
k2.metric("Total Net Profit", f"${tot_prof:.2f}M")
k3.metric("Avg Delivery Days", f"{avg_del:.1f} Days")
k4.metric("Total Orders", f"{n_orders / 1000:.1f}K" if n_orders >= 1000 else f"{n_orders}")
k5.metric("On-Time Rate", f"{ontime:.1f}%")

# ---------------- Charts row 1 ----------------
c1, c2, c3 = st.columns(3)

with c1:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    monthly = fdf.groupby(fdf["OrderDate"].dt.to_period("M"))["revenue"].sum().div(1e6)
    ax.plot(range(len(monthly)), monthly.values, color=NAVY, marker="o", markersize=3, linewidth=2)
    ax.fill_between(range(len(monthly)), monthly.values, color=SKY, alpha=0.7)
    base_style(ax, "Revenue Trend Over Time ($M)")
    ax.set_xticks(range(0, len(monthly), max(1, len(monthly) // 6)))
    ax.set_xticklabels([str(m) for m in monthly.index[::max(1, len(monthly) // 6)]], rotation=30, fontsize=7)
    st.pyplot(fig)
    plt.close(fig)

with c2:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    chan = fdf.groupby("Sales_Channel")["profit"].sum().div(1e6).sort_values()
    bars = ax.barh(chan.index, chan.values, color=TEAL, height=0.55)
    for b in bars:
        w = b.get_width()
        ax.text(w * 1.02, b.get_y() + b.get_height() / 2, f"${w:.1f}M",
                va="center", fontsize=8, weight="bold", color=DARK)
    base_style(ax, "Net Profit by Channel ($M)")
    ax.set_xlim(0, chan.max() * 1.3 if chan.max() > 0 else 1)
    st.pyplot(fig)
    plt.close(fig)

with c3:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    flags = fdf["on_time"].astype(bool)
    late_n, on_n = int((~flags).sum()), int(flags.sum())
    total_n = max(1, late_n + on_n)
    ax.pie([late_n, on_n], labels=[f"Late ({late_n / total_n:.1%})", f"On-Time ({on_n / total_n:.1%})"],
           colors=[NAVY, GRAY], autopct="%1.0f%%", startangle=90, pctdistance=0.75,
           wedgeprops=dict(width=0.42, edgecolor="white"),
           textprops=dict(fontsize=8, color=MUTED))
    ax.text(0, 0, f"{on_n / total_n:.1%}", ha="center", va="center",
            fontsize=13, weight="bold", color=NAVY)
    base_style(ax, "Delivery Status Distribution")
    st.pyplot(fig)
    plt.close(fig)

# ---------------- Charts row 2 ----------------
c4, c5, c6 = st.columns(3)

with c4:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    wh = fdf.groupby("wh_short")["revenue"].sum().div(1e6).sort_values(ascending=False)
    bars = ax.bar(wh.index, wh.values, color=NAVY, width=0.55)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h * 1.02, f"${h:.1f}M",
                ha="center", fontsize=7.5, weight="bold", color=DARK)
    base_style(ax, "Revenue by Warehouse ($M)")
    ax.set_ylim(0, wh.max() * 1.2 if wh.max() > 0 else 1)
    st.pyplot(fig)
    plt.close(fig)

with c5:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    dm = fdf.groupby(fdf["OrderDate"].dt.to_period("M"))["delivery_days"].mean()
    ax.plot(range(len(dm)), dm.values, color=CYAN, linewidth=2)
    ax.fill_between(range(len(dm)), dm.values, color=SKY, alpha=0.7)
    ax.axhline(avg_del, color=NAVY, linestyle="--", linewidth=1)
    base_style(ax, "Avg Delivery Days Timeline")
    ax.set_ylim(0, max(8, dm.max() * 1.15) if len(dm) else 8)
    ax.set_xticks(range(0, len(dm), max(1, len(dm) // 6)))
    ax.set_xticklabels([str(m) for m in dm.index[::max(1, len(dm) // 6)]], rotation=30, fontsize=7)
    st.pyplot(fig)
    plt.close(fig)

with c6:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    fig.patch.set_facecolor("white")
    wp = fdf.groupby("wh_short")["profit"].sum().div(1e6).sort_values(ascending=False)
    bars = ax.bar(wp.index, wp.values, color=TEAL, width=0.55)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h * 1.03, f"${h:.1f}M",
                ha="center", fontsize=7.5, weight="bold", color=DARK)
    base_style(ax, "Profit by Warehouse ($M)")
    ax.set_ylim(0, wp.max() * 1.2 if wp.max() > 0 else 1)
    st.pyplot(fig)
    plt.close(fig)

st.caption("Created by Ansh Thakur | Data Analyst Portfolio Dashboard")
