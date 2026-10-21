"""Deterministic contract validator — NO AI here by design."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


@dataclass
class Violation:
    rule_id: str
    severity: str
    message: str
    rows_affected: int
    sample: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ValidationResult:
    passed: bool
    total_rows: int
    violations: list[Violation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "total_rows": self.total_rows,
            "violations": [
                {"rule_id": v.rule_id, "severity": v.severity,
                 "message": v.message, "rows_affected": v.rows_affected,
                 "sample": v.sample} for v in self.violations
            ],
        }

    def summary(self) -> str:
        if self.passed:
            return f"PASS: {self.total_rows} rows satisfy the contract."
        lines = [f"FAIL: {len(self.violations)} rule(s) broken over {self.total_rows} rows:"]
        for v in self.violations:
            lines.append(f"  - [{v.severity}] {v.rule_id}: {v.message} ({v.rows_affected} rows)")
        return "\n".join(lines)


SEVERITY_MAP = {
    "null_customer_id": "critical", "bad_date_format": "high",
    "non_numeric_money": "high", "chronology_violation": "medium",
    "duplicate_order": "medium", "allowed_value": "high",
    "range_violation": "medium", "missing_column": "critical",
}

_MONEY_RE = re.compile(r"^[\$\s]*([0-9,]*\.?[0-9]+)\s*$")
_SLASH_DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/(\d{2}|\d{4})$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.replace(" ", "_", regex=False)
    df.columns = [re.sub(r"__+", "_", c) for c in df.columns]
    return df


def _sample(df: pd.DataFrame, n: int = 5) -> list[dict[str, Any]]:
    if df.empty:
        return []
    cols = list(df.columns)[:8]
    head = df[cols].head(n)
    return head.astype(object).where(pd.notna(head), None).to_dict(orient="records")


def parse_money_raw(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s == "" or s.lower() == "nan":
        return None
    m = _MONEY_RE.match(s)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def load_contract(contract_path: str | Path) -> dict:
    with open(contract_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_batch(csv_path, contract_path=None) -> ValidationResult:
    """Validate one raw batch CSV. Never raises on bad data."""
    from .paths import CONTRACT_PATH as _default

    contract_path = Path(contract_path) if contract_path else _default
    contract = load_contract(contract_path)
    fields: dict = contract.get("fields", {})
    try:
        raw = pd.read_csv(csv_path, dtype=str, keep_default_na=True)
    except Exception as exc:
        return ValidationResult(False, 0, [Violation("unreadable_file", "critical", f"Could not read CSV: {exc}", 0)])
    df = normalize_headers(raw)
    total = len(df)
    violations: list[Violation] = []

    def add(rule_id, message, bad_idx, sev=None):
        try:
            n = len(bad_idx)
        except TypeError:
            n = int(bad_idx)
        if n <= 0:
            return
        try:
            s = _sample(df.loc[bad_idx])
        except Exception:
            s = []
        violations.append(Violation(rule_id, sev or SEVERITY_MAP.get(rule_id.split(":")[0], "medium"), message, int(n), s))

    for col in fields:
        if col not in df.columns:
            violations.append(Violation("missing_column", "critical", f"Required column '{col}' missing.", total))
    for col, spec in fields.items():
        if col not in df.columns or spec.get("nullable", True):
            continue
        mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        if mask.any():
            key = "null_customer_id" if col == "_CustomerID" else f"null:{col}"
            sev = "critical" if col == "_CustomerID" else "high"
            add(key, f"Column '{col}' must never be null/empty.", df.index[mask], sev)
    date_cols = [c for c, s in fields.items() if s.get("type") == "date" and c in df.columns]
    parsed: dict = {}
    for col in date_cols:
        ser = df[col].astype(object)
        iso = ser.astype(str).str.match(_ISO_DATE_RE, na=False)
        if iso.any():
            add("bad_date_format", f"'{col}' must use DD/MM/YY slashes, found ISO YYYY-MM-DD.", df.index[iso], "high")
        bad = ~(ser.astype(str).str.match(_SLASH_DATE_RE, na=False)) & ~iso
        empty = ser.isna() | (ser.astype(str).str.strip() == "")
        bad = bad & ~empty
        if bad.any():
            add("bad_date_format", f"'{col}' has unparseable dates (expected D/M/YY slashes).", df.index[bad], "high")
        parsed[col] = pd.to_datetime(ser, format="mixed", dayfirst=True, errors="coerce")
    for col, spec in fields.items():
        if col not in df.columns:
            continue
        t = spec.get("type")
        if t == "money":
            bad = [i for i, v in df[col].items() if parse_money_raw(v) is None and str(v).strip() not in ("", "nan", "None")]
            if bad:
                add("non_numeric_money", f"'{col}' must be numeric money (e.g. $1,001.18).", bad, "high")
            if spec.get("min") is not None:
                under = [i for i, v in df[col].items() if (p := parse_money_raw(v)) is not None and p < spec["min"]]
                if under:
                    add("range_violation", f"'{col}' below minimum {spec['min']}.", under, "medium")
        elif t in ("int", "float"):
            num = pd.to_numeric(df[col], errors="coerce")
            empty = df[col].isna() | (df[col].astype(str).str.strip() == "")
            badm = num.isna() & ~empty
            if badm.any():
                add(f"non_numeric:{col}", f"'{col}' must be numeric.", df.index[badm], "high")
            else:
                if spec.get("min") is not None:
                    m = (num < spec["min"]) & num.notna()
                    if m.any():
                        add("range_violation", f"'{col}' below minimum {spec['min']}.", df.index[m], "medium")
                if spec.get("max") is not None:
                    m = (num > spec["max"]) & num.notna()
                    if m.any():
                        add("range_violation", f"'{col}' above maximum {spec['max']}.", df.index[m], "medium")
    for col, spec in fields.items():
        if col not in df.columns or "allowed" not in spec:
            continue
        allowed = set(spec["allowed"])
        mask = ~df[col].isin(allowed) & df[col].notna() & (df[col].astype(str).str.strip() != "")
        if mask.any():
            add("allowed_value", f"'{col}' has values outside approved list.", df.index[mask], "high")
    for col, spec in fields.items():
        if col in df.columns and spec.get("unique"):
            dup = df.index[df.duplicated(subset=[col], keep=False)]
            if len(dup):
                add("duplicate_order", f"'{col}' must be unique ({len(dup)} duplicated rows).", dup, "medium")
    need = ["ProcuredDate", "OrderDate", "ShipDate", "DeliveryDate"]
    if all(c in parsed for c in need):
        ok = parsed["ProcuredDate"].notna() & parsed["OrderDate"].notna() & parsed["ShipDate"].notna() & parsed["DeliveryDate"].notna()
        bad_c = ok & ~((parsed["ProcuredDate"] <= parsed["OrderDate"]) & (parsed["OrderDate"] <= parsed["ShipDate"]) & (parsed["ShipDate"] <= parsed["DeliveryDate"]))
        if bad_c.any():
            add("chronology_violation", "R01 broken: ProcuredDate <= OrderDate <= ShipDate <= DeliveryDate.", df.index[bad_c], "medium")
    return ValidationResult(passed=len(violations) == 0, total_rows=total, violations=violations)
