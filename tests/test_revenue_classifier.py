"""Tests for status -> financial bucket classification."""

from __future__ import annotations

from src.reconciliation.revenue_classifier import build_lookup, classify_status


def test_known_statuses() -> None:
    """Every documented status lands in its bucket."""
    assert classify_status("Shipped - Delivered to Buyer") == "Net Realized"
    assert classify_status("Cancelled") == "Cancellation Leakage"
    assert classify_status("Shipped - Returned to Seller") == "Return Leakage"
    assert classify_status("Shipped - Rejected by Buyer") == "Return Leakage"
    assert classify_status("Shipped - Lost in Transit") == "Loss Leakage"
    assert classify_status("Shipped - Damaged") == "Loss Leakage"
    assert classify_status("Shipped") == "In-Transit"
    assert classify_status("Pending") == "Pending"


def test_unknown_status_unmapped() -> None:
    """Unknown statuses fall back to Unmapped, never crash."""
    assert classify_status("Something Brand New") == "Unmapped"
    assert classify_status("") == "Unmapped"


def test_config_override() -> None:
    """Settings buckets override the default mapping."""
    custom = {"Net Realized": ["Delivered"]}
    assert classify_status("Delivered", custom) == "Net Realized"
    assert classify_status("Cancelled", custom) == "Unmapped"


def test_lookup_counts() -> None:
    """Default lookup covers 13 real Amazon statuses + no duplicates."""
    lookup = build_lookup()
    assert len(lookup) >= 13
    assert lookup["Shipped - Delivered to Buyer"] == "Net Realized"
