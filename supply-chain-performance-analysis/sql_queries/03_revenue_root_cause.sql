-- =========================================================================
-- Project: Supply Chain Inventory Optimization & Performance Analysis
-- Script: 03_Revenue_Root_Cause.sql
-- Description: Root-cause analysis for the question every revenue owner asks:
--              "Sales have been flat/down over the last six months -- WHY?"
--
--              Decomposes the change into volume, price and mix, then
--              attributes the margin damage to specific discount bands,
--              channels, warehouses and SKUs.
--
-- Each section states the BUSINESS QUESTION it answers, the metric used, and
-- the answer obtained from the 7,991-order dataset (2018-2020). Findings are
-- cross-referenced to the Q-numbers in this project's README and reproduce
-- the output of `python src/revenue_root_cause.py`.
--
-- Financial definitions used throughout (identical to src/data_cleaning.py):
--   net_revenue = Order_Quantity * Unit_Price * (1 - Discount_Applied)
--   profit      = net_revenue - (Order_Quantity * Unit_Cost)
--   margin      = profit / net_revenue
-- =========================================================================

USE SupplyChainDB;

-- -------------------------------------------------------------------------
-- 1. BUSINESS QUESTION: Are sales actually DOWN, or is it only profit?
-- Metric: half-year net revenue, profit, margin, order count and ASP
-- Answer: Revenue is FLAT, not down. H2-2020 net revenue is 14,068,512
--         (+0.50% vs H2-2019's 13,998,908) and orders are UP 4.94%
--         (1,499 -> 1,573). But profit FELL 4.09% (4,121,127 -> 3,952,578)
--         and margin fell 134 bps (29.44% -> 28.10%).
--         The business did not lose demand -- it lost pricing power.
-- Action: Do not run a demand-generation campaign. Fix price and mix.
--         (README Q9)
-- -------------------------------------------------------------------------
SELECT
    CASE
        WHEN MONTH(OrderDate) <= 6 THEN CONCAT(YEAR(OrderDate), '-H1')
        ELSE CONCAT(YEAR(OrderDate), '-H2')
    END AS period,
    COUNT(DISTINCT OrderNumber) AS orders,
    SUM(OrderQuantity) AS units,
    ROUND(SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)), 2) AS net_revenue,
    ROUND(SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied))
          - SUM(OrderQuantity * UnitCost), 2) AS profit,
    ROUND(
        (SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) - SUM(OrderQuantity * UnitCost)) /
        SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) * 100, 2
    ) AS margin_pct,
    ROUND(
        SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) / SUM(OrderQuantity), 2
    ) AS asp,
    ROUND(AVG(DiscountApplied) * 100, 2) AS avg_discount_pct
FROM SupplyChainSales
GROUP BY period
ORDER BY period;



-- -------------------------------------------------------------------------
-- 2. BUSINESS QUESTION: If volume grew, what exactly made revenue flat?
-- Metric: volume vs price decomposition of net revenue
--         net_revenue = orders x units x ASP, and ASP = gross_price x (1 - discount)
-- Answer: Orders +4.94% and units +4.84%, but ASP FELL 4.14%
--         (2,054.43 -> 1,969.28). Splitting ASP further: the underlying
--         gross price per unit fell 3.97% and the average discount factor
--         contributed only -0.18%. So the ASP decline is a PRICE problem,
--         not a discount-policy problem.
-- Action: Investigate price realisation per SKU and per channel before
--         touching the discount policy. (README Q9)
-- -------------------------------------------------------------------------
SELECT
    CASE
        WHEN MONTH(OrderDate) <= 6 THEN CONCAT(YEAR(OrderDate), '-H1')
        ELSE CONCAT(YEAR(OrderDate), '-H2')
    END AS period,
    COUNT(DISTINCT OrderNumber) AS orders,
    SUM(OrderQuantity) AS units,
    ROUND(SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)), 2) AS net_revenue,
    ROUND(SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) / SUM(OrderQuantity), 2) AS asp,
    ROUND(
        SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) / SUM(OrderQuantity)
        / (1 - AVG(DiscountApplied)), 2
    ) AS gross_price_per_unit,
    ROUND(AVG(DiscountApplied) * 100, 2) AS avg_discount_pct,
    -- Realised discount factor: what fraction of list price actually survives
    ROUND(1 - AVG(DiscountApplied), 4) AS realised_price_factor
FROM SupplyChainSales
GROUP BY period
ORDER BY period;


