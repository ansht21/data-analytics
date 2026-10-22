"""Cockpit layout components for the "Midnight Deck" dashboard.

Pure HTML builders: every function returns a string of markup that is
rendered with ``st.markdown(..., unsafe_allow_html=True)``. Keeping them
separate from the data layer means the visual design can change without
touching the reconciliation engine.

The layout mirrors the reference CRM mock (sidebar nav -> hero KPI row ->
annotated area chart + right rail -> donut / gauge row) but uses a
deep-navy / sky-cyan / emerald palette instead of the mock's purple-magenta.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_app.theme import (
    ACCENT_DEEP,
)

__all__ = [
    "hero_card",
    "stat_pill",
    "panel_open",
    "panel_close",
    "nav_item",
    "nav_section",
    "nav_brand",
    "profile_block",
    "cta_button",
    "nav_sub",
    "render_cockpit_sidebar",
    "render_export_button",
    "PAGES",
]


# The real app pages, keyed by a short slug. ``path`` is relative to the
# entrypoint (``streamlit_app/Dashboard.py``) so ``st.page_link`` resolves it.
PAGES: list[dict[str, str]] = [
    {"key": "overview", "label": "Overview", "icon": "◈", "path": ""},
    {"key": "executive", "label": "Executive Summary", "icon": "▤",
     "path": "pages/1_Executive_Summary.py"},
    {"key": "trends", "label": "Weekly Trends", "icon": "◹",
     "path": "pages/2_Weekly_Trends.py"},
    {"key": "leakage", "label": "Leakage Analysis", "icon": "◈",
     "path": "pages/3_Leakage_Analysis.py"},
    {"key": "audit", "label": "Exception Audit", "icon": "▣",
     "path": "pages/4_Exception_Audit.py"},
]

# Sidebar grouping, mirroring the reference mock's grouped navigation.
NAV_SECTIONS: list[tuple[str, list[str]]] = [
    ("Profile", ["overview"]),
    ("Workspace", ["executive", "trends", "leakage", "audit"]),
]


def hero_card(label: str, value: str, sub: str, foot: str = "",
              alt: bool = False, unit: str = "") -> str:
    """Build one large gradient KPI card.

    Args:
        label: Small uppercase label above the value.
        value: Primary figure, already formatted.
        sub: Short descriptor under the value.
        foot: Optional footnote line.
        alt: Use the emerald gradient instead of the cyan one.
        unit: Optional unit suffix rendered smaller next to the value.

    Returns:
        HTML string for the card.
    """
    cls = "hero-card hero-alt" if alt else "hero-card"
    unit_html = f'<span class="unit">{unit}</span>' if unit else ""
    foot_html = f'<div class="hero-foot">{foot}</div>' if foot else ""
    return (
        f'<div class="{cls}">'
        f'<div class="hero-label">{label}</div>'
        f'<div class="hero-value">{value}{unit_html}</div>'
        f'<div class="hero-sub">{sub}</div>'
        f"{foot_html}"
        f"</div>"
    )


def stat_pill(icon: str, label: str, value: str, tone: str = "") -> str:
    """Build one compact stat pill (icon + label + value chip).

    Args:
        icon: Single character or emoji shown in the coloured square.
        label: Pill label.
        value: Value chip text.
        tone: Optional suffix - ``pos``, ``warn`` or ``neg`` - for chip colour.

    Returns:
        HTML string for the pill.
    """
    chip_cls = f"pill-value {tone}".strip()
    return (
        f'<div class="pill">'
        f'<div class="pill-left">'
        f'<div class="pill-dot" style="background:{ACCENT_DEEP}">{icon}</div>'
        f'<div class="pill-label">{label}</div></div>'
        f'<div class="{chip_cls}">{value}</div>'
        f"</div>"
    )


def panel_open(title: str, sub: str = "") -> str:
    """Open a chart panel card.

    Args:
        title: Panel title.
        sub: Optional subtitle under the title.

    Returns:
        HTML string opening the panel.
    """
    sub_html = f'<div class="panel-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="panel">'
        f'<div class="panel-title">{title}</div>{sub_html}'
    )


def panel_close() -> str:
    """Close a chart panel card.

    Returns:
        HTML string closing the panel.
    """
    return "</div>"


def nav_brand(title: str, accent_word: str = "") -> str:
    """Build the sidebar brand block.

    Args:
        title: Brand text.
        accent_word: Optional trailing word rendered in the accent colour.

    Returns:
        HTML string for the brand block.
    """
    tail = f' <span>{accent_word}</span>' if accent_word else ""
    return f'<div class="nav-brand">{title}{tail}</div>'


def nav_section(title: str) -> str:
    """Build a sidebar navigation section header.

    Args:
        title: Section title (rendered uppercase).

    Returns:
        HTML string for the section header.
    """
    return f'<div class="nav-section">{title}</div>'


def nav_item(label: str, icon: str = "", active: bool = False) -> str:
    """Build a sidebar navigation row.

    Args:
        label: Item label.
        icon: Optional icon glyph.
        active: Render the item in the active state.

    Returns:
        HTML string for the nav row.
    """
    cls = "nav-item active" if active else "nav-item"
    icon_html = f'<span class="ni-icon">{icon}</span>' if icon else ""
    return f'<div class="{cls}">{icon_html}<span>{label}</span></div>'


def nav_sub(label: str, active: bool = False) -> str:
    """Build an indented sidebar sub-item.

    Args:
        label: Sub-item label.
        active: Render the sub-item in the active state.

    Returns:
        HTML string for the sub-item.
    """
    cls = "nav-sub active" if active else "nav-sub"
    return f'<div class="{cls}">{label}</div>'


def profile_block(name: str, role: str, initials: str) -> str:
    """Build the sidebar user-profile block.

    Args:
        name: Display name.
        role: Job title / role.
        initials: Avatar initials.

    Returns:
        HTML string for the profile block.
    """
    return (
        f'<div class="profile">'
        f'<div class="avatar">{initials}</div>'
        f'<div><div class="profile-name">{name}</div>'
        f'<div class="profile-role">{role}</div></div>'
        f"</div>"
    )


def cta_button(label: str) -> str:
    """Build the sidebar call-to-action button.

    Args:
        label: Button text.

    Returns:
        HTML string for the button.
    """
    return f'<div class="cta">{label}</div>'


def panel(title: str, sub: str = "") -> st.container:
    """Open a dark panel that wraps arbitrary Streamlit content.

    Uses Streamlit's native bordered container (re-skinned as a dark panel by
    the theme CSS) so charts, tables and text all sit inside the same card,
    the way the reference mock does.

    Args:
        title: Panel title.
        sub: Optional subtitle under the title.

    Returns:
        The container to render the panel body into.
    """
    container = st.container(border=True)
    with container:
        sub_html = f'<div class="panel-sub">{sub}</div>' if sub else ""
        st.markdown(
            f'<div class="panel-title">{title}</div>{sub_html}',
            unsafe_allow_html=True,
        )
    return container


def legend_row(color: str, label: str, value: str, share: str) -> str:
    """Build one row of a colour-keyed chart legend.

    Rendered as HTML rather than a Plotly legend so the key always sits
    inside the panel: Plotly positions legends in paper coordinates, which
    drift outside the plot when the container is resized responsively.

    Args:
        color: Swatch colour (hex).
        label: Series label.
        value: Formatted value.
        share: Formatted share, e.g. ``"48.2%"``.

    Returns:
        HTML string for the legend row.
    """
    return (
        f'<div class="lg-row">'
        f'<span class="lg-swatch" style="background:{color}"></span>'
        f'<span class="lg-label">{label}</span>'
        f'<span class="lg-value">{value}</span>'
        f'<span class="lg-share">{share}</span>'
        f"</div>"
    )


def _page_link(key: str, active_key: str, hrefs: dict[str, str]) -> None:
    """Render one real, clickable sidebar navigation link.

    The visual styling comes from CSS (``.nav-link``); the anchor points at
    the same URL Streamlit's own navigation would use, so navigation keeps
    working and the browser URL stays bookmarkable.

    Args:
        key: Key of the page in :data:`PAGES`.
        active_key: Key of the page currently being viewed.
        hrefs: Mapping of page key -> href (from :func:`_resolve_hrefs`).
    """
    page = next(p for p in PAGES if p["key"] == key)
    href = hrefs.get(key, _page_href(page["path"]))
    active = " nav-active" if key == active_key else ""
    st.sidebar.markdown(
        f'<a class="nav-link{active}" href="{href}">'
        f'<span class="ni-icon">{page["icon"]}</span>'
        f'<span class="ni-text">{page["label"]}</span></a>',
        unsafe_allow_html=True,
    )


def _page_href(path: str) -> str:
    """Return the in-app URL for a page path.

    Streamlit's own multipage routing already exposes these URLs, so the
    bespoke sidebar links to exactly the same targets.

    Args:
        path: Page path relative to the entrypoint.

    Returns:
        A relative URL string.
    """
    if path in ("", "Dashboard.py"):
        return "./"
    slug = path.replace("pages/", "").replace(".py", "")
    return f"./{slug.lstrip('0123456789_')}"


def _page_registry() -> dict[str, str]:
    """Map script paths to their in-app URL pathnames.

    Streamlit owns the URL scheme (it strips the numeric filename prefix
    and the title casing rules), so the bespoke sidebar asks Streamlit
    rather than re-deriving it. Falls back to an empty mapping when the
    runtime registry is unavailable (e.g. unit tests).

    Returns:
        Mapping of resolved script path -> URL pathname.
    """
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()
        if ctx is None or ctx.pages_manager is None:
            return {}
        return {
            str(info["script_path"]): str(info["url_pathname"])
            for info in ctx.pages_manager.get_pages().values()
        }
    except Exception:  # pragma: no cover - runtime introspection is best effort
        return {}


def _resolve_hrefs() -> dict[str, str]:
    """Resolve every nav page key to a working in-app URL.

    Returns:
        Mapping of page key -> relative href.
    """
    registry = _page_registry()
    hrefs: dict[str, str] = {}
    for page in PAGES:
        path = page["path"] or "Dashboard.py"
        slug = registry.get(path)
        if slug:
            hrefs[page["key"]] = f"./{slug}" if slug else "./"
        else:
            hrefs[page["key"]] = _page_href(path)
    return hrefs


def _active_key(hrefs: dict[str, str]) -> str:
    """Determine which nav page is currently being viewed.

    Args:
        hrefs: Mapping of page key -> href (from :func:`_resolve_hrefs`).

    Returns:
        The key of the active page, or an empty string if it cannot be
        determined.
    """
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()
        if ctx is None or ctx.pages_manager is None:
            return ""
        pages = ctx.pages_manager.get_pages()
        current = pages.get(ctx._active_script_hash)  # noqa: SLF001
        if not current:
            return ""
        active_slug = str(current.get("url_pathname", ""))
        for key, href in hrefs.items():
            if active_slug == "" and href == "./":
                return key
            if href == f"./{active_slug}":
                return key
    except Exception:  # pragma: no cover - runtime introspection is best effort
        return ""
    return ""


def render_cockpit_sidebar(
    active_key: str,
    df,
    weekly,
    render_filters,
) -> None:
    """Render the full bespoke sidebar: brand, grouped nav, filters, profile.

    Args:
        active_key: Key of the page currently being viewed.
        df: Cleaned transaction frame (passed to the filter renderer).
        weekly: Weekly KPI frame (passed to the filter renderer).
        render_filters: Callable that renders the filter widgets and returns
            the ``(weeks, categories, fulfilments, states)`` selections.
    """
    st.sidebar.markdown(
        nav_brand("Revenue", "Cockpit"), unsafe_allow_html=True
    )

    hrefs = _resolve_hrefs()
    # Fall back to the caller-supplied key when the runtime cannot tell us.
    active = _active_key(hrefs) or active_key

    for section, keys in NAV_SECTIONS:
        st.sidebar.markdown(nav_section(section), unsafe_allow_html=True)
        for key in keys:
            _page_link(key, active, hrefs)

    st.sidebar.markdown(nav_section("Channels"), unsafe_allow_html=True)
    weeks, categories, fulfilments, states = render_filters(df, weekly)

    st.sidebar.markdown(
        profile_block("Ansh Thakur", "Revenue Analytics", "AT"),
        unsafe_allow_html=True,
    )
    return weeks, categories, fulfilments, states


def render_export_button(
    weekly_filtered: pd.DataFrame,
    filename: str = "revenue_reconciliation_report.csv",
) -> None:
    """Render the sidebar "Export Report" download button.

    Exports the *filtered* weekly reconciliation matrix, so what the user
    downloads is exactly what the dashboard is showing.

    Args:
        weekly_filtered: Weekly KPI frame for the current filter selection.
        filename: Download filename offered to the browser.
    """
    st.sidebar.download_button(
        "Export Report",
        data=weekly_filtered.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
        key="sidebar_export_report",
    )

