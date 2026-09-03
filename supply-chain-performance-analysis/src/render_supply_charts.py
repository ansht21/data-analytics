"""
Generate per-chart visuals for the Supply Chain project, mirroring the
multi-chart image style used in the subscription-retention and uber
projects.

Output PNGs (overwritten on each run):
    image/supply_revenue_by_channel.png
    image/supply_avg_delivery_by_warehouse.png
    image/supply_monthly_revenue_trend.png
    image/supply_abc_classification.png
    image/supply_discount_margin.png
    image/supply_warehouse_ontime.png
    image/supply_profit_by_supplier.png  (bonus)

Run from supply-chain-performance-analysis/:
    python src/render_supply_charts.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "Cleaned_Supplychain_Data.csv"
OUT_DIR = ROOT / "image"

NAVY = "#1F3864"
BLUE = "#2F75B5"
TEAL = "#00A6A6"
LIGHT_BLUE = "#DDEBF7"
GREEN = "#548235"
RED = "#C00000"
ORANGE = "#F4B183"
TEXT = "#1F2937"
PALETTE = ["#1F3864", "#2F75B5", "#00A6A6", "#F4B183", "#9C27B0", "#548235"]


def _style(ax, title: str, ylabel: str = "", xlabel: str = ""):
    ax.set_title(title, fontsize=13, weight="bold", color=NAVY, pad=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=TEXT)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=TEXT)
    ax.tick_params(axis="both", labelsize=8, colors=TEXT)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)


def chart_revenue_by_channel(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    data = df.groupby("Sales_Channel")["revenue"].sum().div(1e6).round(2)
    colors = [BLUE, TEAL, ORANGE, "#9C27B0"]
    bars = ax.bar(data.index, data.values, color=colors[: len(data)])
    _style(ax, "Revenue by Sales Channel ($M)", ylabel="Revenue ($M)")
    for b, v in zip(bars, data.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"${v:.1f}M",
                ha="center", fontsize=9, weight="bold", color=TEXT)
    ax.set_ylim(0, data.max() * 1.15)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "supply_revenue_by_channel.png")
    plt.close(fig)


def chart_avg_delivery_by_warehouse(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    data = df.groupby("WarehouseCode")["delivery_days"].mean().round(2).sort_values()
    bars = ax.bar(data.index, data.values, color=BLUE)
    _style(ax, "Avg Delivery Days by Warehouse", ylabel="Avg Delivery Days", xlabel="Warehouse")
    for b, v in zip(bars, data.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.04, f"{v:.2f}",
                ha="center", fontsize=9, weight="bold", color=TEXT)
    ax.set_ylim(0, data.max() * 1.18)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "supply_avg_delivery_by_warehouse.png")
    plt.close(fig)


def chart_monthly_revenue_trend(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    monthly = df.groupby("order_month")["revenue"].sum().div(1e6).round(2)
    ax.plot(monthly.index.astype(str), monthly.values, color=BLUE, marker="o", linewidth=2.2)
    ax.fill_between(range(len(monthly)), monthly.values, color=BLUE, alpha=0.15)
    _style(ax, "Monthly Net Revenue Trend ($M)", ylabel="Revenue ($M)", xlabel="Month")
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "supply_monthly_revenue_trend.png")
    plt.close(fig)


def chart_abc_classification(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    abc = (df.groupby("_ProductID")["revenue"].sum()
             .sort_values(ascending=False).reset_index())
    abc["cum_share"] = abc["revenue"].cumsum() / abc["revenue"].sum() * 100
    ax2 = ax.twinx()
    ax.bar(range(len(abc)), abc["revenue"].div(1e3), color=BLUE, label="Product revenue ($K)")
    ax2.plot(range(len(abc)), abc["cum_share"], color=RED, marker="o", markersize=3, linewidth=1.5, label="Cumulative share %")
    ax2.axhline(80, color="gray", linestyle="--", linewidth=0.8)
    ax2.set_ylabel("Cumulative Revenue Share %", color=RED, fontsize=9)
    ax2.tick_params(axis="y", colors=RED, labelsize=8)
    _style(ax, "ABC Classification — Product Revenue Concentration", ylabel="Revenue ($K)", xlabel="Products (sorted)")
    ax.set_xticks([])
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax2.legend(loc="upper right", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "supply_abc_classification.png")
    plt.close(fig)


def chart_discount_margin(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    df = df.copy()
    df["discount_band"] = pd.cut(df["Discount_Applied"],
                                 bins=[-0.01, 0.05, 0.10, 0.15, 0.20, 1.01],
                                 labels=["0-5%", "5-10%", "10-15%", "15-20%", "20%+"])
    data = df.groupby("discount_band", observed=True)["profit_margin"].mean().mul(100).round(2)
    colors = [BLUE, TEAL, ORANGE, "#9C27B0", RED]
    bars = ax.bar(data.index.astype(str), data.values, color=colors)
    _style(ax, "Realised Profit Margin by Discount Band", ylabel="Margin %", xlabel="Discount Band")
    for b, v in zip(bars, data.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.1f}%",
                ha="center", fontsize=9, weight="bold", color=TEXT)
    ax.set_ylim(0, max(data.values) * 1.20)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "supply_discount_margin.png")
    plt.close(fig)


def chart_warehouse_ontime(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    data = df.groupby("WarehouseCode")["on_time"].mean().mul(100).round(1).sort_values()
    bars = ax.bar(data.index.astype(str), data.values, color=GREEN)
    _style(ax, "On-Time Delivery Rate by Warehouse", ylabel="On-Time %", xlabel="Warehouse")
    for b, v in zip(bars, data.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.1f}%",
                ha="center", fontsize=9, weight="bold", color=TEXT)
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "supply_warehouse_ontime.png")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chart_revenue_by_channel(df)
    chart_avg_delivery_by_warehouse(df)
    chart_monthly_revenue_trend(df)
    chart_abc_classification(df)
    chart_discount_margin(df)
    chart_warehouse_ontime(df)
    print("Supply Chain per-chart visuals written to image/")


if __name__ == "__main__":
    main()
