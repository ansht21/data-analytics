"""
Generate per-chart visuals for the Uber Trip Demand project to mirror the
multi-chart image style used in the subscription-retention and supply-chain
projects.

Output PNGs (overwritten on each run):
    image/uber_hourly_demand.png
    image/uber_vehicle_revenue.png
    image/uber_airport_share.png
    image/uber_zone_pareto.png
    image/uber_rating_vs_fare.png

Run from uber-trip-demand-analysis/:
    python src/render_uber_charts.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_CANDIDATES = [
    ROOT / "data" / "UberTripsData.csv",
    ROOT / "data" / "Cleaned_UberTrips_Data.csv",
    ROOT / "data" / "Uber_Cleaned_data.csv",
]
OUT_DIR = ROOT / "image"

NAVY = "#1F3864"
BLUE = "#2F75B5"
TEAL = "#00A6A6"
LIGHT_BLUE = "#DDEBF7"
GREEN = "#548235"
RED = "#C00000"
ORANGE = "#F4B183"
TEXT = "#1F2937"


def _resolve_data() -> Path:
    for p in DATA_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("No Uber trips CSV found in data/")


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


def chart_hourly_demand(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    data = df.groupby("Hour").size()
    bars = ax.bar(data.index, data.values, color=BLUE)
    peak = data.idxmax()
    bars[list(data.index).index(peak)].set_color(RED)
    _style(ax, "Trips by Hour of Day", ylabel="Trips", xlabel="Hour")
    for h, v in data.items():
        if v > data.median() * 1.2:
            ax.text(h, v + 25, f"{v:,}", ha="center", fontsize=7, color=TEXT)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "uber_hourly_demand.png")
    plt.close(fig)


def chart_vehicle_revenue(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    rev = df.groupby("Vehicle_Type")["Fare_Amount"].sum().div(1e5).round(2).sort_values()
    bars = ax.barh(rev.index, rev.values, color=[BLUE, TEAL, ORANGE, "#9C27B0", GREEN][: len(rev)])
    _style(ax, "Total Revenue by Vehicle Type (₹ Lakhs)", ylabel="", xlabel="Revenue (₹ Lakhs)")
    for b, v in zip(bars, rev.values):
        ax.text(v + rev.max() * 0.01, b.get_y() + b.get_height() / 2, f"₹{v:.1f}L",
                va="center", fontsize=9, weight="bold", color=TEXT)
    ax.set_xlim(0, rev.max() * 1.18)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "uber_vehicle_revenue.png")
    plt.close(fig)


def chart_airport_share(df: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.2), dpi=140)
    fig.patch.set_facecolor("white")

    counts = df["Is_Airport_Trip"].value_counts()
    labels = ["Non-Airport", "Airport"]
    ax1.pie(counts.values, labels=labels,
            colors=[BLUE, ORANGE],
            autopct="%1.1f%%", startangle=90,
            wedgeprops=dict(edgecolor="white", linewidth=2),
            textprops=dict(fontsize=9, color=TEXT))
    ax1.set_title("Trip Share by Airport Flag", fontsize=11, weight="bold", color=NAVY)

    rev = df.groupby("Is_Airport_Trip")["Fare_Amount"].sum()
    ax2.pie(rev.values, labels=labels,
            colors=[BLUE, ORANGE],
            autopct="%1.1f%%", startangle=90,
            wedgeprops=dict(edgecolor="white", linewidth=2),
            textprops=dict(fontsize=9, color=TEXT))
    ax2.set_title("Revenue Share by Airport Flag", fontsize=11, weight="bold", color=NAVY)

    fig.suptitle("Airport Trips: 39.6% of volume → 54.8% of revenue",
                 fontsize=12, weight="bold", color=NAVY)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUT_DIR / "uber_airport_share.png")
    plt.close(fig)


def chart_zone_pareto(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    data = df.groupby("Pickup_Location")["Fare_Amount"].sum().div(1e5).round(2).sort_values(ascending=False)
    cum = data.cumsum() / data.sum() * 100
    ax2 = ax.twinx()
    ax.bar(data.index, data.values, color=BLUE, label="Revenue (₹L)")
    ax2.plot(data.index, cum.values, color=RED, marker="o", markersize=4, linewidth=1.5, label="Cumulative %")
    ax2.axhline(80, color="gray", linestyle="--", linewidth=0.8)
    _style(ax, "Zone Revenue Pareto", ylabel="Revenue (₹L)", xlabel="Pickup Zone")
    ax2.set_ylabel("Cumulative %", color=RED, fontsize=9)
    ax2.tick_params(axis="y", colors=RED, labelsize=8)
    for s in ax2.spines.values():
        s.set_visible(False)
    ax.tick_params(axis="x", labelsize=7)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "uber_zone_pareto.png")
    plt.close(fig)


def chart_rating_vs_fare(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=140)
    fig.patch.set_facecolor("white")
    df = df.copy()
    df["band"] = pd.cut(df["Rating"], bins=[0, 4.0, 4.4, 4.6, 4.8, 5.01],
                        labels=["<4.0", "4.0-4.4", "4.4-4.6", "4.6-4.8", "4.8-5.0"])
    data = df.groupby("band", observed=True)["Fare_Amount"].mean().round(2)
    bars = ax.bar(data.index.astype(str), data.values, color=ORANGE)
    _style(ax, "Average Fare by Driver Rating Band", ylabel="Avg Fare (₹)", xlabel="Rating Band")
    for b, v in zip(bars, data.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 4, f"₹{v:.0f}",
                ha="center", fontsize=9, weight="bold", color=TEXT)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "uber_rating_vs_fare.png")
    plt.close(fig)


def main() -> None:
    data_path = _resolve_data()
    df = pd.read_csv(data_path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chart_hourly_demand(df)
    chart_vehicle_revenue(df)
    chart_airport_share(df)
    chart_zone_pareto(df)
    chart_rating_vs_fare(df)
    print(f"Uber per-chart visuals written using {data_path.name}")


if __name__ == "__main__":
    main()
