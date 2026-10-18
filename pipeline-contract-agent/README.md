# 🛡️ Pipeline Contract Agent

Contract-first data pipeline guard for the supply-chain log.
**The contract enforces. The agent investigates. The human approves.**

```
batch arrives → validate (deterministic pandas, NO AI)
   ├── PASS → load to warehouse/orders.db
   └── FAIL → quarantine to incidents/ + trigger agent
                  → incident_report.md (rule → cause → impact → fix)
                  → fix.patch + MR body (dry-run default; live GitLab MR with token)
```

## Quickstart

```bash
pip install -r requirements.txt
python fixtures/make_fixtures.py
pytest -q                                   # 22 tests
python -W ignore pipeline/ingest.py --batch fixtures/good_sample.csv
python -W ignore pipeline/ingest.py --batch fixtures/bad_nulls.csv --auto-investigate
```

## Simulate a daily batch (drift on demand)

```bash
python src/ingest_sim.py --inject-drift all     # dates| nulls | text | mode | all
python -m src.pipeline --batch data/batches/orders_batch_*.csv
```

## Run as a service

```bash
uvicorn api.main:app --port 8000        # POST /ingest, GET /health /contract /incidents
streamlit run app.py --server.port 8501 # operations console
docker compose up --build               # api :8000 + ui :8501
```

## API

| Method | Route | Effect |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/contract` | contract name/version/hash |
| POST | `/ingest` | validate upload; 200 pass / 422 quarantined + report |
| GET | `/incidents` | quarantined batch list |

## Design decisions

1. **Contract-first** — `contract/supply_orders.contract.yaml` (v1.0.0, sha-pinned)
   is the single source of truth, reviewable in MRs.
2. **Deterministic validation** — `src/validate.py` is pure pandas; identical input
   always yields identical FAIL. The LLM never gates data.
3. **Quarantine, don't delete** — every FAIL preserves batch + validation.json +
   manifest.json under `incidents/<utc>_<batch>/`.
4. **Agent proposes only** — offline rule-based investigator by default; Groq
   (`GROQ_API_KEY`) only upgrades narrative. `fix.patch` needs human apply.
5. **Deploy-shaped** — FastAPI + Streamlit + Docker + GitLab CI (tests on push,
   scheduled batch) + GitHub Actions mirror for the PR story.

## Repo map

`contract/` law · `src/` validate/trigger/investigate/report/mr/pipeline/warehouse ·
`pipeline/ingest.py` CLI · `api/main.py` service · `app.py` console ·
`fixtures/` good + 4 bad · `tests/` 22 green · `incidents/` audit trail.

## 60-second demo (recruiter tour)

```bash
python -W ignore pipeline/ingest.py --batch fixtures/bad_money.csv --auto-investigate
# QUARANTINED -> incidents/<utc>_bad_money/
# Report: incidents/<utc>_bad_money/incident_report.md
# MR: fix.patch + mr_body.md (dry-run; live GitLab MR with GITLAB_TOKEN)
```

What to show:
1. `validation.json` — `non_numeric_money [high]` on `Unit_Cost`/`Unit_Price`.
2. `incident_report.md` — rule → cause (`_clean_money` regex) → impact (revenue NaN) → fix.
3. `fix.patch` — per-rule guardrail proposal (human must approve + apply).
