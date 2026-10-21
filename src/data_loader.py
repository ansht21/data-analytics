"""11-step ingestion & cleaning pipeline for Amazon transaction logs.

Steps: drop dead columns → robust date normalization → null Amount
fill → currency defaulting → state/city standardization → postal
cleanup → fulfilment imputation → fiscal tagging → status bucket
mapping → schema validation → parquet export.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import Settings
from .logger import get_logger
from .reconciliation.revenue_classifier import classify_status
from .utils.date_utils import add_fiscal_tags, parse_mixed_dates

log = get_logger(__name__)

EXPECTED_DTYPES: dict[str, str] = {
    "Order ID": "object",
    "Status": "object",
    "Amount": "float64",
    "financial_bucket": "object",
}


def run_cleaning_pipeline(settings: Settings) -> pd.DataFrame:
    """Execute the full 11-step cleaning pipeline.

    Args:
        settings: Loaded :class:`Settings` with paths and rules.

    Returns:
        Cleaned DataFrame (also persisted to parquet).

    Raises:
        FileNotFoundError: If the raw CSV is missing.
        ValueError: If schema validation fails.
    """
    raw_path = settings.resolve(settings.data.raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw CSV not found: {raw_path}")
    log.info("Step 0: loading raw CSV (%s)", raw_path)
    df = pd.read_csv(raw_path, low_memory=False)
    log.info("Raw shape: %s rows x %s cols", *df.shape)

    # 1. Drop dead columns (only those present).
    drop = [c for c in settings.cleaning.drop_columns if c in df.columns]
    df = df.drop(columns=drop)
    log.info("Step 1: dropped dead columns %s -> shape %s", drop, df.shape)

    # 2. Robust date normalization (mixed MM-DD-YY / MM-DD-YYYY).
    df["parsed_date"] = parse_mixed_dates(df[settings.cleaning.date_column])
    n_bad = int(df["parsed_date"].isna().sum())
    log.info("Step 2: parsed dates, %d unparseable rows", n_bad)

    # 3. Handle null Amounts -> 0.0.
    amt = settings.cleaning.amount_column
    n_null_amt = int(df[amt].isna().sum())
    df[amt] = df[amt].fillna(0.0).astype(float)
    log.info("Step 3: filled %d null Amounts with 0.0", n_null_amt)

    # 4. Currency defaulting.
    if "currency" in df.columns:
        df["currency"] = df["currency"].fillna(settings.cleaning.default_currency)
        log.info("Step 4: defaulted currency to %s", settings.cleaning.default_currency)

    # 5. State / city standardization.
    for col in ("ship-state", "ship-city"):
        if col in df.columns:
            df[col] = (
                df[col].astype("object").fillna(settings.cleaning.unknown_state)
                .astype(str).str.strip().str.upper()
                .replace({"": settings.cleaning.unknown_state, "NAN": settings.cleaning.unknown_state})
            )
    log.info("Step 5: standardized ship-state / ship-city")

    # 6. Postal code cleanup.
    if "ship-postal-code" in df.columns:
        df["ship-postal-code"] = (
            pd.to_numeric(df["ship-postal-code"], errors="coerce").fillna(0).astype(int)
        )
        log.info("Step 6: postal codes cleaned")

    # 7. Fulfilment imputation.
    if "fulfilled-by" in df.columns and "Fulfilment" in df.columns:
        mask = (df["Fulfilment"] == "Amazon") & df["fulfilled-by"].isna()
        df.loc[mask, "fulfilled-by"] = "Amazon FBA"
        log.info("Step 7: imputed %d Amazon FBA fulfilled-by rows", int(mask.sum()))

    # 8. Fiscal calendar tagging (W13..W26 etc).
    df = add_fiscal_tags(
        df,
        date_col="parsed_date",
        week_col=settings.fiscal.week_column,
        year_col=settings.fiscal.year_column,
        label_col=settings.fiscal.label_column,
    )
    log.info("Step 8: fiscal weeks %s", sorted(df[settings.fiscal.label_column].dropna().unique().tolist()))

    # 9. Status -> financial bucket mapping.
    df["financial_bucket"] = df["Status"].map(
        lambda s: classify_status(str(s), settings.buckets)
    )
    log.info("Step 9: bucket distribution:\n%s", df["financial_bucket"].value_counts().to_string())

    # 10. Schema validation (fail fast).
    missing = [c for c in EXPECTED_DTYPES if c not in df.columns]
    if missing:
        raise ValueError(f"Schema validation failed, missing columns: {missing}")
    log.info("Step 10: schema validation passed")

    # 11. Parquet export.
    out_path = settings.resolve(settings.data.processed_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    log.info("Step 11: wrote cleaned parquet -> %s (%d rows)", out_path, len(df))
    return df


def load_processed(settings: Settings) -> pd.DataFrame:
    """Load the cleaned parquet, running the pipeline first if missing."""
    out_path = Path(settings.resolve(settings.data.processed_path))
    if not out_path.exists():
        return run_cleaning_pipeline(settings)
    return pd.read_parquet(out_path)
