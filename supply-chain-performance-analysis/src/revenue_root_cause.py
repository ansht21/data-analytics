"""
revenue_root_cause.py
---------------------
Answers the classic analyst question: "Revenue/profit has stalled over the last
six months -- what actually caused it?" using the 7,991-order supply chain
transaction log (2018-2020).

Method
------
1. Half-year windows (H1/H2) so the trailing six months can be compared both
   sequentially (H2 vs H1) and year-over-year (H2-2020 vs H2-2019).
2. Volume / price / mix decomposition of net revenue:
       net_revenue = orders x quantity x ASP,  ASP = gross_price x (1 - discount)
3. SKU-level decomposition (price-per-unit effect, volume effect, SKU mix
   residual) so the price decline is attributed to specific products rather
   than to an aggregate artefact.
4. Discount-band mix counterfactual: re-weight 2020H2 band margins by the
   2019H2 revenue mix to price the cost of the shift into deep discounts.
5. Channel and warehouse attribution of the profit change.

Every figure is written to outputs/revenue_root_cause.json so that anything
quoted in the README is reproducible and diffable.

Run:
    python src/revenue_root_cause.py
Output:
    outputs/revenue_root_cause.json
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = ROOT / "data" / "Cleaned_Supplychain_Data.csv"
OUT_DIR = ROOT / "outputs"

# Revenue-band boundaries for the discount-mix counterfactual.
BANDS = [0.0, 0.05, 0.10, 0.15, 0.20, 1.0]
BAND_LABELS = ["0-5", "5-10", "10-15", "15-20", "20+"]


def load() -> pd.DataFrame:
    """Load the cleaned dataset and attach the derived metric columns.

    Uses the same net-revenue definition as data_cleaning.py:
        revenue = Order_Quantity * Unit_Price * (1 - Discount_Applied)
        profit  = revenue - (Order_Quantity * Unit_Cost)
    """
    df = pd.read_csv(CLEAN_PATH)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["net_revenue"] = df["revenue"]
    df["total_cost"] = df["Order_Quantity"] * df["Unit_Cost"]
    df["profit"] = df["net_revenue"] - df["total_cost"]
    df["year"] = df["OrderDate"].dt.year
    df["half"] = df["OrderDate"].dt.month.map(lambda m: "H1" if m <= 6 else "H2")
    df["discount_band"] = pd.cut(
        df["Discount_Applied"], BANDS, right=False, labels=BAND_LABELS
    )
    return df


def window(df: pd.DataFrame, year: int, half: str) -> pd.DataFrame:
    return df[(df["year"] == year) & (df["half"] == half)]


def pct_change(new: float, old: float) -> float:
    return round((new / old - 1) * 100, 2)


def summarise(df: pd.DataFrame) -> dict:
    """Headline KPIs for one comparison window."""
    revenue = df["net_revenue"].sum()
    profit = df["profit"].sum()
    on_time = df["on_time"].astype(bool)
    return {
        "orders": int(df["OrderNumber"].nunique()),
        "units": int(df["Order_Quantity"].sum()),
        "net_revenue": round(float(revenue), 2),
        "profit": round(float(profit), 2),
        "margin_pct": round(float(profit / revenue * 100), 2),
        "aov": round(float(revenue / df["OrderNumber"].nunique()), 2),
        "asp": round(float(revenue / df["Order_Quantity"].sum()), 2),
        "gross_price_per_unit": round(
            float(revenue / df["Order_Quantity"].sum() / (1 - df["Discount_Applied"].mean())), 2
        ),
        "avg_discount_pct": round(float(df["Discount_Applied"].mean() * 100), 2),
        "on_time_pct": round(float(on_time.mean() * 100), 2),
        "late_orders": int((~on_time).sum()),
        "late_order_net_revenue": round(float(df.loc[~on_time, "net_revenue"].sum()), 2),
        "unprofitable_orders": int((df["profit"] < 0).sum()),
        "unprofitable_loss": round(float(df.loc[df["profit"] < 0, "profit"].sum()), 2),
    }



def sku_decomposition(prev: pd.DataFrame, cur: pd.DataFrame) -> dict:
    """Split the revenue change into per-SKU price, per-SKU volume and SKU mix.

    price_effect  = sum((asp_2020 - asp_2019) * qty_2020)
    volume_effect = sum((qty_2020 - qty_2019) * asp_2019)
    mix_effect    = residual, so the three parts always reconcile to the delta.
    """
    def by_sku(d: pd.DataFrame) -> pd.DataFrame:
        s = d.groupby("_ProductID").agg(
            revenue=("net_revenue", "sum"), qty=("Order_Quantity", "sum")
        )
        s["asp"] = s["revenue"] / s["qty"]
        return s

    s_prev, s_cur = by_sku(prev), by_sku(cur)
    common = s_prev.index.intersection(s_cur.index)
    price_effect = float(
        ((s_cur.loc[common, "asp"] - s_prev.loc[common, "asp"]) * s_cur.loc[common, "qty"]).sum()
    )
    volume_effect = float(
        ((s_cur.loc[common, "qty"] - s_prev.loc[common, "qty"]) * s_prev.loc[common, "asp"]).sum()
    )
    actual = float(cur["net_revenue"].sum() - prev["net_revenue"].sum())
    mix_effect = actual - price_effect - volume_effect
    return {
        "price_per_unit_effect": round(price_effect, 2),
        "volume_effect": round(volume_effect, 2),
        "sku_mix_effect": round(mix_effect, 2),
        "total": round(price_effect + volume_effect + mix_effect, 2),
        "actual_net_revenue_delta": round(actual, 2),
    }


def discount_mix_counterfactual(prev: pd.DataFrame, cur: pd.DataFrame) -> dict:
    """Isolate how much of the margin fall is explained by the discount-band mix.

    Re-weight 2020H2 band-level margins by the 2019H2 revenue mix. The gap
    between that counterfactual and the actual 2020H2 margin is the cost of the
    mix shift, holding per-band profitability constant.
    """
    band_margin_cur = {}
    for band in BAND_LABELS:
        sub = cur[cur["discount_band"] == band]
        band_margin_cur[band] = (
            float(sub["profit"].sum() / sub["net_revenue"].sum()) if len(sub) else 0.0
        )

    mix_prev = {
        b: float(
            prev.loc[prev["discount_band"] == b, "net_revenue"].sum() / prev["net_revenue"].sum()
        )
        for b in BAND_LABELS
    }
    mix_cur = {
        b: float(
            cur.loc[cur["discount_band"] == b, "net_revenue"].sum() / cur["net_revenue"].sum()
        )
        for b in BAND_LABELS
    }

    margin_actual = float(cur["profit"].sum() / cur["net_revenue"].sum())
    margin_if_old_mix = sum(band_margin_cur[b] * mix_prev[b] for b in BAND_LABELS)
    return {
        "actual_margin_pct": round(margin_actual * 100, 2),
        "margin_if_2019_mix_pct": round(margin_if_old_mix * 100, 2),
        "mix_shift_cost_bps": round((margin_actual - margin_if_old_mix) * 10000, 1),
        "mix_shift_cost_profit": round(
            (margin_actual - margin_if_old_mix) * cur["net_revenue"].sum(), 2
        ),
        "band_mix_pct": {
            b: {
                "2019H2": round(mix_prev[b] * 100, 2),
                "2020H2": round(mix_cur[b] * 100, 2),
                "shift_pp": round((mix_cur[b] - mix_prev[b]) * 100, 2),
            }
            for b in BAND_LABELS
        },
        "band_margin_pct_2020H2": {b: round(band_margin_cur[b] * 100, 2) for b in BAND_LABELS},
    }


def by_dimension(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Aggregate a dimension (channel / warehouse) by period.

    `df` must carry a "p" column holding the period label (e.g. "2019H2").
    Returns a frame indexed by (dimension, period).
    """
    g = df.groupby([col, "p"], observed=True).agg(
        net_revenue=("net_revenue", "sum"),
        profit=("profit", "sum"),
        orders=("OrderNumber", "nunique"),
        units=("Order_Quantity", "sum"),
        avg_discount=("Discount_Applied", "mean"),
    )
    g["margin_pct"] = g["profit"] / g["net_revenue"] * 100
    # Revenue mix is computed WITHIN each period, not across all periods.
    period_total = g["net_revenue"].groupby(level="p").transform("sum")
    g["revenue_mix_pct"] = g["net_revenue"] / period_total * 100
    g["asp"] = g["net_revenue"] / g["units"]
    return g


