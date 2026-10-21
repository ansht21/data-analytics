"""Typed YAML configuration parser for the reconciliation engine.

All paths, thresholds, bucket maps and report settings flow through
:class:`Settings` so no module hardcodes business parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, TypeVar

import yaml

_T = TypeVar("_T")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS = PROJECT_ROOT / "config" / "settings.yaml"


def _build(cls: type[_T], raw: dict[str, Any] | None) -> _T:
    """Instantiate a settings dataclass, ignoring unknown YAML keys.

    Keeps older/partial ``settings.yaml`` files loadable instead of raising
    ``TypeError`` on a stray key.
    """
    allowed = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    payload = {k: v for k, v in (raw or {}).items() if k in allowed}
    return cls(**payload)


@dataclass
class DataConfig:
    """Raw / processed / archive dataset locations."""

    raw_path: str = "data/raw/Amazon_Sale_Report.csv"
    processed_path: str = "data/processed/cleaned_transactions.parquet"
    archive_dir: str = "data/archive"


@dataclass
class CleaningConfig:
    """Column handling and defaulting rules for ingestion."""

    drop_columns: list[str] = field(default_factory=lambda: ["index", "New", "PendingS"])
    date_column: str = "Date"
    amount_column: str = "Amount"
    default_currency: str = "INR"
    unknown_state: str = "UNKNOWN"


@dataclass
class FiscalConfig:
    """Column names produced by fiscal calendar tagging."""

    week_column: str = "fiscal_week"
    year_column: str = "fiscal_year"
    label_column: str = "week_label"


@dataclass
class Thresholds:
    """Anomaly detection thresholds (percent units).

    ``settled_clearance_critical_below`` is the audit target applied to the
    **settled** base (Net Realized + true leakage) — i.e. of the money that
    actually reached a final state, what share did we keep? The gross-based
    figure (``clearance_rate``) is reported separately as *settlement lag*
    because most GMV in this export is still In-Transit.
    """

    settled_clearance_critical_below: float = 70.0
    leakage_warning_above: float = 35.0
    cancellation_warning_above: float = 15.0
    wow_drop_alert_below: float = -10.0
    min_days_for_full_week: int = 7


@dataclass
class ReportsConfig:
    """Excel workbook destination settings."""

    output_dir: str = "reports"
    workbook_prefix: str = "Revenue_Reconciliation_Dashboard"


@dataclass
class Settings:
    """Root settings object assembled from ``settings.yaml``."""

    data: DataConfig = field(default_factory=DataConfig)
    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    fiscal: FiscalConfig = field(default_factory=FiscalConfig)
    buckets: dict[str, list[str]] = field(default_factory=dict)
    thresholds: Thresholds = field(default_factory=Thresholds)
    reports: ReportsConfig = field(default_factory=ReportsConfig)
    raw: dict[str, Any] = field(default_factory=dict)

    def resolve(self, relative: str) -> Path:
        """Resolve a repo-relative path against the project root."""
        return (PROJECT_ROOT / relative).resolve()


def load_settings(path: str | Path | None = None) -> Settings:
    """Load :class:`Settings` from a YAML file.

    Args:
        path: Optional override path; defaults to ``config/settings.yaml``.

    Returns:
        Populated :class:`Settings` instance.
    """
    cfg_path = Path(path) if path else DEFAULT_SETTINGS
    with open(cfg_path, encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    data = _build(DataConfig, raw.get("data", {}))
    cleaning = _build(CleaningConfig, raw.get("cleaning", {}))
    fiscal = _build(FiscalConfig, raw.get("fiscal", {}))
    thresholds = _build(Thresholds, raw.get("thresholds", {}))
    reports = _build(ReportsConfig, raw.get("reports", {}))
    return Settings(
        data=data,
        cleaning=cleaning,
        fiscal=fiscal,
        buckets=raw.get("buckets", {}),
        thresholds=thresholds,
        reports=reports,
        raw=raw,
    )
