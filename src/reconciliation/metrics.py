"""Headline KPI aggregation — the single source of truth for every surface.

The Streamlit dashboard, the Excel workbook and the PNG renderer all import
from this module, so a number can never disagree between them (the previous
version hardcoded values in the renderer, which silently drifted from the
engine output).

Two distinct coverage metrics are computed and always reported side by side:

* **Settled clearance %** = Net Realized / (Net Realized + true leakage).
  The audit metric: of the money that reached a final financial state, what
  share did we keep?
* **Gross coverage %** = Net Realized / Gross Invoiced.
  Low by construction when a large share of GMV is still In-Transit — this is
  settlement lag, not loss.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from .engine import CANCEL, IN_TRANSIT, LOSS, NET, PENDING, RETURN

LEAKAGE_BUCKETS = (CANCEL, RETURN, LOSS)


@dataclass(frozen=True)
class HeadlineKpis:
    """Portfolio-level KPIs for the full reconciliation period."""

    gross_revenue: float
    net_realized: float
    total_leakage: float
    cancellation_leakage: float
    return_leakage: float
    loss_leakage: float
    in_transit_value: float
    pending_value: float
    settled_base: float
    settled_clearance_rate: float
    gross_coverage_rate: float
    settlement_lag_rate: float
    total_lines: int
    unique_orders: int
    cancelled_orders: int
    avg_order_value: float
    weeks_active: int
    full_weeks: int
    partial_weeks: int

    def as_dict(self) -> dict[str, float | int]:
        """Return the KPI mapping for template/JSON use."""
        return asdict(self)


def _sum_bucket(df: pd.DataFrame, bucket: str) -> float:
    """Sum ``Amount`` for one financial bucket across the whole frame."""
    if "financial_bucket" not in df.columns or "Amount" not in df.columns:
        return 0.0
    return float(df.loc[df["financial_bucket"] == bucket, "Amount"].sum())


def compute_headline_kpis(df: pd.DataFrame, weekly: pd.DataFrame) -> HeadlineKpis:
    """Compute the headline KPI set from the cleaned frame and weekly KPIs.

    Args:
        df: Cleaned transaction frame.
        weekly: Weekly KPI frame from :func:`engine.aggregate_weekly`.

    Returns:
        A populated :class:`HeadlineKpis`.
    """
    gross = float(df["Amount"].sum()) if "Amount" in df.columns else 0.0
    net = _sum_bucket(df, NET)
    cancel = _sum_bucket(df, CANCEL)
    ret = _sum_bucket(df, RETURN)
    loss = _sum_bucket(df, LOSS)
    transit = _sum_bucket(df, IN_TRANSIT)
    pending = _sum_bucket(df, PENDING)
    leakage = cancel + ret + loss
    settled_base = net + leakage

    lines = int(len(df))
    unique_orders = int(df["Order ID"].nunique()) if "Order ID" in df.columns else lines
    cancelled_orders = (
        int((df["financial_bucket"] == CANCEL).sum())
        if "financial_bucket" in df.columns
        else 0
    )

    if "is_partial_week" in weekly.columns:
        partial_weeks = int(weekly["is_partial_week"].sum())
        full_weeks = int(len(weekly) - partial_weeks)
    else:
        partial_weeks = 0
        full_weeks = int(len(weekly))

    return HeadlineKpis(
        gross_revenue=round(gross, 2),
        net_realized=round(net, 2),
        total_leakage=round(leakage, 2),
        cancellation_leakage=round(cancel, 2),
        return_leakage=round(ret, 2),
        loss_leakage=round(loss, 2),
        in_transit_value=round(transit, 2),
        pending_value=round(pending, 2),
        settled_base=round(settled_base, 2),
        settled_clearance_rate=round((net / settled_base * 100) if settled_base else 0.0, 2),
        gross_coverage_rate=round((net / gross * 100) if gross else 0.0, 2),
        settlement_lag_rate=round(((transit + pending) / gross * 100) if gross else 0.0, 2),
        total_lines=lines,
        unique_orders=unique_orders,
        cancelled_orders=cancelled_orders,
        avg_order_value=round((gross / lines) if lines else 0.0, 2),
        weeks_active=int(len(weekly)),
        full_weeks=full_weeks,
        partial_weeks=partial_weeks,
    )


def leakage_by_dimension(
    df: pd.DataFrame,
    dimension: str,
    top_n: int = 10,
) -> pd.DataFrame:
    """Aggregate true-leakage revenue by one dimension.

    Args:
        df: Cleaned transaction frame.
        dimension: Column to group by (e.g. ``ship-state``, ``Category``).
        top_n: Number of groups to keep.

    Returns:
        Frame with ``dimension``, ``leakage_amount``, ``leakage_orders`` and
        ``leakage_share`` (share of total leakage), sorted descending.
    """
    empty = pd.DataFrame(
        columns=[dimension, "leakage_amount", "leakage_orders", "leakage_share"]
    )
    if dimension not in df.columns:
        return empty
    leak = df[df["financial_bucket"].isin(LEAKAGE_BUCKETS)]
    if not len(leak):
        return empty
    out = (
        leak.groupby(dimension)
        .agg(
            leakage_amount=("Amount", "sum"),
            leakage_orders=("Order ID", "nunique")
            if "Order ID" in leak.columns
            else ("Amount", "size"),
        )
        .reset_index()
        .sort_values("leakage_amount", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    total = float(out["leakage_amount"].sum()) or 1.0
    out["leakage_share"] = (out["leakage_amount"] / total * 100).round(2)
    return out


def category_revenue(df: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """Gross revenue and order volume by product category.

    Args:
        df: Cleaned transaction frame.
        top_n: Number of categories to keep.

    Returns:
        Frame with ``Category``, ``revenue``, ``orders`` and ``qty``.
    """
    if "Category" not in df.columns:
        return pd.DataFrame(columns=["Category", "revenue", "orders", "qty"])
    out = (
        df.groupby("Category")
        .agg(
            revenue=("Amount", "sum"),
            orders=("Order ID", "nunique") if "Order ID" in df.columns else ("Amount", "size"),
            qty=("Qty", "sum") if "Qty" in df.columns else ("Amount", "size"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    out["revenue"] = out["revenue"].round(2)
    return out


def fulfilment_settlement(df: pd.DataFrame) -> pd.DataFrame:
    """Gross vs net vs leakage split for each fulfilment channel.

    Args:
        df: Cleaned transaction frame.

    Returns:
        Frame with ``Fulfilment``, ``gross_revenue``, ``net_realized``,
        ``total_leakage`` and ``settled_clearance_rate``.
    """
    if "Fulfilment" not in df.columns:
        return pd.DataFrame(
            columns=[
                "Fulfilment",
                "gross_revenue",
                "net_realized",
                "total_leakage",
                "settled_clearance_rate",
            ]
        )
    rows: list[dict[str, object]] = []
    for name, group in df.groupby("Fulfilment"):
        gross = float(group["Amount"].sum())
        net = _sum_bucket(group, NET)
        leak = sum(_sum_bucket(group, b) for b in LEAKAGE_BUCKETS)
        base = net + leak
        rows.append(
            {
                "Fulfilment": str(name),
                "gross_revenue": round(gross, 2),
                "net_realized": round(net, 2),
                "total_leakage": round(leak, 2),
                "settled_clearance_rate": round((net / base * 100) if base else 0.0, 2),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("gross_revenue", ascending=False)
        .reset_index(drop=True)
    )
