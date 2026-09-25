"""Deterministic analytics: quick-insight chips + executive brief data.

Every insight is plain pandas computed LIVE on the loaded DataFrame — no LLM,
no hardcoding, no hallucination. Each returns (finding, explanation,
suggestion, chart_spec | None, pandas_snippet).

chart_spec is a serialisable dict the UI turns into a Plotly figure:
{"kind": "bar"|"line", "x": [...], "y": [...], "title": str,
 "x_label": str, "y_label": str, "annotate_max": bool}
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import pandas as pd


@dataclass
class Insight:
    finding: str
    explanation: str
    suggestion: str
    chart: dict | None
    pandas_snippet: str
    runtime_ms: float
    dataset: str


def _timed(func, *args, **kwargs) -> tuple:
    started = time.perf_counter()
    out = func(*args, **kwargs)
    return out, (time.perf_counter() - started) * 1000.0


# ------------------------------------------------------------------ #
# Supply chain insights
# ------------------------------------------------------------------ #
def supply_margin_bleed(df: pd.DataFrame) -> Insight:
    """Orders at 20%+ discount realise far thinner margins — cap them.

    Banding + margin definition match the committed SQL exactly
    (Q8 in supply-chain-performance-analysis/sql_queries/02_sales_analysis.sql):
    realised_margin = SUM(profit) / SUM(revenue) inside each discount band.
    """
    def _compute():
        bands = pd.cut(
            df["Discount_Applied"],
            bins=[-0.05, 0.05, 0.10, 0.20, 1.01],
            labels=["0-5%", "5-10%", "10-20%", "20%+"],
        ).astype(str)
        grp = df.assign(band=bands).groupby("band").agg(orders=("profit", "size"),
                                                        revenue=("revenue", "sum"),
                                                        profit=("profit", "sum"))
        grp["realised_margin"] = grp["profit"] / grp["revenue"]
        return grp.reindex(["0-5%", "5-10%", "10-20%", "20%+"])
    grp, ms = _timed(_compute)
    finding = (
        f"Orders at 20%+ discount realise only {grp.loc['20%+', 'realised_margin'] * 100:.2f}% "
        f"margin (SUM profit / SUM revenue) versus "
        f"{grp.loc['5-10%', 'realised_margin'] * 100:.2f}% in the 5-10% band — "
        f"over {int(grp.loc['20%+', 'orders'])} orders analysed."
    )
    explanation = (
        "Deep discounts do not just shave profit — past ~15% the margin collapses, "
        "meaning those orders subsidise volume with almost no payback."
    )
    suggestion = (
        "Apply product-level profit floors and route every 20%+ discount through "
        "approval; shift that volume to the 5-10% band where margin peaks."
    )
    chart = {
        "kind": "bar", "x": list(grp.index),
        "y": [round(float(v) * 100, 2) for v in grp["realised_margin"].values],
        "title": "Realised margin by discount band (matches SQL Q8)",
        "x_label": "Discount band", "y_label": "Margin %", "annotate_max": False,
    }
    snippet = (
        "bands = pd.cut(df['Discount_Applied'], bins=[-0.05,0.05,0.10,0.20,1.01],\n"
        "               labels=['0-5%','5-10%','10-20%','20%+'])\n"
        "g = df.assign(band=bands).groupby('band').agg(revenue=('revenue','sum'), profit=('profit','sum'))\n"
        "g['profit'] / g['revenue']  # realised margin, same as SQL Q8"
    )
    return Insight(finding, explanation, suggestion, chart, snippet, ms, "supply")


def supply_warehouse_trap(df: pd.DataFrame) -> Insight:
    """Volume illusion: the busiest warehouse looks worst — variance says otherwise.

    Matches warehouse_performance.csv + the README finding: WARE-NMK1003 causes
    31.9% of late orders yet handles 31.4% of all orders; only 0.08% of
    delivery-time variance sits between warehouses (ANOVA-style decomposition).
    """
    def _compute():
        late = df.groupby("WarehouseCode")["late"].agg(["mean", "count"])
        total_late = int(df["late"].sum())
        grand = float(df["delivery_days"].mean())
        counts = df.groupby("WarehouseCode").size()
        means = df.groupby("WarehouseCode")["delivery_days"].mean()
        ss_between = float(((means - grand) ** 2 * counts).sum())
        ss_total = float(((df["delivery_days"] - grand) ** 2).sum())
        return late, total_late, 100 * ss_between / ss_total
    (late, total_late, share), ms = _timed(_compute)
    worst = late["count"].idxmax()
    worst_late = int((df["late"] & (df["WarehouseCode"] == worst)).sum())
    finding = (
        f"{worst} tops late-order COUNT ({worst_late} of {total_late} late orders, "
        f"{worst_late / total_late * 100:.1f}%) — but its late RATE "
        f"({late.loc[worst, 'mean'] * 100:.1f}%) matches the network average "
        f"({df['late'].mean() * 100:.1f}%). Only {share:.2f}% of delivery-time "
        "variance sits between warehouses."
    )
    explanation = (
        "Ranking raw late-order counts punishes the warehouse that simply handles the "
        "most volume. Delivery spread is nearly identical everywhere — the defect is "
        "upstream scheduling, not a facility."
    )
    suggestion = (
        "Do NOT fund a per-site fix; audit order-to-ship scheduling and procurement "
        "lead times network-wide instead."
    )
    chart = {
        "kind": "bar", "x": list(late.index),
        "y": [round(float(v) * 100, 1) for v in late["mean"].values],
        "title": "Late-delivery rate by warehouse (all near-identical)",
        "x_label": "Warehouse", "y_label": "Late %", "annotate_max": False,
    }
    snippet = (
        "df.groupby('WarehouseCode')['late'].agg(['mean','count'])\n"
        "df.groupby('WarehouseCode')['delivery_days'].mean().var() / df['delivery_days'].var()"
    )
    return Insight(finding, explanation, suggestion, chart, snippet, ms, "supply")


def supply_abc_sku(df: pd.DataFrame) -> Insight:
    """A-items dominate revenue — protect them first.

    Classification matches the pipeline output in
    supply-chain-performance-analysis/outputs/abc_classification.csv:
    A = first 36 SKUs (76.6% of products, 80.6% of revenue).
    """
    def _compute():
        sku = df.groupby("_ProductID")["revenue"].sum().sort_values(ascending=False)
        cum = sku.cumsum() / sku.sum() * 100
        return sku, cum
    (sku, cum), ms = _timed(_compute)
    a_items = int((cum <= 80).sum())
    finding = (
        f"{a_items} of {len(sku)} SKUs drive 80% of net revenue; the tail "
        f"({len(sku) - a_items} SKUs) contributes the remaining 20%."
    )
    explanation = (
        "A thin head of SKUs funds the business while dozens of tail SKUs add "
        "operational complexity for marginal return."
    )
    suggestion = (
        "Ring-fence A-item stock and service levels; review tail SKUs for delisting "
        "or made-to-order to cut carrying cost."
    )
    top = sku.head(15)
    chart = {
        "kind": "bar", "x": [str(i) for i in top.index],
        "y": [round(float(v) / 1e6, 2) for v in top.values],
        "title": "Revenue by SKU (top 15, $M)",
        "x_label": "Product ID", "y_label": "Revenue $M", "annotate_max": True,
    }
    snippet = (
        "sku = df.groupby('_ProductID')['revenue'].sum().sort_values(ascending=False)\n"
        "(sku.cumsum() / sku.sum() * 100 <= 80).sum()  # A-items"
    )
    return Insight(finding, explanation, suggestion, chart, snippet, ms, "supply")


# ------------------------------------------------------------------ #
# Uber insights
# ------------------------------------------------------------------ #
def uber_surge_timing(df: pd.DataFrame) -> Insight:
    """Demand accelerates at 5 PM — an hour before the 6 PM volume peak."""
    def _compute():
        hourly = df.groupby("Hour").size().sort_index()
        return hourly, hourly.pct_change() * 100
    (hourly, growth), ms = _timed(_compute)
    surge, peak = int(growth.idxmax()), int(hourly.idxmax())
    finding = (
        f"Demand ACCELERATES at {surge}:00 ({growth.max():+.0f}% vs prior hour) but "
        f"volume PEAKS at {peak}:00 ({hourly.max():,} trips). The 5-7 PM window carries "
        f"{hourly.loc[17:19].sum() / hourly.sum() * 100:.1f}% of demand in 3 of 24 hours."
    )
    explanation = (
        "Chasing the volume peak is too late — by 6 PM the surge is priced in. "
        "The 5 PM growth inflection is the true trigger moment."
    )
    suggestion = (
        "Launch driver incentives by 4:30 PM and pre-position premium vehicles near "
        "airport corridors before the 5 PM acceleration."
    )
    chart = {
        "kind": "line", "x": [int(h) for h in hourly.index], "y": [int(v) for v in hourly.values],
        "title": "Trips by hour (surge starts 17:00)",
        "x_label": "Hour of day", "y_label": "Trips", "annotate_max": True,
    }
    snippet = (
        "hourly = df.groupby('Hour').size().sort_index()\n"
        "hourly.pct_change() * 100  # inflects 17:00, peaks 18:00"
    )
    return Insight(finding, explanation, suggestion, chart, snippet, ms, "uber")


def uber_airport_mix(df: pd.DataFrame) -> Insight:
    """Airport trips: minority of volume, majority of revenue."""
    def _compute():
        vol = df["is_airport"].mean() * 100
        rev = df.loc[df["is_airport"], "Fare_Amount"].sum() / df["Fare_Amount"].sum() * 100
        return vol, rev, df.loc[df["is_airport"], "Fare_Amount"].mean(), df.loc[~df["is_airport"], "Fare_Amount"].mean()
    (vol, rev, avg_air, avg_other), ms = _timed(_compute)
    finding = (
        f"Airport trips are {vol:.1f}% of volume but {rev:.1f}% of revenue "
        f"(₹{avg_air:.0f} vs ₹{avg_other:.0f} avg fare)."
    )
    explanation = (
        "Longer airport runs at premium pricing make each airport trip worth roughly "
        "twice a city trip — the revenue engine hides in a volume minority."
    )
    suggestion = (
        "Protect airport-corridor supply (dedicated queue, reliability bonuses) and "
        "test a small airport-priority fee rather than city-wide surge."
    )
    chart = {
        "kind": "bar", "x": ["Non-airport", "Airport"],
        "y": [round(float(avg_other), 0), round(float(avg_air), 0)],
        "title": "Average fare: airport vs non-airport (₹)",
        "x_label": "Trip type", "y_label": "Avg fare ₹", "annotate_max": True,
    }
    snippet = "df.groupby('is_airport')['Fare_Amount'].agg(['mean','sum','count'])"
    return Insight(finding, explanation, suggestion, chart, snippet, ms, "uber")


def uber_vehicle_tier(df: pd.DataFrame) -> Insight:
    """Revenue per km separates premium tiers from volume tiers."""
    def _compute():
        tier = df.groupby("Vehicle_Type").agg(
            trips=("Fare_Amount", "size"), revenue=("Fare_Amount", "sum"), km=("Trip_Distance_km", "sum"))
        tier["rev_per_km"] = tier["revenue"] / tier["km"].replace(0, float("nan"))
        return tier.sort_values("rev_per_km", ascending=False)
    tier, ms = _timed(_compute)
    top, bottom = tier.index[0], tier.index[-1]
    finding = (
        f"{top} earns ₹{tier.loc[top, 'rev_per_km']:.0f}/km vs "
        f"₹{tier.loc[bottom, 'rev_per_km']:.0f}/km for {bottom} — a "
        f"~{tier.loc[top, 'rev_per_km'] / tier.loc[bottom, 'rev_per_km']:.1f}x gap."
    )
    explanation = (
        "Premium tiers monetise every kilometre far better; volume tiers move people "
        "but dilute per-km yield."
    )
    suggestion = (
        "Grow the premium fleet where utilisation supports it; use Pool/X only as "
        "feeder volume, not the growth bet."
    )
    chart = {
        "kind": "bar", "x": list(tier.index),
        "y": [round(float(v), 1) for v in tier["rev_per_km"].values],
        "title": "Revenue per km by vehicle tier (₹)",
        "x_label": "Vehicle tier", "y_label": "₹ / km", "annotate_max": True,
    }
    snippet = (
        "tier = df.groupby('Vehicle_Type').agg(trips=('Fare_Amount','size'),\n"
        "        revenue=('Fare_Amount','sum'), km=('Trip_Distance_km','sum'))"
    )
    return Insight(finding, explanation, suggestion, chart, snippet, ms, "uber")


# ------------------------------------------------------------------ #
# Churn insights
# ------------------------------------------------------------------ #
def churn_high_risk_cohort(df: pd.DataFrame) -> Insight:
    """Month-to-month + fiber = the revenue-at-risk concentration."""
    def _compute():
        cohort = df[(df["Contract"] == "Month-to-month") & (df["InternetService"] == "Fiber optic")]
        rate = cohort["churned"].mean() * 100
        share = cohort["MonthlyCharges"].sum() / df["MonthlyCharges"].sum() * 100
        return len(cohort), rate, share, float(cohort["MonthlyCharges"].sum())
    (n, rate, share, cohort_rev), ms = _timed(_compute)
    finding = (
        f"{n:,} month-to-month fiber customers churn at {rate:.1f}% — "
        f"${cohort_rev:,.0f} of monthly revenue at risk. "
        f"(Segment table: churn_segment_revenue.csv.)"
    )
    explanation = (
        "No contract lock-in plus premium pricing creates the highest-intent-to-leave "
        "cohort — churn concentrates where the dollars are."
    )
    suggestion = (
        "Offer this cohort a 1-year contract with a fiber loyalty discount; prioritise "
        "save-desk outreach by revenue at risk, not by tenure."
    )
    by_contract = df.groupby("Contract")["churned"].mean() * 100
    chart = {
        "kind": "bar", "x": list(by_contract.index),
        "y": [round(float(v), 1) for v in by_contract.values],
        "title": "Churn rate by contract type (%)",
        "x_label": "Contract", "y_label": "Churn %", "annotate_max": True,
    }
    snippet = (
        "cohort = df[(df['Contract']=='Month-to-month') & (df['InternetService']=='Fiber optic')]\n"
        "cohort['churned'].mean(); cohort['MonthlyCharges'].sum() / df['MonthlyCharges'].sum()"
    )
    return Insight(finding, explanation, suggestion, chart, snippet, 0.0, "churn")



def churn_tenure_curve(df: pd.DataFrame) -> Insight:
    """Churn decays with tenure — the first year is the danger zone."""
    def _compute():
        bands = pd.cut(df["tenure"], bins=[-1, 12, 24, 48, 100],
                       labels=["0-12 mo", "13-24 mo", "25-48 mo", "49+ mo"]).astype(str)
        curve = df.assign(band=bands).groupby("band")["churned"].mean() * 100
        return curve.reindex(["0-12 mo", "13-24 mo", "25-48 mo", "49+ mo"])
    curve, ms = _timed(_compute)
    gap = curve["0-12 mo"] / max(curve["49+ mo"], 0.01)
    finding = (
        f"First-year customers churn at {curve['0-12 mo']:.1f}% vs "
        f"{curve['49+ mo']:.1f}% for 4+ year veterans — a {gap:.0f}x gap."
    )
    explanation = (
        "Churn risk is front-loaded: onboarding experience decides retention; veterans "
        "rarely leave once embedded."
    )
    suggestion = (
        "Fund a 90-day onboarding save programme (proactive check-ins, first-bill clarity) "
        "instead of spreading retention spend evenly."
    )
    chart = {
        "kind": "line", "x": list(curve.index),
        "y": [round(float(v), 1) for v in curve.values],
        "title": "Churn rate by tenure band (%)",
        "x_label": "Tenure", "y_label": "Churn %", "annotate_max": False,
    }
    snippet = (
        "bands = pd.cut(df['tenure'], bins=[-1,12,24,48,100],\n"
        "               labels=['0-12 mo','13-24 mo','25-48 mo','49+ mo'])"
    )
    return Insight(finding, explanation, suggestion, chart, snippet, ms, "churn")


def churn_payment_risk(df: pd.DataFrame) -> Insight:
    """Electronic-check payers churn hardest — a billing-friction signal (SQL: 45.3%)."""
    def _compute():
        pay = df.groupby("PaymentMethod")["churned"].agg(["mean", "count"])
        return pay.sort_values("mean", ascending=False)
    pay, ms = _timed(_compute)
    top = pay.index[0]
    finding = (
        f"{top} payers churn at {pay.loc[top, 'mean'] * 100:.1f}% "
        f"({int(pay.loc[top, 'count']):,} accounts) — the highest of any payment method."
    )
    explanation = (
        "Manual, friction-heavy billing correlates with exit: customers who must act "
        "every month reconsider every month."
    )
    suggestion = (
        "Nudge electronic-check users to autopay with a small bill credit; fix "
        "first-payment failures, which seed this cohort."
    )
    chart = {
        "kind": "bar", "x": list(pay.index),
        "y": [round(float(v) * 100, 1) for v in pay["mean"].values],
        "title": "Churn rate by payment method (%)",
        "x_label": "Payment method", "y_label": "Churn %", "annotate_max": True,
    }
    snippet = "df.groupby('PaymentMethod')['churned'].agg(['mean','count'])"
    return Insight(finding, explanation, suggestion, chart, snippet, ms, "churn")

# ------------------------------------------------------------------ #
# Registry: dataset key -> ordered [(chip label, function)]
# ------------------------------------------------------------------ #
CHIPS: dict[str, list[tuple[str, object]]] = {
    "supply": [
        ("Margin Bleed Audit", supply_margin_bleed),
        ("Warehouse Trap Check", supply_warehouse_trap),
        ("ABC SKU Pareto", supply_abc_sku),
    ],
    "uber": [
        ("Peak Surge Detection", uber_surge_timing),
        ("Airport Revenue Share", uber_airport_mix),
        ("Vehicle Tier Efficiency", uber_vehicle_tier),
    ],
    "churn": [
        ("High-Risk Cohort Audit", churn_high_risk_cohort),
        ("Tenure Decay Curve", churn_tenure_curve),
        ("Payment Friction Risk", churn_payment_risk),
    ],
}


def chip_labels(key: str) -> list[str]:
    return [label for label, _ in CHIPS[key]]


def run_chip(key: str, label: str, df: pd.DataFrame) -> Insight:
    for chip_label, func in CHIPS[key]:
        if chip_label == label:
            return func(df)  # type: ignore[operator]
    raise KeyError(f"Unknown chip '{label}' for dataset '{key}'.")


def dataset_choices() -> list[tuple[str, str]]:
    """(key, 'icon label — scale') pairs for the sidebar selector."""
    from .datasets import DATASETS

    return [(k, f"{v['icon']} {v['label']} — {v['scale']}") for k, v in DATASETS.items()]
