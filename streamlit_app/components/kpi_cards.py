"""Streamlit KPI card component.

Thin compatibility wrapper: the dashboard now renders dark HTML cards from
:mod:`streamlit_app.common` (see :func:`kpi_card` / :func:`kpi_row`) so the
cards match the cockpit PNG renderer. This module re-exports those helpers so
existing imports keep working.
"""

from __future__ import annotations

from streamlit_app.common import format_inr, kpi_card, kpi_row

__all__ = ["format_inr", "kpi_card", "kpi_row"]

