"""Validator rule tests: every rule gets a pass case + fail case."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.validate import parse_money_raw, validate_batch

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_good_sample_passes():
    r = validate_batch(FIX / "good_sample.csv")
    assert r.passed, r.summary()
    assert r.total_rows == 30


def test_null_customer_ids_fail_critical():
    r = validate_batch(FIX / "bad_nulls.csv")
    assert not r.passed
    ids = [v.rule_id for v in r.violations]
    assert "null_customer_id" in ids
    crit = [v for v in r.violations if v.rule_id == "null_customer_id"][0]
    assert crit.severity == "critical" and crit.rows_affected == 3


def test_iso_dates_flagged():
    r = validate_batch(FIX / "bad_dates.csv")
    assert not r.passed
    assert any(v.rule_id == "bad_date_format" for v in r.violations)


def test_text_money_flagged():
    r = validate_batch(FIX / "bad_money.csv")
    assert not r.passed
    assert any(v.rule_id == "non_numeric_money" for v in r.violations)


def test_chronology_rule():
    r = validate_batch(FIX / "bad_chronology.csv")
    assert not r.passed
    assert any(v.rule_id == "chronology_violation" for v in r.violations)


def test_unreadable_file_is_violation_not_crash():
    r = validate_batch(FIX / "does_not_exist.csv")
    assert not r.passed and r.total_rows == 0


@pytest.mark.parametrize("raw,expected", [
    ("$1,001.18", 1001.18), ("$0.00", 0.0), (12, 12.0),
    ("twelve", None), ("FREE", None), ("", None),
])
def test_money_parser(raw, expected):
    assert parse_money_raw(raw) == expected


def test_summary_strings():
    ok = validate_batch(FIX / "good_sample.csv")
    assert ok.summary().startswith("PASS")
    bad = validate_batch(FIX / "bad_nulls.csv")
    assert "FAIL" in bad.summary() and "null_customer_id" in bad.summary()


def test_result_serialises_to_json(tmp_path):
    import json
    r = validate_batch(FIX / "bad_nulls.csv")
    json.dumps(r.to_dict())  # must not raise
