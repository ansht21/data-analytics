# AI Agents in Data Pipelines — Review Conversation (Saved 2026-10-18)

## Original Question
> Check my project https://gitlab.com/ansht_121/data-analytics.git and tell me which is better for adding AI — comparing against article "AI Agents in Data Pipelines: Start with Data Contracts (9 Oct 2026)". Yesterday I created one project, could you review that and suggest what to do to make it stronger — because I used an AI agent inside data analyst project, is that good?

## Review Summary
- Found local project at `C:\Users\ansht\data-analytics\` with new module `pipeline-contract-agent/` (commit 5874bed, 2026-10-17).
- Verified: contract-first design matches article blueprint almost exactly.
- Tests: `22 passed` in `pipeline-contract-agent/tests`.
- Sample incident `incidents/sample_bad_money/incident_report.md` correctly maps rule → cause → impact → fix.

## Scorecard vs Article Blueprint
1. Define contract first → `contract/supply_orders.contract.yaml` (17 fields, R01-R05, severity) — BETTER than article's 3-rule example.
2. Validate at ingestion → `src/validate.py` pure pandas, NO AI — CORRECT.
3. Agent investigates → `src/agent_investigate.py` offline EXPLAIN map + Groq ReAct (inspect_quarantine, read_pipeline_code, recent_changes, query_warehouse) — EXACT match.
4. Write report → `src/report.py` → What broke / Root cause → impact → fix / Audit trail.
5. Open PR/MR → `src/open_fix_mr.py` → fix.patch + mr_body.md, live GitLab MR if token — pattern correct.
6. Principle: "The contract enforces. The agent investigates. The human approves." — PERFECT.
7. Audit trail: validation.json + manifest.json + batch__* untouched.

## Which AI is Stronger?
- A) `pipeline-contract-agent` → STRONG for Data Engineer / Analytics Engineer (protects quality, explains failure, repeatable + MR).
- B) `analytics-intelligence-copilot` → GOOD for analyst storytelling, WEAK as "agent in pipeline" (article says chat-on-DB is less impressive).
- Recommendation: Lead with A for pipeline/DE roles. Keep B as interactive capstone.

## Fixes Applied (2026-10-18 session)
1. `src/open_fix_mr.py` — replaced generic fix.patch with per-rule `_rule_snippets()` (null, bad_date_format, non_numeric, chronology, duplicate, allowed_value, range, missing_column) + rows affected + HUMAN MUST REVIEW line. Verified on bad_money.csv.
2. `src/agent_investigate.py` — `enhance_with_llm()` now returns clean `mode: offline-rule-based` + polite `llm_note` instead of leaking `llm import failed: No module named...`.
3. `pipeline-contract-agent/README.md` — 20 → 22 tests, added 60-second demo section.
4. `data-analytics/README.md` — surfaced contract-agent: top banner, portfolio table row, dual 60-sec tours (analyst + data engineer), architecture tree entry.

## Validation
- `pytest pipeline-contract-agent/tests -q` → 22 passed in 1.46s.
- `pipeline/ingest.py --batch fixtures/bad_money.csv --auto-investigate` → QUARANTINED → incidents/20261018T083114Z_bad_money/ with validation.json + incident_report.md (Mode: offline-rule-based) + per-rule fix.patch.

## Remaining TODO (needs user GitLab token)
- Open one LIVE MR: set GITLAB_TOKEN + GITLAB_PROJECT_ID=85374986, re-run ingest, paste MR URL into README. This proves real GitLab workflow automation.

## Key Quote for Interviews
> Copilot answers business questions. Contract-Agent protects the pipeline so those answers stay true.

## Full Article Reference
Article: "AI Agents in Data Pipelines: Start with Data Contracts" (9 Oct 2026) — contract defines source/destination/rules (dates YY/MM/DD, Customer ID never null, Amount numeric, status allowlist, etc.); pipeline validates → flags → agent scans code+data → explains → opens GitHub PR. Design: contract explicit, validation deterministic, agent for investigation not enforcement, output actionable, preserve audit trail.
