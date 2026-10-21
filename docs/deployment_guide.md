# Deployment Guide

## 1. Local (Windows / macOS / Linux)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python run_pipeline.py            # clean + Excel workbook in reports/
streamlit run streamlit_app/Dashboard.py  # dashboard on http://localhost:8501
```

Make shortcuts: `make run`, `make streamlit`, `make test`, `make lint`.

## 2. Docker

```bash
docker build -t weekly-revenue-reconciliation-engine .
docker run --rm -v ${PWD}/reports:/app/reports weekly-revenue-reconciliation-engine python run_pipeline.py
docker compose up dashboard       # dashboard on :8501
```

## 3. GitLab CI/CD

`.gitlab-ci.yml` runs three stages on every push:

1. **lint** — Ruff + MyPy
2. **test** — pytest with `--cov-fail-under=80`
3. **build** (default branch only) — Docker image build + smoke `--no-excel` run

## 4. Scheduling (Finance weekly run)

Cron example — Sunday 02:00 IST:

```
0 2 * * 0  cd /app && python run_pipeline.py >> logs/cron.log 2>&1
```

The Excel workbook name is timestamped
(`Revenue_Reconciliation_Dashboard_<YYYYmmdd_HHMMSS>.xlsx`), so weekly
runs never overwrite each other; copy `reports/` to your finance share
or attach to an email hook.
