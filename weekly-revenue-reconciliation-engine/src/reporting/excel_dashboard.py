"""3-tab openpyxl workbook orchestrator: Executive, Trends, Audit."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

from ..config import Settings
from ..logger import get_logger
from ..utils.file_utils import ensure_dir
from .excel_cockpit import build_command_center
from .tabs_audit import build_audit_tab
from .tabs_trends import build_trends_tab

log = get_logger(__name__)


def _build_executive_tab(
    wb: Workbook, settings: Settings, weekly: pd.DataFrame, period: str,
    run_str: str, df: pd.DataFrame
):
    """Executive Dashboard tab: the dark "Command Center" cockpit.

    Args:
        wb: Target workbook (first sheet is reused).
        settings: Loaded settings (audit thresholds).
        weekly: Weekly KPI frame from the reconciliation engine.
        period: Human fiscal period label.
        run_str: Human-readable run timestamp.
        df: Cleaned transaction frame.

    Returns:
        The Executive sheet (chart destination).
    """
    ws = wb.active
    ws.title = "Executive Dashboard"
    build_command_center(ws, settings, weekly, df, period, run_str)
    return ws


def build_workbook(
    settings: Settings,
    weekly: pd.DataFrame,
    exceptions: pd.DataFrame,
    period_label: str,
    df: pd.DataFrame | None = None,
) -> Path:
    """Generate the 3-tab reconciliation workbook.

    Args:
        settings: Loaded settings (output dir + prefix).
        weekly: Weekly KPI frame (with ``wow_net_growth``).
        exceptions: Cancelled / returned / lost order detail rows.
        period_label: Human fiscal period string for the header.
        df: Optional cleaned transaction frame, used to compute headline KPIs
            for the executive cards. When omitted, the cards fall back to
            values aggregated from ``weekly`` alone.

    Returns:
        Path of the written ``.xlsx`` workbook.
    """
    wb = Workbook()
    now = datetime.now()
    run_str = now.strftime("%Y-%m-%d %H:%M")
    source = df if df is not None else pd.DataFrame()
    _build_executive_tab(wb, settings, weekly, period_label, run_str, source)
    build_trends_tab(wb, weekly)
    build_audit_tab(wb, exceptions, run_str)
    out_dir = ensure_dir(settings.resolve(settings.reports.output_dir))
    stamp = now.strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"{settings.reports.workbook_prefix}_{stamp}.xlsx"
    wb.save(path)
    log.info("Workbook written -> %s", path)
    return path

