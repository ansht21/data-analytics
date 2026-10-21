"""End-to-end integration: CSV -> clean -> aggregate -> reports."""

from __future__ import annotations

from pathlib import Path

from src.data_loader import run_cleaning_pipeline
from src.reconciliation.engine import aggregate_weekly
from src.reconciliation.variance_analyzer import add_wow_variance, detect_anomalies
from src.reporting.excel_dashboard import build_workbook


def test_full_pipeline(settings) -> None:
    """Synthetic CSV flows through every layer and produces artifacts."""
    df = run_cleaning_pipeline(settings)
    weekly = add_wow_variance(aggregate_weekly(df))
    anomalies = detect_anomalies(weekly, settings.thresholds)
    exc = df[df["financial_bucket"].isin(
        ["Cancellation Leakage", "Return Leakage", "Loss Leakage"])]

    assert len(df) == 8
    assert len(weekly) >= 2
    assert "wow_net_growth" in weekly.columns
    assert isinstance(anomalies, type(weekly))

    out_dir = Path(settings.resolve(settings.reports.output_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "exception_audit.csv"
    exc.to_csv(csv_path, index=False)
    assert csv_path.exists()

    xlsx = build_workbook(settings, weekly, exc, "synthetic")
    assert xlsx.exists() and xlsx.suffix == ".xlsx"

    processed = Path(settings.resolve(settings.data.processed_path))
    assert processed.exists()
