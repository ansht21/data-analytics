"""
GenAI layer tests: schema validation, unsupported-claim detection, and the
deterministic offline Copilot fallback (no API key required).
"""
import sys
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import genai


def _valid_response():
    return json.dumps({
        "risk_level": "High", "churn_probability": 0.87,
        "top_drivers": ["ctl_Contract_Month_to_month", "tenure", "MonthlyCharges"],
        "evidence": ["Contract type is Month-to-month (payload).",
                     "Monthly charges are 92 (payload)."],
        "retention_considerations": ["RECOMMENDATION (not evidence): review contract options."],
        "missing_information": ["complaints", "satisfaction scores",
                                "support interactions", "competitor information"],
        "limitations": ["SHAP values are model-supported contributions, not causal evidence."],
    })


def test_schema_validation_accepts_valid():
    data = genai.validate_schema(_valid_response())
    assert data["risk_level"] == "High"


def test_schema_validation_rejects_missing_field():
    raw = json.dumps({"risk_level": "High"})  # missing everything else
    with pytest.raises(ValueError):
        genai.validate_schema(raw)


def test_schema_validation_rejects_bad_risk_level():
    raw = _valid_response().replace('"High"', '"Extreme"')
    with pytest.raises(ValueError):
        genai.validate_schema(raw)


def test_unsupported_claim_detection_complaints():
    assert "complaints" in genai.check_unsupported_claims(
        "This customer complained three times.")


def test_unsupported_claim_detection_satisfaction():
    assert "satisfaction" in genai.check_unsupported_claims(
        "The customer is very satisfied with support.")


def test_offline_template_is_grounded_and_schema_valid(monkeypatch):
    provider = genai.LLMProvider(api_key="")  # force offline
    assert not provider.is_live
    record = {"customerID": "0001", "Contract": "Month-to-month", "tenure": 5,
              "MonthlyCharges": 92, "churn_probability": 0.87,
              "risk_level": "High", "top_drivers": ["tenure", "Contract"]}
    resp = genai.generate_copilot_response(record, "C_structured", provider)
    val = resp["validation"]
    assert val["schema_valid"] is True
    assert val["unsupported_claims"] == []  # offline template adds no invented facts
    assert resp["churn_probability"] == 0.87


def test_copilot_missing_information_acknowledged():
    # Negative case: dataset has no complaints/satisfaction/competitor data.
    rec = {"customerID": "C2", "churn_probability": 0.4, "risk_level": "Medium",
           "top_drivers": ["MonthlyCharges"]}
    resp = genai.generate_copilot_response(rec, "C_structured", genai.LLMProvider(api_key=""))
    if resp["validation"]["schema_valid"]:
        assert any("complain" in (x or "").lower() or "insufficient"
                   in " ".join(resp["missing_information"]).lower()
                   for x in resp["missing_information"])