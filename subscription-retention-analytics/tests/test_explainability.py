"""
Explainability, grounding-scan, and JSON-extraction tests.
Fast + deterministic: small forest on a fixed subsample.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import genai
import modeling as mdl
from data_processing import load_and_clean
from explainability import (get_explainer, global_importance,
                            local_explanation, build_customer_risk_record)
from feature_engineering import build_features


@pytest.fixture(scope="session")
def small_model_env():
    df = load_and_clean(ROOT / "data" / "Telco_Customer_Churn.csv").sample(
        1200, random_state=42)
    feats = build_features(df)
    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(n_estimators=50, min_samples_leaf=5,
                                random_state=42, n_jobs=1).fit(feats, df["ChurnFlag"])
    explainer = get_explainer(rf, feats.head(100), "Random Forest")
    return df, feats, rf, explainer


def test_local_explanation_structure(small_model_env):
    df, feats, rf, explainer = small_model_env
    row = feats.head(1)
    out = local_explanation(explainer, row, list(feats.columns), top_n=5)
    assert len(out["top_drivers"]) == 5
    assert all(d["direction"] in ("raises risk", "lowers risk")
               for d in out["top_drivers"])
    assert isinstance(out["base_value"], float)


def test_global_importance_ranked(small_model_env):
    df, feats, rf, explainer = small_model_env
    imp = global_importance(explainer, feats.head(100), top_n=8)
    assert len(imp) == 8
    assert imp["mean_abs_shap"].is_monotonic_decreasing


def test_customer_risk_record_consistency(small_model_env):
    df, feats, rf, explainer = small_model_env
    cid = df["customerID"].iloc[0]
    rec = build_customer_risk_record(df, cid, rf, explainer, None,
                                     "Random Forest")
    assert 0 <= rec["churn_probability"] <= 1
    assert rec["risk_level"] == mdl.risk_band(rec["churn_probability"])
    assert abs(rec["monthly_revenue_at_risk"]
               - round(rec["churn_probability"] * rec["monthly_revenue"], 2)) < 0.01
    assert len(rec["top_drivers"]) == 5


def test_scan_claims_flags_claim_sections_only():
    # hallucinated claim in evidence -> flagged
    bad = {"evidence": ["The customer complained three times last month."],
           "retention_considerations": []}
    assert "complaints" in genai.scan_claims(bad)
    # honest missing_information naming the category -> NOT flagged
    good = {"evidence": ["Contract is Month-to-month (payload)."],
            "retention_considerations": [],
            "missing_information": ["complaints", "satisfaction scores"]}
    assert genai.scan_claims(good) == []


def test_extract_json_object_from_mixed_text():
    text = 'Analyst asks: {"a": 1, "b": {"c": 2}} and also {"d": 3}'
    obj = genai._extract_json_object(text)
    assert obj == {"a": 1, "b": {"c": 2}}  # first parseable object wins
    assert genai._extract_json_object("no json here") is None


def test_schema_rejects_out_of_range_probability():
    raw = genai.offline_template({"churn_probability": 0.5,
                                  "risk_level": "Medium", "top_drivers": ["tenure"]})
    data = genai.validate_schema(raw)
    data["churn_probability"] = 1.5
    with pytest.raises(ValueError):
        genai.validate_schema(genai_offline_json(data))


def genai_offline_json(data: dict) -> str:
    import json
    return json.dumps(data)
