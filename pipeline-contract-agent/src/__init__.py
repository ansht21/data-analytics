"""Shared config + path resolution for pipeline-contract-agent.

All paths resolve relative to this project's root so the package works
identically on local Windows, Docker, and CI runners.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "contract" / "supply_orders.contract.yaml"
INCIDENTS_DIR = Path(os.getenv("INCIDENTS_DIR", str(PROJECT_ROOT / "incidents")))
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
# Sibling cleaned data this contract protects (never mutated by this project).
CLEANED_CSV = (
    PROJECT_ROOT.parent
    / "supply-chain-performance-analysis"
    / "data"
    / "Cleaned_Supplychain_Data.csv"
)
RAW_CSV = (
    PROJECT_ROOT.parent
    / "supply-chain-performance-analysis"
    / "data"
    / "Supplychain_rawData.csv"
)

API_URL = os.getenv("API_URL", "http://localhost:8000")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
