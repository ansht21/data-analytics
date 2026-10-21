# LinkedIn Post 1 — Pipeline Contract Agent (post this week, carousel)

---
**Hook:** Your dashboard is lying. A CSV changed format upstream and nobody noticed. I built the guard that catches it. 🛡️

**Body:**
Silent data corruption is the costliest bug in analytics — a money column arrives as "twelve" instead of 12, revenue goes NaN, and the P&L understates for weeks.

So I built a contract-first pipeline guard:

✅ Deterministic pandas validator (NO AI gates data) — same CSV in, same verdict out
✅ 30 clean rows → PASS, loaded to warehouse
✅ 12 dirty rows → FAIL → quarantined with full audit bundle:
   validation.json + incident_report.md (rule → cause → impact → fix) + fix.patch + MR body
✅ FastAPI gate (200 pass / 422 quarantine) + Streamlit ops console + Docker + CI on every push
✅ 22/22 tests green, works fully offline

The contract enforces. The agent investigates. The human approves.

Repo + 60-sec demo: https://github.com/ansht21/data-analytics/tree/main/pipeline-contract-agent

#DataEngineering #DataQuality #Python #FastAPI #OpenToWork
---

# LinkedIn Post 2 — Revenue Reconciliation Engine (post next week)

---
**Hook:** We invoiced ₹7.86 Cr. Only ₹1.86 Cr was real. Here's where the rest went. 💧

**Body:**
128,976 Amazon India transactions. One question finance asks weekly and rarely answers honestly: how much cash did we actually realise?

I built a deterministic reconciliation engine (no ML — auditable SUM() math):

📊 ₹7.86 Cr gross → ₹1.86 Cr net realized (23.7% clearance)
🔴 ₹69.18L cancellations (18,334 orders) — largest true leakage
🟠 ₹13.85L returns · ⚪ ₹5.10 Cr in-transit (settlement lag, NOT loss)
🚨 20 anomaly triggers: clearance < 85% → CRITICAL, cancel > 15% → WARNING, WoW drop > 10% → ALERT

Outputs: 3-tab Excel workbook (live formulas + native charts) + 4-page Streamlit dashboard. One command: python run_pipeline.py

Repo: https://gitlab.com/ansht_121/data-analytics/-/tree/main/weekly-revenue-reconciliation-engine

#DataAnalytics #Finance #Python #Excel #OpenToWork
---
