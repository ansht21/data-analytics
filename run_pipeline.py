"""CLI entry point for the Weekly Revenue Reconciliation Engine.

Usage:
    python run_pipeline.py                 # full run + Excel workbook
    python run_pipeline.py --week W20      # focus one fiscal week
    python run_pipeline.py --no-excel      # clean + aggregate only
"""

from __future__ import annotations

import argparse

from src.config import load_settings
from src.data_loader import run_cleaning_pipeline
from src.logger import get_logger
from src.reconciliation.engine import aggregate_weekly
from src.reconciliation.variance_analyzer import add_wow_variance, detect_anomalies
from src.reporting.excel_dashboard import build_workbook
from src.utils.file_utils import ensure_dir

log = get_logger("run_pipeline")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    p = argparse.ArgumentParser(description="Weekly Revenue Reconciliation Engine")
    p.add_argument("--week", help="Fiscal week focus, e.g. W20")
    p.add_argument("--output-dir", help="Override reports output directory")
    p.add_argument("--no-excel", action="store_true", help="Skip Excel workbook")
    p.add_argument("--config", help="Path to settings.yaml")
    return p.parse_args()


def main() -> None:
    """Execute clean -> aggregate -> anomalies -> reports."""
    args = parse_args()
    settings = load_settings(args.config)
    if args.output_dir:
        settings.reports.output_dir = args.output_dir

    log.info("Pipeline start")
    df = run_cleaning_pipeline(settings)
    weekly = add_wow_variance(aggregate_weekly(
        df, min_days_for_full_week=settings.thresholds.min_days_for_full_week))
    anomalies = detect_anomalies(weekly, settings.thresholds)
    exc = df[df["financial_bucket"].isin(
        ["Cancellation Leakage", "Return Leakage", "Loss Leakage"])]

    if args.week:
        weekly = weekly[weekly["week_label"] == args.week]
        exc = exc[exc["week_label"] == args.week]

    period = (f"{weekly['week_label'].min()}-{weekly['week_label'].max()}"
              if len(weekly) else "empty")
    print(weekly[["week_label", "gross_revenue", "net_realized", "total_leakage",
                  "settled_clearance_rate", "clearance_rate", "wow_net_growth",
                  "total_orders"]]
          .to_string(index=False))
    print(f"\nAnomalies: {len(anomalies)}")
    if len(anomalies):
        print(anomalies.to_string(index=False))

    if not args.no_excel:
        out_dir = ensure_dir(settings.resolve(settings.reports.output_dir))
        exc_csv = out_dir / "exception_audit.csv"
        exc.drop(columns=["parsed_date"], errors="ignore").to_csv(exc_csv, index=False)
        path = build_workbook(settings, weekly, exc, period, df)
        print(f"\nWorkbook: {path}")
        print(f"Exceptions CSV: {exc_csv}")
    log.info("Pipeline done")


if __name__ == "__main__":
    main()