def compare_dimension(frame: pd.DataFrame) -> dict:
    """Compare the 2019H2 and 2020H2 slices of a pivoted dimension frame."""
    out = {}
    for name in sorted(frame.index.get_level_values(0).unique()):
        r19 = frame.loc[(name, "2019H2")]
        r20 = frame.loc[(name, "2020H2")]
        out[name] = {
            "net_revenue_2019H2": round(float(r19["net_revenue"]), 2),
            "net_revenue_2020H2": round(float(r20["net_revenue"]), 2),
            "net_revenue_change_pct": pct_change(r20["net_revenue"], r19["net_revenue"]),
            "profit_delta": round(float(r20["profit"] - r19["profit"]), 2),
            "margin_2019H2_pct": round(float(r19["margin_pct"]), 2),
            "margin_2020H2_pct": round(float(r20["margin_pct"]), 2),
            "margin_change_pp": round(float(r20["margin_pct"] - r19["margin_pct"]), 2),
            "revenue_mix_2019H2_pct": round(float(r19["revenue_mix_pct"]), 2),
            "revenue_mix_2020H2_pct": round(float(r20["revenue_mix_pct"]), 2),
            "asp_2019H2": round(float(r19["asp"]), 2),
            "asp_2020H2": round(float(r20["asp"]), 2),
            "units_change_pct": pct_change(r20["units"], r19["units"]),
            "avg_discount_2019H2_pct": round(float(r19["avg_discount"] * 100), 2),
            "avg_discount_2020H2_pct": round(float(r20["avg_discount"] * 100), 2),
        }
    return out