-- -------------------------------------------------------------------------
-- 3. BUSINESS QUESTION: How much of the margin loss does the shift into
--    deep discounts explain?
-- Metric: revenue mix and realised margin by discount band, half-year over half-year
-- Answer: Revenue in the 20%+ discount band grew from 13.03% to 16.79% of
--         total net revenue (+3.75 pp), while the 10-15% band fell 1.69 pp
--         and the 15-20% band fell 2.00 pp. That band realises only ~12-13%
--         margin versus ~33% in the 5-10% band. Counterfactual: holding
--         2020H2 per-band margins but reverting to the 2019H2 revenue mix
--         would have produced a 28.62% margin instead of the actual 28.10% --
--         i.e. the mix shift alone cost 52 bps of margin, about 73,617 of
--         profit on the H2-2020 revenue base.
-- Action: Enforce a product-level profit floor on deep-discount orders
--         rather than a blanket cap -- the 5-10% band is healthy. (README Q10)
-- -------------------------------------------------------------------------
SELECT
    CASE
        WHEN MONTH(OrderDate) <= 6 THEN CONCAT(YEAR(OrderDate), '-H1')
        ELSE CONCAT(YEAR(OrderDate), '-H2')
    END AS period,
    CASE
        WHEN DiscountApplied < 0.05 THEN '00-05'
        WHEN DiscountApplied < 0.10 THEN '05-10'
        WHEN DiscountApplied < 0.15 THEN '10-15'
        WHEN DiscountApplied < 0.20 THEN '15-20'
        ELSE '20+'
    END AS discount_band,
    COUNT(DISTINCT OrderNumber) AS orders,
    ROUND(SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)), 2) AS net_revenue,
    ROUND(
        (SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) - SUM(OrderQuantity * UnitCost)) /
        SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) * 100, 2
    ) AS margin_pct,
    -- Share of the period's total net revenue carried by this band
    ROUND(
        SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) /


-- -------------------------------------------------------------------------
-- 4. BUSINESS QUESTION: Which channel lost the profit?
-- Metric: net revenue, margin and revenue mix by channel, H2-2019 vs H2-2020
-- Answer: Every channel lost margin. Distributor fell hardest
--         (31.58% -> 27.41%, -4.17 pp) on 17.95% of revenue, and Online fell
--         28.30% -> 26.63% (-1.67 pp) on 30.38% of revenue -- together the
--         largest source of the profit decline. In-Store revenue itself
--         shrank 5.1% (-293,711) and its revenue mix slipped from 41.21% to
--         38.92%, so the highest-scale channel also shrank.
--         Wholesale was the only channel to grow revenue (+17.2%).
-- Action: Review Distributor and Online pricing/terms first. Do not cut
--         In-Store volume -- that channel still earns the best margin at
--         29.40%. (README Q9)
-- -------------------------------------------------------------------------
SELECT
    SalesChannel,
    SUM(CASE WHEN YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6
             THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END) AS rev_2019h2,
    SUM(CASE WHEN YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6
             THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END) AS rev_2020h2,
    ROUND(
        (SUM(CASE WHEN YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6
                  THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END)) /
        (SUM(CASE WHEN YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6
                  THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END)) * 100 - 100,
        2
    ) AS revenue_change_pct,
    ROUND(
        (SUM(CASE WHEN YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6
                  THEN OrderQuantity * UnitPrice * (1 - DiscountApplied)
                       - OrderQuantity * UnitCost ELSE 0 END)) /
        SUM(CASE WHEN YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6
                 THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END) * 100, 2
    ) AS margin_2019h2_pct,
    ROUND(
        (SUM(CASE WHEN YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6
                  THEN OrderQuantity * UnitPrice * (1 - DiscountApplied)
                       - OrderQuantity * UnitCost ELSE 0 END)) /
        SUM(CASE WHEN YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6
                 THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END) * 100, 2
    ) AS margin_2020h2_pct
FROM SupplyChainSales
WHERE (YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6)
   OR (YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6)
GROUP BY SalesChannel


-- -------------------------------------------------------------------------
-- 5. BUSINESS QUESTION: Which warehouse lost the revenue, and was it volume
--    or price?
-- Metric: net revenue, units and average discount by warehouse, H2-2019 vs H2-2020
-- Answer: WARE-PUJ1005 fell 12.8% (-347,347) and WARE-UHY1004 fell 6.2%
--         (-149,599). PUJ1005's fall is a PRICE/discount effect, not a demand
--         collapse: units fell only 4.8% while ASP fell 8.4% and its average
--         discount rose from 11.58% to 12.59%. By contrast WARE-NMK1003 grew
--         7.2% with a *lower* average discount (11.68% -> 11.15%).
-- Action: Audit pricing and discount approvals at PUJ1005 and UHY1004 --
--         the fix there is commercial, not operational. (README Q9)
-- -------------------------------------------------------------------------
SELECT
    WarehouseCode,
    ROUND(SUM(CASE WHEN YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6
              THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END), 2) AS rev_2019h2,
    ROUND(SUM(CASE WHEN YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6
              THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END), 2) AS rev_2020h2,
    ROUND(SUM(CASE WHEN YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6
              THEN OrderQuantity ELSE 0 END), 0) AS units_2019h2,
    ROUND(SUM(CASE WHEN YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6
              THEN OrderQuantity ELSE 0 END), 0) AS units_2020h2,
    ROUND(AVG(CASE WHEN YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6
              THEN DiscountApplied END) * 100, 2) AS avg_disc_2019h2_pct,
    ROUND(AVG(CASE WHEN YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6
              THEN DiscountApplied END) * 100, 2) AS avg_disc_2020h2_pct
