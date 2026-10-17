"""Failure trigger: quarantine bad batches + preserve audit trail.

On validation FAIL: copies the offending batch into
incidents/<timestamp>_<batch>/, writes validation.json + manifest.json.
On PASS: returns a pass receipt (nothing quarantined).
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import INCIDENTS_DIR
from .validate import ValidationResult


@dataclass
class TriggerOutcome:
    status: str  # "passed" | "quarantined"
    incident_dir: Path | None
    validation: dict


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def handle_result(batch_path: str | Path, result: ValidationResult,
                  incidents_dir: str | Path = INCIDENTS_DIR) -> TriggerOutcome:
    batch_path = Path(batch_path)
    if result.passed:
        return TriggerOutcome("passed", None, result.to_dict())
    folder = Path(incidents_dir) / f"{_stamp()}_{batch_path.stem}"
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(batch_path, folder / f"batch__{batch_path.name}")
    (folder / "validation.json").write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    manifest = {
        "batch_file": batch_path.name, "contract": "contract/supply_orders.contract.yaml",
        "total_rows": result.total_rows, "failed_rules": [v.rule_id for v in result.violations],
        "quarantined_at_utc": _stamp(),
        "downstream_blocked": True,
        "note": "Cleaned data NOT overwritten. Fix forward via agent + MR, then re-ingest.",
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return TriggerOutcome("quarantined", folder, result.to_dict())
