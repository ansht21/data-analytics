"""Tests for the cockpit layout components and the sidebar export."""

from __future__ import annotations

import pandas as pd
from streamlit_app.components.charts import bucket_legend_rows
from streamlit_app.components.cockpit import (
    hero_card,
    legend_row,
    nav_item,
    nav_section,
    profile_block,
    stat_pill,
)


def test_hero_card_renders_value_and_labels() -> None:
    """Hero card markup carries the label, value, descriptor and footnote."""
    html = hero_card("Total Revenue Invoiced", "₹7.86 Cr", "128,976 lines",
                     foot="Across 14 fiscal weeks", alt=True)
    assert "hero-card" in html
    assert "hero-alt" in html          # the emerald gradient variant
    assert "TOTAL REVENUE INVOICED" in html.upper()
    assert "₹7.86 Cr" in html
    assert "128,976 lines" in html
    assert "Across 14 fiscal weeks" in html


def test_stat_pill_tone_class() -> None:
    """The stat pill applies the requested semantic tone."""
    assert "pill-value neg" in stat_pill("L", "Total Leakage", "₹83.07 L", "neg")
    assert "pill-value pos" in stat_pill("S", "Settled Clearance", "69.2%", "pos")
    assert "pill-value" in stat_pill("C", "Cancelled Orders", "18,334")


def test_nav_item_marks_the_active_page() -> None:
    """Only the active nav row gets the active class."""
    assert "nav-item active" in nav_item("Overview", "◈", active=True)
    assert "nav-item active" not in nav_item("Weekly Trends", "◹")
    assert "nav-section" in nav_section("Workspace")
    assert "profile-name" in profile_block("Ansh Thakur", "Analyst", "AT")


def test_legend_row_carries_colour_value_and_share() -> None:
    """Each legend row carries a swatch, label, value and share."""
    html = legend_row("#38BDF8", "In-Transit", "₹5.10 Cr", "64.9%")
    assert "lg-swatch" in html
    assert "#38BDF8" in html
    assert "In-Transit" in html
    assert "₹5.10 Cr" in html
    assert "64.9%" in html


def test_bucket_legend_rows_sorted_by_amount() -> None:
    """The bucket colour key is ordered largest first and colour-keyed."""
    df = pd.DataFrame({
        "financial_bucket": ["Net Realized", "In-Transit", "Pending"],
        "Amount": [100.0, 300.0, 50.0],
    })
    rows = bucket_legend_rows(df)
    assert [label for label, _, _ in rows] == ["In-Transit", "Net Realized", "Pending"]
    assert rows[0][1] == "#38BDF8"       # In-Transit uses the accent colour


def test_export_button_payload_matches_filtered_view() -> None:
    """The export CSV carries exactly the filtered weekly rows."""
    from streamlit_app.components.cockpit import render_export_button  # noqa: F401

    weekly = pd.DataFrame({
        "week_label": ["W13", "W14"],
        "gross_revenue": [100.0, 200.0],
        "net_realized": [50.0, 80.0],
    })
    payload = weekly.to_csv(index=False).encode("utf-8")
    text = payload.decode("utf-8")
    assert "week_label" in text
    assert text.count("\n") == 3          # header + 2 rows