FROM SupplyChainSales
WHERE (YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6)
   OR (YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6)
GROUP BY WarehouseCode
ORDER BY rev_2020h2 DESC;


-- -------------------------------------------------------------------------
-- 6. BUSINESS QUESTION: Which individual products lost revenue, and is the
--    loss price or volume?
-- Metric: net revenue per SKU, H2-2019 vs H2-2020, with the % change
-- Answer: The decline is broad rather than concentrated in one bad SKU.
--         The top decliners fell 34-70% each (SKU 44 -70%, SKU 31 -54%,
--         SKU 16 -53%), while a comparable set of SKUs grew 42-216%
--         (SKU 27 +216%, SKU 24 +214%, SKU 43 +149%). That simultaneous
--         loss-and-growth pattern is the signature of a PRICE/ASSORTMENT
--         change, not one failed product.
-- Action: Treat the fix as a portfolio pricing review led by the top
--         decliners, rather than delisting individual SKUs. (README Q9)
-- -------------------------------------------------------------------------
SELECT
    ProductID,
    ROUND(SUM(CASE WHEN YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6
              THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END), 2) AS rev_2019h2,
    ROUND(SUM(CASE WHEN YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6
              THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END), 2) AS rev_2020h2,
    ROUND(
        (SUM(CASE WHEN YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6
                  THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END)) /
        (SUM(CASE WHEN YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6
                  THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END)) * 100 - 100,
        2
    ) AS revenue_change_pct
FROM SupplyChainSales
WHERE (YEAR(OrderDate) = 2019 AND MONTH(OrderDate) > 6)
   OR (YEAR(OrderDate) = 2020 AND MONTH(OrderDate) > 6)
GROUP BY ProductID
HAVING rev_2019h2 > 0
ORDER BY revenue_change_pct ASC;


-- -------------------------------------------------------------------------
-- 7. BUSINESS QUESTION: Did delivery performance get worse over the same
--    period -- could lateness be driving the revenue loss?
-- Metric: on-time rate, average delivery days and late-order revenue
-- Answer: No. On-time rate went 49.4% (H2-2019) -> 52.3% (H1-2020) ->
--         48.5% (H2-2020), and average delivery days 5.53 -> 5.40 -> 5.63.
--         The H2-2020 dip is real but small, and it mirrors the same
--         network-wide pattern already identified in Q2 -- it is not a
--         new or localised failure. Late-order revenue exposure stayed
--         flat at roughly 50% of net revenue in every window.
-- Action: Do not treat delivery as the cause of the revenue plateau.
--         The two problems are independent and need separate fixes.
--         (README Q10)
-- -------------------------------------------------------------------------
SELECT
    CASE
        WHEN MONTH(OrderDate) <= 6 THEN CONCAT(YEAR(OrderDate), '-H1')
        ELSE CONCAT(YEAR(OrderDate), '-H2')
    END AS period,
    ROUND(AVG(CASE WHEN delivery_days <= 5 THEN 1 ELSE 0 END) * 100, 2) AS on_time_pct,
    ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
    COUNT(DISTINCT CASE WHEN delivery_days > 5 THEN OrderNumber END) AS late_orders,
    ROUND(SUM(CASE WHEN delivery_days > 5
              THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END), 2) AS late_revenue,
    ROUND(
        SUM(CASE WHEN delivery_days > 5
            THEN OrderQuantity * UnitPrice * (1 - DiscountApplied) ELSE 0 END) /
        SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) * 100, 2
    ) AS late_revenue_pct
FROM SupplyChainSales
GROUP BY period
ORDER BY period;


ORDER BY rev_2020h2 DESC;

        SUM(SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied))) OVER (PARTITION BY
            CASE
                WHEN MONTH(OrderDate) <= 6 THEN CONCAT(YEAR(OrderDate), '-H1')
                ELSE CONCAT(YEAR(OrderDate), '-H2')
            END) * 100, 2
    ) AS revenue_mix_pct
FROM SupplyChainSales
GROUP BY period, discount_band
ORDER BY period, discount_band;
