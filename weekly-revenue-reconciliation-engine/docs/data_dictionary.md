# Data Dictionary — Amazon_Sale_Report.csv (cleaned schema)

## Source
Amazon India Marketplace sales export (Kaggle CC0), 128,976 rows × 21 raw
columns, 31-Mar-2022 → 29-Jun-2022 (ISO weeks W13–W26).

## Cleaned Columns

| Column | Type | Cleaning Rule |
|:---|:---|:---|
| Order ID | str | Kept; 8,747 multi-item duplicate rows (legit line items) |
| Date | str (raw) | Kept as-is for traceability |
| parsed_date | datetime64 | `to_datetime(format="mixed")` |
| Status | str | Mapped to `financial_bucket` |
| financial_bucket | str | Net Realized / Cancellation / Return / Loss / In-Transit / Pending / Unmapped |
| Fulfilment | str | `Amazon` (FBA) or `Merchant` (FBM) |
| Sales Channel | str | marketplace channel |
| ship-service-level | str | Easy Ship / Amazon |
| Category | str | Product category (T-shirt, Shirt, …) |
| Size | str | Apparel size |
| Courier Status | str | Courier state (partial nulls in source) |
| Qty | int | Units per line |
| currency | str | Null → `INR` |
| Amount | float | Null → `0.0` (7,800 rows); INR line revenue |
| ship-city | str | Strip + UPPER; null → `UNKNOWN` |
| ship-state | str | Strip + UPPER; null → `UNKNOWN` (35 rows) |
| ship-postal-code | int | Null → 0 |
| ship-country | str | Mostly IND |
| B2B | bool | 128,104 B2C vs 872 B2B |
| fulfilled-by | str | Null where FBA → `Amazon FBA`; Merchant → `Easy Ship` |
| fiscal_week / fiscal_year / week_label | int/int/str | ISO calendar from `parsed_date` |

## Dropped Columns
`index` (CSV artifact), `New` and `PendingS` (100 % null).

## Known Data Quirks

### `Fulfilment` tracks dispatch state, not a business channel
In this Kaggle export the `Fulfilment` column is **not** a clean
Amazon-FBA-vs-Merchant channel split. It correlates with where the order sits
in the dispatch lifecycle:

| Status | Fulfilment |
|:---|:---|
| `Shipped` (77,815), `Shipping` (8) | `Amazon` (all) |
| `Shipped - Delivered to Buyer` (28,756) | `Merchant` (all) |
| `Cancelled` (18,334) | mixed (11,475 Amazon / 6,859 Merchant) |

Consequence: a "channel settlement comparison" legitimately shows
`Amazon` net realized = ₹0, because every delivered order in this export is
flagged `Merchant`. This is a property of the source data (verified directly
against the raw CSV), not a classification bug. The cockpit chart is titled
*"Settlement Split by Fulfilment Flag"* so it is not read as a channel
comparison.

### `ship-service-level` is the true channel proxy
`Expedited` (88,630) maps to `Amazon`; `Standard` (1,083 + 39,263) maps to
`Merchant`. Use `ship-service-level` if a genuine channel split is needed.

### Partial weeks at the window edges
The export window (31-Mar → 29-Jun-2022) does not align to ISO week
boundaries, so **W13 has 4 observed days** and **W26 has 3**. Both are
flagged `is_partial_week` by the engine, excluded from anomaly detection, and
rendered as hollow markers with the chart line broken — a truncated week must
never be read as a collapse to zero.

## Financial Buckets
- **Net Realized** — Shipped - Delivered to Buyer
- **Cancellation Leakage** — Cancelled
- **Return Leakage** — Returned / Returning to Seller, Rejected by Buyer
- **Loss Leakage** — Lost in Transit, Damaged
- **In-Transit** — Shipped, Picked Up, Out for Delivery, Shipping
- **Pending** — Pending, Waiting for Pick Up
- **Unmapped** — anything else (fail-soft, logged)
