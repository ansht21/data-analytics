"""Deterministic analytics tests — every figure must match the committed SQL/outputs.

Run:  PYTHONPATH=. pytest tests/ -q
"""
from __future__ import annotations

import pytest

from src.analytics import CHIPS, chip_labels, run_chip
from src.brief import brief_markdown, build_brief
from src.datasets import DATASETS, dataset_kpis, load_dataset


@pytest.mark.parametrize("key", ["supply", "uber", "churn"])
def test_datasets_load_with_expected_shapes(key: str) -> None:
    df = load_dataset(key)
    assert len(df) > 1000
    assert key in DATASETS


def test_supply_row_count() -> None:
    assert len(load_dataset("supply")) == 7991


def test_uber_row_count() -> None:
    assert len(load_dataset("uber")) == 35000


def test_churn_row_count() -> None:
    # Raw CSV has 7,043 rows; 11 are blank-TotalCharges newcomers kept as 0
    # (see subscription-retention-analytics/sql_queries/01_data_cleaning.sql).
    assert len(load_dataset("churn")) == 7043


def test_margin_bleed_matches_sql_q8() -> None:
    """SQL Q8: 20%+ -> 4.64% realised margin vs 31.02% for 5-10%."""
    ins = run_chip("supply", "Margin Bleed Audit", load_dataset("supply"))
    assert "4.64%" in ins.finding and "31.02%" in ins.finding
    assert ins.chart and ins.chart["kind"] == "bar"
    assert ins.runtime_ms >= 0


def test_warehouse_trap_matches_readme() -> None:
    """README: 31.9% of late orders, only 0.08% between-warehouse variance."""
    ins = run_chip("supply", "Warehouse Trap Check", load_dataset("supply"))
    assert "31.9%" in ins.finding and "0.08%" in ins.finding
    assert "WARE-NMK1003" in ins.finding


def test_abc_matches_pipeline_output() -> None:
    """abc_classification.csv: 36 A-items; our <=80% rule gives 35-36."""
    ins = run_chip("supply", "ABC SKU Pareto", load_dataset("supply"))
    assert "47 SKUs" in ins.finding


def test_surge_timing_matches_readme() -> None:
    ins = run_chip("uber", "Peak Surge Detection", load_dataset("uber"))
    assert "5:00" in ins.finding and "18:00" in ins.finding and "31.2%" in ins.finding


def test_airport_mix_matches_readme() -> None:
    ins = run_chip("uber", "Airport Revenue Share", load_dataset("uber"))
    assert "39.6%" in ins.finding and "54.8%" in ins.finding


def test_vehicle_tier_matches_readme() -> None:
    ins = run_chip("uber", "Vehicle Tier Efficiency", load_dataset("uber"))
    assert "Uber Black" in ins.finding and "Uber Pool" in ins.finding


def test_churn_cohort_matches_segment_table() -> None:
    """churn_segment_revenue.csv row 1: 2,128 customers, 0.546 rate."""
    ins = run_chip("churn", "High-Risk Cohort Audit", load_dataset("churn"))
    assert "2,128" in ins.finding and "54.6%" in ins.finding


def test_churn_payment_matches_sql() -> None:
    """SQL: Electronic check 45.3%."""
    ins = run_chip("churn", "Payment Friction Risk", load_dataset("churn"))
    assert "Electronic check" in ins.finding and "45.3%" in ins.finding


def test_all_chips_have_consulting_format() -> None:
    for key in ("supply", "uber", "churn"):
        df = load_dataset(key)
        assert len(chip_labels(key)) == 3
        for label in chip_labels(key):
            ins = run_chip(key, label, df)
            assert ins.finding and ins.explanation and ins.suggestion
            assert ins.pandas_snippet and ins.chart


def test_brief_builds_and_renders_markdown() -> None:
    for key in ("supply", "uber", "churn"):
        brief = build_brief(key, load_dataset(key))
        assert len(brief["kpis"]) == 4 and len(brief["insights"]) == 3
        md = brief_markdown(brief, DATASETS[key]["label"])
        assert "Executive Brief" in md and "Recommended decisions" in md


def test_kpis_are_sane() -> None:
    kpis = dict(dataset_kpis("supply", load_dataset("supply")))
    assert kpis["Net revenue"].startswith("$73.")
    assert kpis["Late orders"].startswith("49.")
