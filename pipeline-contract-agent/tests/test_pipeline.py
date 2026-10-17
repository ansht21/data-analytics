"""Pipeline, contract, trigger + investigator tests (offline, no keys)."""
from __future__ import annotations

from pathlib import Path

from src import agent_investigate, trigger
from src.contract import contract_info, load_data_contract
from src.pipeline import run
from src.validate import validate_batch
from src import CONTRACT_PATH

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_contract_has_version_and_hash():
    c = load_data_contract(CONTRACT_PATH)
    assert c.version and len(c.sha256) == 12 and len(c.fields) >= 10
    assert contract_info(CONTRACT_PATH)["sha256"] == c.sha256


def test_pipeline_pass_loads_warehouse(tmp_path, monkeypatch):
    import src.warehouse as wh
    monkeypatch.setattr(wh, "WAREHOUSE", tmp_path / "orders.db")
    out = run(FIX / "good_sample.csv", auto_investigate=False)
    assert out["status"] == "passed"
    assert out["warehouse"]["batch_rows"] == 30


def test_pipeline_fail_quarantines(tmp_path):
    out = run(FIX / "bad_money.csv", auto_investigate=True)
    assert out["status"] == "quarantined"
    inc = Path(out["incident_dir"])
    for f in ("validation.json", "manifest.json", "incident_report.md",
              "fix.patch", "mr_body.md"):
        assert (inc / f).exists(), f"missing {f}"


def test_trigger_pass_returns_receipt(tmp_path):
    r = validate_batch(FIX / "good_sample.csv")
    o = trigger.handle_result(FIX / "good_sample.csv", r, incidents_dir=tmp_path)
    assert o.status == "passed" and o.incident_dir is None


def test_investigator_offline_maps_rules():
    r = validate_batch(FIX / "bad_nulls.csv")
    a = agent_investigate.analyse(r.to_dict())
    assert a["severity_overall"] == "critical"
    assert a["mode"] == "offline-rule-based"
    assert any("CustomerID" in f["cause"] or "customer" in f["cause"].lower()
               for f in a["findings"])


def test_investigator_without_key_stays_offline(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    a = agent_investigate.enhance_with_llm({"mode": "x", "findings": []},
                                           {"violations": []})
    assert "offline" in a["mode"]


def test_react_agent_offline_safe():
    from src import agent_investigate
    agent_investigate.set_context({"total_rows": 3, "violations": []}, None)
    out = agent_investigate.run_react_agent("test")
    assert "offline" in out["mode"]


def test_react_tools_registered_when_available():
    from src import agent_investigate
    ok, _ = agent_investigate.react_available()
    assert isinstance(ok, bool)  # offline env -> False, keyed env -> True
