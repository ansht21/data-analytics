"""Typed contract loader with version + hash.

Gives the pipeline a reviewable, versioned standard:
contract version, sha256 hash, field specs, business rules.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DataContract:
    name: str
    version: str
    raw: dict
    sha256: str
    fields: dict = field(default_factory=dict)
    business_rules: list = field(default_factory=list)
    failure_policy: dict = field(default_factory=dict)

    @property
    def field_names(self) -> list[str]:
        return list(self.fields.keys())


def load_data_contract(path: str | Path) -> DataContract:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    # support both flat (our) and nested (blueprint) layouts
    if "contract" in raw and isinstance(raw["contract"], dict):
        meta = raw["contract"]
        name = str(meta.get("name", path.stem))
        version = str(meta.get("version", "1.0.0"))
        fields = raw.get("schema", {}) or raw.get("fields", {})
        rules = raw.get("business_rules", [])
        policy = raw.get("on_failure", {})
    else:
        name = str(raw.get("name", path.stem))
        version = str(raw.get("version", "1.0.0"))
        fields = raw.get("fields", {})
        rules = raw.get("business_rules", [])
        policy = raw.get("failure_policy", {})
    return DataContract(name=name, version=version, raw=raw,
                        sha256=sha, fields=fields,
                        business_rules=rules, failure_policy=policy)


def contract_info(path: str | Path) -> dict[str, Any]:
    c = load_data_contract(path)
    return {"name": c.name, "version": c.version, "sha256": c.sha256,
            "fields": len(c.fields), "rules": len(c.business_rules)}
