"""Daily-batch simulator with drift injection.

Copies N rows from the real raw CSV into data/batches/.
--inject-drift corrupts rows on demand so failures are demoable:
  dates  -> 2026-10-04 ISO instead of 26/10/04 slashes (article example)
  nulls  -> empty _CustomerID (article example)
  text   -> 'twelve' inside Unit Price (article example)
  mode   -> unapproved Sales_Channel value
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import RAW_CSV  # noqa: E402

BATCHES = Path(__file__).resolve().parents[1] / "data" / "batches"


def corrupt(df: pd.DataFrame, drift: str) -> pd.DataFrame:
    df = df.copy()
    idx = df.index
    if drift in ("dates", "all"):
        df.loc[idx[1], "OrderDate"] = "2026-10-04"
        if len(idx) > 4:
            df.loc[idx[4], "ShipDate"] = "2026-10-05"
    if drift in ("nulls", "all"):
        for i in (2, 5, 7):
            if i < len(idx):
                df.loc[idx[i], "_CustomerID"] = ""
    if drift in ("text", "all"):
        if len(idx) > 3:
            df.loc[idx[3], "Unit Price"] = "twelve"
        if len(idx) > 6:
            df.loc[idx[6], "Unit Cost"] = "FREE"
    if drift in ("mode", "all"):
        if len(idx) > 0:
            df.loc[idx[0], "Sales Channel"] = "Drone-Delivery"
    return df


def main() -> int:
    ap = argparse.ArgumentParser(description="Simulate one daily batch.")
    ap.add_argument("--rows", type=int, default=40)
    ap.add_argument("--inject-drift", default="none",
                    choices=["none", "dates", "nulls", "text", "mode", "all"])
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    BATCHES.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW_CSV, dtype=str, keep_default_na=True)
    batch = df.sample(min(args.rows, len(df)), random_state=args.seed).reset_index(drop=True)
    if args.inject_drift != "none":
        batch = corrupt(batch, args.inject_drift)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    out = BATCHES / f"orders_batch_{stamp}_{args.inject_drift}.csv"
    batch.to_csv(out, index=False)
    print(f"batch: {out} ({len(batch)} rows, drift={args.inject_drift})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