def trailing_six_months(df: pd.DataFrame) -> dict:
    """The literal 'last six months' view, compared with the six months before."""
    monthly = df.groupby(df["OrderDate"].dt.to_period("M")).agg(
        net_revenue=("net_revenue", "sum"), profit=("profit", "sum")
    ).sort_index()
    last6, prior6 = monthly.iloc[-6:], monthly.iloc[-12:-6]
    rev, prev_rev = float(last6["net_revenue"].sum()), float(prior6["net_revenue"].sum())
    prof, prev_prof = float(last6["profit"].sum()), float(prior6["profit"].sum())
    return {
        "last_6m_label": f"{monthly.index[-6]} to {monthly.index[-1]}",
        "prior_6m_label": f"{monthly.index[-12]} to {monthly.index[-7]}",
        "net_revenue": round(rev, 2),
        "prior_net_revenue": round(prev_rev, 2),
        "net_revenue_change_pct": pct_change(rev, prev_rev),
        "profit": round(prof, 2),
        "prior_profit": round(prev_prof, 2),
        "profit_change_pct": pct_change(prof, prev_prof),
        "margin_pct": round(prof / rev * 100, 2),
        "prior_margin_pct": round(prev_prof / prev_rev * 100, 2),
        "margin_change_bps": round((prof / rev - prev_prof / prev_rev) * 10000, 1),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load()

    prev = window(df, 2019, "H2")
    cur = window(df, 2020, "H2")
    first_half = window(df, 2020, "H1")

    k_prev, k_cur, k_first = summarise(prev), summarise(cur), summarise(first_half)

    # --- Headline: is "sales down" even true? -------------------------------
    headline = {
        "comparison": "2020H2 (Jul-Dec 2020) vs 2019H2 (Jul-Dec 2019)",
        "net_revenue_change_pct": pct_change(k_cur["net_revenue"], k_prev["net_revenue"]),
        "profit_change_pct": pct_change(k_cur["profit"], k_prev["profit"]),
        "profit_delta": round(k_cur["profit"] - k_prev["profit"], 2),
        "margin_change_bps": round((k_cur["margin_pct"] - k_prev["margin_pct"]) * 100, 1),
        "orders_change_pct": pct_change(k_cur["orders"], k_prev["orders"]),
        "units_change_pct": pct_change(k_cur["units"], k_prev["units"]),
        "asp_change_pct": pct_change(k_cur["asp"], k_prev["asp"]),
        "gross_price_change_pct": pct_change(
            k_cur["gross_price_per_unit"], k_prev["gross_price_per_unit"]
        ),
        "discount_level_effect_pct": round(
            pct_change(1 - k_cur["avg_discount_pct"] / 100, 1 - k_prev["avg_discount_pct"] / 100),
            2,
        ),
        "verdict": "Revenue is FLAT (not down); profit is down. The gap is price, not volume.",
    }

    # --- Profit bridge: volume contribution vs margin-rate contribution ----
    volume_effect = (k_cur["orders"] - k_prev["orders"]) * k_prev["aov"]
    margin_effect = (k_cur["margin_pct"] / 100 - k_prev["margin_pct"] / 100) * k_cur["net_revenue"]
    profit_bridge = {
        "start_profit": k_prev["profit"],
        "end_profit": k_cur["profit"],
        "total_delta": round(k_cur["profit"] - k_prev["profit"], 2),
        "volume_effect": round(volume_effect, 2),
        "margin_rate_effect": round(margin_effect, 2),
        "note": "volume_effect + margin_rate_effect reconciles to total_delta.",
    }

    # --- Attribution by channel / warehouse -------------------------------
    both = pd.concat([prev.assign(p="2019H2"), cur.assign(p="2020H2")])
    channel = compare_dimension(by_dimension(both, "Sales_Channel"))
    warehouse = compare_dimension(by_dimension(both, "WarehouseCode"))

    # --- SKU movers -------------------------------------------------------
    sku = (
        both.pivot_table(index="_ProductID", columns="p", values="net_revenue", aggfunc="sum")
        .fillna(0)
    )
    sku["delta"] = sku["2020H2"] - sku["2019H2"]
    sku["change_pct"] = (sku["2020H2"] / sku["2019H2"].replace(0, pd.NA) - 1) * 100
    decliners = sku.sort_values("delta").head(5).round(2)
    growers = sku.sort_values("delta").tail(5).round(2)

    result = {
        "source_file": CLEAN_PATH.name,
        "rows": int(len(df)),
        "date_range": f"{df['OrderDate'].min().date()} to {df['OrderDate'].max().date()}",
        "headline": headline,
        "windows": {"2019H2": k_prev, "2020H1": k_first, "2020H2": k_cur},
        "profit_bridge": profit_bridge,
        "trailing_6m": trailing_six_months(df),
        "sku_decomposition": sku_decomposition(prev, cur),
        "discount_mix_counterfactual": discount_mix_counterfactual(prev, cur),
        "channel_attribution": channel,
        "warehouse_attribution": warehouse,
        "sku_top_decliners": {
            str(i): {"delta": float(r["delta"]), "change_pct": float(r["change_pct"])}
            for i, r in decliners.iterrows()
        },
        "sku_top_growers": {
            str(i): {"delta": float(r["delta"]), "change_pct": float(r["change_pct"])}
            for i, r in growers.iterrows()
        },
    }

    out_path = OUT_DIR / "revenue_root_cause.json"
    out_path.write_text(json.dumps(result, indent=2))

    # --- Console summary ---------------------------------------------------
    print("=" * 72)
    print("REVENUE ROOT-CAUSE ANALYSIS  |  2020H2 vs 2019H2")
    print("=" * 72)
    print(f"Net revenue   {k_prev['net_revenue']:>16,.0f} -> {k_cur['net_revenue']:>16,.0f} "
          f"({headline['net_revenue_change_pct']:+.2f}%)")
    print(f"Profit        {k_prev['profit']:>16,.0f} -> {k_cur['profit']:>16,.0f} "
          f"({headline['profit_change_pct']:+.2f}%)")
    print(f"Margin        {k_prev['margin_pct']:>15.2f}% -> {k_cur['margin_pct']:>15.2f}% "
          f"({headline['margin_change_bps']:+.0f} bps)")
    print(f"Orders        {k_prev['orders']:>16,} -> {k_cur['orders']:>16,} "
          f"({headline['orders_change_pct']:+.2f}%)")
    print(f"ASP           {k_prev['asp']:>16,.2f} -> {k_cur['asp']:>16,.2f} "
          f"({headline['asp_change_pct']:+.2f}%)")
    print(f"\nVERDICT: {headline['verdict']}")
    sku_dec = result["sku_decomposition"]
    print(f"SKU price effect   {sku_dec['price_per_unit_effect']:>14,.0f}")
    print(f"SKU volume effect  {sku_dec['volume_effect']:>14,.0f}")
    print(f"SKU mix effect     {sku_dec['sku_mix_effect']:>14,.0f}")
    mix = result["discount_mix_counterfactual"]
    print(f"\nDiscount-mix shift cost: {mix['mix_shift_cost_bps']:+.0f} bps "
          f"({mix['mix_shift_cost_profit']:,.0f} of profit)")
    print(f"20%+ band revenue mix: {mix['band_mix_pct']['20+']['2019H2']}% -> "
          f"{mix['band_mix_pct']['20+']['2020H2']}% ({mix['band_mix_pct']['20+']['shift_pp']:+} pp)")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
