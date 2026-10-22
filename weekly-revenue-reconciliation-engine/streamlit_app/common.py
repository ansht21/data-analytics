"""Shared Streamlit bootstrap: sys.path + cached data loading.

The dashboard is rebuilt around a single cached loader so the 11-step cleaning
pipeline runs **once per session**, not once per page render. The previous
version re-ran the whole pipeline on every widget interaction.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Settings, load_settings  # noqa: E402
from src.data_loader import load_processed  # noqa: E402
from src.reconciliation.engine import aggregate_weekly  # noqa: E402
from src.reconciliation.metrics import HeadlineKpis, compute_headline_kpis  # noqa: E402
from src.reconciliation.variance_analyzer import (  # noqa: E402
    add_wow_variance,
    detect_anomalies,
)

from streamlit_app.theme import CSS  # noqa: E402

LEAKAGE_BUCKETS = ["Cancellation Leakage", "Return Leakage", "Loss Leakage"]


@st.cache_data(show_spinner=False)
def load_all() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Settings]:
    """Load cleaned data + weekly KPIs + anomaly log (cached per session).

    Returns:
        Tuple of (cleaned_df, weekly_df, anomalies_df, settings).
    """
    settings = load_settings()
    df = load_processed(settings)
    weekly = add_wow_variance(
        aggregate_weekly(
            df,
            min_days_for_full_week=settings.thresholds.min_days_for_full_week,
        )
    )
    anomalies = detect_anomalies(weekly, settings.thresholds)
    return df, weekly, anomalies, settings


@st.cache_data(show_spinner=False)
def headline_kpis(df: pd.DataFrame, weekly: pd.DataFrame) -> HeadlineKpis:
    """Compute headline KPIs (cached).

    Args:
        df: Cleaned transaction frame.
        weekly: Weekly KPI frame.

    Returns:
        Populated :class:`HeadlineKpis`.
    """
    return compute_headline_kpis(df, weekly)


def inject_theme() -> None:
    """Inject the dark cockpit theme CSS into the running app."""
    st.markdown(CSS, unsafe_allow_html=True)


def format_inr(value: float, decimals: int = 2) -> str:
    """Format an INR amount using Indian short units (Cr / L / K).

    Args:
        value: Amount in rupees.
        decimals: Decimal places for the short form.

    Returns:
        Formatted string, e.g. ``₹7.86 Cr``.
    """
    if abs(value) >= 1e7:
        return f"₹{value / 1e7:,.{decimals}f} Cr"
    if abs(value) >= 1e5:
        return f"₹{value / 1e5:,.{decimals}f} L"
    if abs(value) >= 1e3:
        return f"₹{value / 1e3:,.{decimals}f} K"
    return f"₹{value:,.0f}"


def format_inr_millions(value: float) -> str:
    """Format an INR amount in millions (used inside chart labels)."""
    return f"₹{value / 1e6:,.2f}M"


def format_inr_lakhs(value: float) -> str:
    """Format an INR amount in lakhs (used inside chart labels)."""
    return f"₹{value / 1e5:,.1f}L"


def kpi_card(label: str, value: str, sub: str = "", delta: str = "",
             delta_up: bool | None = None) -> str:
    """Build one dark KPI card as HTML.

    Args:
        label: Uppercase card title.
        value: Pre-formatted primary value.
        sub: Supporting context line.
        delta: Optional delta badge text (e.g. ``▲ 4.2%``).
        delta_up: True for a positive delta, False for negative, None to hide.

    Returns:
        HTML string for the card.
    """
    badge = ""
    if delta and delta_up is not None:
        cls = "up" if delta_up else "down"
        badge = f'<div class="kpi-delta {cls}">{delta}</div>'
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>{sub_html}{badge}</div>'
    )


def kpi_row(cards: list[str], columns: int = 4) -> None:
    """Render a row of KPI cards across evenly-sized columns.

    Args:
        cards: Pre-built HTML card strings.
        columns: Number of columns per row.
    """
    for start in range(0, len(cards), columns):
        chunk = cards[start:start + columns]
        cols = st.columns(len(chunk))
        for col, card in zip(cols, chunk, strict=False):
            col.markdown(card, unsafe_allow_html=True)


def section_title(text: str) -> None:
    """Render a section header in the accent colour.

    Args:
        text: Header text.
    """
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def status_banner(title: str, sub: str) -> None:
    """Render the dark status banner used at the top of the cockpit.

    Args:
        title: Bold banner title.
        sub: Supporting line.
    """
    st.markdown(
        f'<div class="status-banner"><div class="sb-title">{title}</div>'
        f'<div class="sb-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def render_global_sidebar(active_key: str, df, weekly) -> None:
    """Render the bespoke sidebar and publish the global filter selection.

    Every page calls this so the grouped navigation and the filter controls
    are always present, and so the selections stay shared across pages.

    Args:
        active_key: Key of the page currently being viewed.
        df: Cleaned transaction frame.
        weekly: Weekly KPI frame.
    """
    # Imported lazily: the cockpit components import Streamlit, and this
    # module is imported by the pages themselves.
    from streamlit_app.components.cockpit import render_cockpit_sidebar

    weeks, categories, fulfilments, states = render_cockpit_sidebar(
        active_key=active_key,
        df=df,
        weekly=weekly,
        render_filters=render_sidebar_filters,
    )
    st.session_state["filters"] = {
        "weeks": weeks,
        "categories": categories,
        "fulfilments": fulfilments,
        "states": states,
    }


def apply_filters(
    df: pd.DataFrame,
    weeks: list[str],
    categories: list[str],
    fulfilments: list[str],
    states: list[str],
) -> pd.DataFrame:
    """Apply the global sidebar filters to the transaction frame.

    Every dashboard page uses this one function, so the filters shown in the
    sidebar genuinely drive every chart and table (the previous version built
    charts from the unfiltered frame, so the sidebar was decorative).

    Args:
        df: Cleaned transaction frame.
        weeks: Selected week labels (empty list = all weeks).
        categories: Selected categories (empty list = all).
        fulfilments: Selected fulfilment channels (empty list = all).
        states: Selected ship states (empty list = all).

    Returns:
        The filtered frame.
    """
    out = df
    if weeks:
        out = out[out["week_label"].isin(weeks)]
    if categories:
        out = out[out["Category"].isin(categories)]
    if fulfilments:
        out = out[out["Fulfilment"].isin(fulfilments)]
    if states:
        out = out[out["ship-state"].isin(states)]
    return out


def render_sidebar_filters(
    df: pd.DataFrame,
    weekly: pd.DataFrame,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Render the global filter sidebar and return the selections.

    Args:
        df: Cleaned transaction frame.
        weekly: Weekly KPI frame (for the week list).

    Returns:
        Tuple of (weeks, categories, fulfilments, states) selections.
    """
    # The bespoke sidebar already renders the group header ("Channels"),
    # so only the controls themselves are emitted here.
    weeks_all = weekly["week_label"].tolist()
    weeks = st.sidebar.multiselect(
        "Fiscal Week", weeks_all, default=weeks_all,
        help="Select the fiscal weeks included in every chart and table.",
    )
    cats_all = sorted(df["Category"].dropna().unique().tolist())
    categories = st.sidebar.multiselect("Category", cats_all, default=cats_all)
    ful_all = sorted(df["Fulfilment"].dropna().unique().tolist())
    fulfilments = st.sidebar.multiselect("Fulfilment", ful_all, default=ful_all)
    st_all = sorted(df["ship-state"].dropna().unique().tolist())
    states = st.sidebar.multiselect("Ship State", st_all, default=st_all)
    return weeks, categories, fulfilments, states


def filtered_weekly(weekly: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Recompute the weekly KPI frame for a filtered transaction set.

    Args:
        weekly: Full weekly KPI frame (used as a fallback).
        df: Filtered transaction frame.

    Returns:
        Weekly KPIs for the filtered rows, with WoW variance applied, or an
        empty frame if the filter produced no rows.
    """
    if not len(df):
        return weekly.iloc[0:0].copy()
    return add_wow_variance(aggregate_weekly(df))


