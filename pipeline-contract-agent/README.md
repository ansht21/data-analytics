# 🛡️ Pipeline Contract Agent

Contract-first data pipeline guard for the supply-chain log.
**The contract enforces. The agent investigates. The human approves.**

> **✅ Live-verified 19-Oct-2026 (Windows, Python 3.14):** good batch
> `PASS: 30 rows` → bad batch `FAIL: 2 rule(s)` → quarantined to
> `incidents/20261019T075751Z_bad_money/` with `validation.json` +
> `incident_report.md` + `fix.patch`. Reproduce with the 60-second demo below.

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

## ✅ Proof it works (verified live)

### Terminal — PASS vs FAIL (run this)

```bash
# 1. Good batch sails through
python -W ignore pipeline/ingest.py --batch fixtures/good_sample.csv
# PASS: 30 rows satisfy the contract.
# PASS — batch accepted for cleaning. (Downstream load may proceed.)

# 2. Bad batch gets caught + quarantined (exit code 1 = blocked by design)
python -W ignore pipeline/ingest.py --batch fixtures/bad_money.csv --auto-investigate
# FAIL: 2 rule(s) broken over 12 rows:
#   - [high] non_numeric_money: 'Unit_Cost' must be numeric money (1 rows)
#   - [high] non_numeric_money: 'Unit_Price' must be numeric money (1 rows)
# QUARANTINED -> incidents/<utc>_bad_money/
```

### Quarantine bundle — every FAIL leaves 6 files

```
incidents/20261019T075751Z_bad_money/
├── batch__bad_money.csv   # untouched evidence (12 rows)
├── validation.json        # passed:false, 2 violations (SO-000107, SO-000104)
├── incident_report.md     # rule → cause → impact → fix
├── fix.patch              # guardrail proposal (human must approve + apply)
├── mr_body.md             # ready-to-post MR text (dry-run default)
└── manifest.json          # quarantine receipt (downstream_blocked:true)
```

`manifest.json` excerpt:

```json
{
  "batch_file": "bad_money.csv",
  "contract": "contract/supply_orders.contract.yaml",
  "total_rows": 12,
  "failed_rules": ["non_numeric_money", "non_numeric_money"],
  "downstream_blocked": true,
  "note": "Cleaned data NOT overwritten. Fix forward via agent + MR, then re-ingest."
}
```

### Service — API + UI

```bash
uvicorn api.main:app --port 8000        # http://localhost:8000/docs
streamlit run app.py --server.port 8501 # http://localhost:8501
docker compose up --build               # api :8000 + ui :8501
```

| Where | Good batch | Bad batch |
|---|---|---|
| CLI | `PASS: 30 rows` | `FAIL → QUARANTINED` (exit 1) |
| `POST /ingest` | `200` + warehouse receipt | `422` + `incident_dir` |
| Streamlit | green `PASS` banner | red `QUARANTINED` + expandable report/patch |

### CI — deployed in workflow

- **GitHub Actions** (`.github/workflows/pipeline.yml`): tests on every push + scheduled daily drift batch, `incidents/` + `warehouse/` kept as artifacts.
- **GitLab CI** (`.gitlab-ci.yml`): `test` stage (fixtures → `pytest -q`, 22 green) + `scheduled-batch` stage (drift injection → quarantine), artifacts expire in 30 days.
- **Sample evidence:** committed under `incidents/sample_bad_money/` — open its `validation.json` + `incident_report.md` without running anything.
