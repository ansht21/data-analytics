"""Build controlled demo fixtures from the real raw supply-chain CSV."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT.parent / "supply-chain-performance-analysis" / "data" / "Supplychain_rawData.csv"
OUT = ROOT / "fixtures"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW, dtype=str, keep_default_na=True)
    print(f"raw: {len(df)} rows x {len(df.columns)} cols")
    good = df.head(30).copy()
    good.to_csv(OUT / "good_sample.csv", index=False)
    bad_nulls = df.head(12).copy()
    bad_nulls.loc[bad_nulls.index[2], "_CustomerID"] = ""
    bad_nulls.loc[bad_nulls.index[5], "_CustomerID"] = ""
    bad_nulls.loc[bad_nulls.index[7], "_CustomerID"] = ""
    bad_nulls.to_csv(OUT / "bad_nulls.csv", index=False)
    bad_dates = df.head(12).copy()
    bad_dates.loc[bad_dates.index[1], "OrderDate"] = "2026-10-04"
    bad_dates.loc[bad_dates.index[4], "ShipDate"] = "2026-10-05"
    bad_dates.to_csv(OUT / "bad_dates.csv", index=False)
    bad_money = df.head(12).copy()
    bad_money.loc[bad_money.index[3], "Unit Price"] = "twelve"
    bad_money.loc[bad_money.index[6], "Unit Cost"] = "FREE"
    bad_money.to_csv(OUT / "bad_money.csv", index=False)
    bad_chrono = df.head(12).copy()
    # swap ship/delivery to break chronology on row 0
    tmp = bad_chrono.loc[bad_chrono.index[0], "ShipDate"]
    bad_chrono.loc[bad_chrono.index[0], "ShipDate"] = bad_chrono.loc[bad_chrono.index[0], "DeliveryDate"]
    bad_chrono.loc[bad_chrono.index[0], "DeliveryDate"] = tmp
    bad_chrono.to_csv(OUT / "bad_chronology.csv", index=False)
    for f in sorted(OUT.glob("*.csv")):
        print(f"wrote {f.name} ({sum(1 for _ in open(f, encoding='utf-8'))-1} rows)")

if __name__ == "__main__":
    main()
