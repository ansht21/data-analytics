"""Week-over-Week variance & anomaly detection engine."""

from __future__ import annotations

import pandas as pd

from ..config import Thresholds
from ..logger import get_logger

log = get_logger(__name__)


def add_wow_variance(weekly: pd.DataFrame) -> pd.DataFrame:
    """Add WoW Net Revenue growth % vs the prior fiscal week.

    Args:
        weekly: Output of :func:`engine.aggregate_weekly`.

    Returns:
        Copy with ``wow_net_growth`` column (first week = 0.0).
    """
    out = weekly.copy()
    prior = out["net_realized"].shift(1)
    out["wow_net_growth"] = (((out["net_realized"] - prior) / prior) * 100).fillna(0.0).round(2)
    return out


def detect_anomalies(
    weekly: pd.DataFrame,
    thresholds: Thresholds,
    label_col: str = "week_label",
) -> pd.DataFrame:
    """Flag CRITICAL / WARNING / ALERT weeks per business rules.

    - CRITICAL: settled clearance rate below target. Measured against the
      **settled base** (Net Realized + true leakage), not gross invoiced, so
      the signal reflects real leakage rather than In-Transit settlement lag.
    - WARNING: leakage share of the settled base above target.
    - ALERT: WoW net revenue drop worse than threshold.

    Partial weeks (fewer observed days than a full week) are excluded: their
    truncated volumes would otherwise fire spurious CRITICAL/ALERT rules.

    Args:
        weekly: Weekly KPI frame (with ``wow_net_growth``).
        thresholds: Anomaly cut-offs from settings.
        label_col: Week label column.

    Returns:
        Anomaly log frame (one row per triggered rule).
    """
    records: list[dict[str, object]] = []
    for _, row in weekly.iterrows():
        if bool(row.get("is_partial_week", False)):
            continue
        week = str(row[label_col])
        settled = float(row.get("settled_clearance_rate", 0.0))
        if settled < thresholds.settled_clearance_critical_below:
            records.append(
                {"week_label": week, "severity": "CRITICAL",
                 "rule": f"Settled clearance {settled}% < {thresholds.settled_clearance_critical_below}%",
                 "value": settled}
            )
        leakage_share = 100.0 - settled
        if leakage_share > thresholds.leakage_warning_above:
            records.append(
                {"week_label": week, "severity": "WARNING",
                 "rule": f"Leakage share of settled base {leakage_share}% > {thresholds.leakage_warning_above}%",
                 "value": round(leakage_share, 2)}
            )
        if float(row.get("cancellation_rate", 0.0)) > thresholds.cancellation_warning_above:
            records.append(
                {"week_label": week, "severity": "WARNING",
                 "rule": f"Cancellation {row['cancellation_rate']}% > {thresholds.cancellation_warning_above}%",
                 "value": float(row["cancellation_rate"])}
            )
        if float(row.get("wow_net_growth", 0.0)) < thresholds.wow_drop_alert_below:
            records.append(
                {"week_label": week, "severity": "ALERT",
                 "rule": f"WoW Net {row['wow_net_growth']}% < {thresholds.wow_drop_alert_below}%",
                 "value": float(row["wow_net_growth"])}
            )
    anomalies = pd.DataFrame(records, columns=["week_label", "severity", "rule", "value"])
    log.info("Detected %d anomaly triggers", len(anomalies))
    return anomalies
