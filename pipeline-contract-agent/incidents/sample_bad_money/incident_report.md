# Incident Report — `bad_money.csv`

**Overall severity:** high  
**Mode:** offline-rule-based (llm import failed: No module named 'langchain_groq')  
**Rows scanned:** 12  
**Rules broken:** 2

## What broke

- **non_numeric_money** [high] — 'Unit_Cost' must be numeric money (e.g. $1,001.18). (1 rows)
- **non_numeric_money** [high] — 'Unit_Price' must be numeric money (e.g. $1,001.18). (1 rows)

## Root cause -> impact -> fix

### 1. non_numeric_money [high]
- **Likely cause:** Currency column arrived as free text ('twelve') or new symbol formatting.
- **Pipeline location:** `src/data_cleaning.py _clean_money regex — passes through anything matching [$ ,0-9.].`
- **Downstream impact:** revenue/profit become NaN; P&L totals understate.
- **Suggested fix:** Strict money parser + quarantine on unparseable (enforced); propose upstream numeric export.

### 2. non_numeric_money [high]
- **Likely cause:** Currency column arrived as free text ('twelve') or new symbol formatting.
- **Pipeline location:** `src/data_cleaning.py _clean_money regex — passes through anything matching [$ ,0-9.].`
- **Downstream impact:** revenue/profit become NaN; P&L totals understate.
- **Suggested fix:** Strict money parser + quarantine on unparseable (enforced); propose upstream numeric export.

## Audit trail
- `batch__*` — quarantined offending batch (untouched)
- `validation.json` — deterministic validator output
- `manifest.json` — quarantine receipt
- `incident_report.md` — this file (rule -> root cause -> impact)
- `fix.patch` — proposed guardrail/test (human must approve + apply)
