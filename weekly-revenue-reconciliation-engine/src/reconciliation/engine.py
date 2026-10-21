"""Weekly aggregation & KPI math: Gross vs Net, leakage, clearance."""

from __future__ import annotations

import pandas as pd

from ..logger import get_logger

log = get_logger(__name__)

NET = "Net Realized"
CANCEL = "Cancellation Leakage"
RETURN = "Return Leakage"
LOSS = "Loss Leakage"
IN_TRANSIT = "In-Transit"
PENDING = "Pending"

LEAKAGE_BUCKETS = (CANCEL, RETURN, LOSS)


def _bucket_sum(group: pd.DataFrame, bucket: str) -> float:
    """Sum ``Amount`` for one financial bucket inside a week group."""
    mask = group["financial_bucket"] == bucket
    return float(group.loc[mask, "Amount"].sum())


def aggregate_weekly(
    df: pd.DataFrame,
    label_col: str = "week_label",
    year_col: str = "fiscal_year",
    week_col: str = "fiscal_week",
    min_days_for_full_week: int = 7,
) -> pd.DataFrame:
    """Aggregate cleaned transactions to one row per fiscal week.

    Computes two distinct revenue-coverage metrics, because conflating them
    is the classic mistake in marketplace reconciliation:

    * ``clearance_rate`` — Net Realized ÷ **Gross Invoiced**. Low by
      construction whenever a large share of GMV is still In-Transit or
      Pending at export time. This is *settlement lag*, not loss.
    * ``settled_clearance_rate`` — Net Realized ÷ **Settled Base**
      (Net Realized + true leakage). This is the audit metric: of the money
      that reached a final financial state, what share did we actually keep?

    Also flags ``is_partial_week`` for weeks with fewer than
    ``min_days_for_full_week`` distinct transaction days (window edges), so
    downstream anomaly logic can avoid false alarms on truncated weeks.

    Args:
        df: Cleaned transaction frame with ``financial_bucket``.
        label_col: Week label column (``W13`` …).
        year_col: ISO year column.
        week_col: ISO week integer column.
        min_days_for_full_week: Distinct days required for a full week.

    Returns:
        Weekly KPI frame sorted chronologically.
    """
    rows: list[dict[str, object]] = []
    has_dates = "parsed_date" in df.columns
    for (label, year, week), group in df.groupby([label_col, year_col, week_col]):
        gross = float(group["Amount"].sum())
        net = _bucket_sum(group, NET)
        cancel_rev = _bucket_sum(group, CANCEL)
        return_rev = _bucket_sum(group, RETURN)
        loss_rev = _bucket_sum(group, LOSS)
        leakage = cancel_rev + return_rev + loss_rev
        transit = _bucket_sum(group, IN_TRANSIT)
        pending = _bucket_sum(group, PENDING)
        settled_base = net + leakage
        orders = int(len(group))
        cancelled_orders = int((group["financial_bucket"] == CANCEL).sum())
        unique_orders = int(group["Order ID"].nunique()) if "Order ID" in group.columns else orders
        days_observed = (
            int(group["parsed_date"].dt.date.nunique()) if has_dates else min_days_for_full_week
        )
        rows.append(
            {
                label_col: label,
                year_col: int(year),
                week_col: int(week),
                "gross_revenue": round(gross, 2),
                "net_realized": round(net, 2),
                "cancellation_leakage": round(cancel_rev, 2),
                "return_leakage": round(return_rev, 2),
                "loss_leakage": round(loss_rev, 2),
                "total_leakage": round(leakage, 2),
                "in_transit_value": round(transit, 2),
                "pending_value": round(pending, 2),
                "settled_base": round(settled_base, 2),
                "clearance_rate": round((net / gross * 100) if gross else 0.0, 2),
                "settled_clearance_rate": round(
                    (net / settled_base * 100) if settled_base else 0.0, 2
                ),
                "cancellation_rate": round(
                    (cancelled_orders / orders * 100) if orders else 0.0, 2
                ),
                "total_orders": orders,
                "unique_orders": unique_orders,
                "cancelled_orders": cancelled_orders,
                "avg_order_value": round((gross / orders) if orders else 0.0, 2),
                "days_observed": days_observed,
                "is_partial_week": days_observed < min_days_for_full_week,
            }
        )
    weekly = pd.DataFrame(rows).sort_values([year_col, week_col]).reset_index(drop=True)
    log.info("Aggregated %d fiscal weeks", len(weekly))
    return weekly
