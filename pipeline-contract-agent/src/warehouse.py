"""Warehouse loader (PASS path): cleaned batch -> SQLite warehouse/orders.db.

Keeps the 'destination' side of the contract real: passing batches land
in warehouse.orders with load metadata. Postgres-ready (SQLAlchemy URL swap).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .validate import normalize_headers

WAREHOUSE = Path(__file__).resolve().parents[1] / "warehouse" / "orders.db"


def load_to_warehouse(batch_csv: str | Path, batch_name: str = "") -> dict:
    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    df = normalize_headers(pd.read_csv(batch_csv, dtype=str, keep_default_na=True))
    df["_batch"] = batch_name or Path(batch_csv).name
    with sqlite3.connect(WAREHOUSE) as con:
        df.to_sql("orders", con, if_exists="append", index=False)
        n = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    return {"warehouse": str(WAREHOUSE), "batch_rows": len(df), "total_rows": int(n)}


def impact_stats() -> dict:
    if not WAREHOUSE.exists():
        return {"total_rows": 0}
    with sqlite3.connect(WAREHOUSE) as con:
        n = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        batches = con.execute("SELECT COUNT(DISTINCT _batch) FROM orders").fetchone()[0]
    return {"total_rows": int(n), "batches": int(batches)}
