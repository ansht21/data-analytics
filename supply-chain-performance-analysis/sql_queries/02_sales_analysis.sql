-- =========================================================================
-- Project: Supply Chain Inventory Optimization & Performance Analysis
-- Script: 02_Sales_Analysis.sql
-- Description: Analyzes key business metrics, including data quality,
--              sales channel revenue, trends, warehousing efficiency,
--              and detailed profit margins.
-- =========================================================================

USE SupplyChainDB;

-- -------------------------------------------------------------------------
-- 1. Data Quality & Completeness Audit
-- Description: Scans for missing date entries to verify ETL pipeline integrity.
-- -------------------------------------------------------------------------
SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN ProcuredDate IS NULL THEN 1 ELSE 0 END) AS procured_date_nulls,
    SUM(CASE WHEN OrderDate IS NULL THEN 1 ELSE 0 END) AS order_date_nulls,
    SUM(CASE WHEN ShipDate IS NULL THEN 1 ELSE 0 END) AS ship_date_nulls,
    SUM(CASE WHEN DeliveryDate IS NULL THEN 1 ELSE 0 END) AS delivery_date_nulls
FROM SupplyChainSales;


-- -------------------------------------------------------------------------
-- 2. Sales Channel Financial Performance
-- Description: Computes total order volume, gross revenue, discount impacts,
--              net revenue, and total profit margins by channel.
-- -------------------------------------------------------------------------
SELECT
    SalesChannel,
    COUNT(OrderNumber) AS total_orders,
    SUM(OrderQuantity) AS total_units_sold,

    -- Gross Revenue before discounts
    ROUND(SUM(OrderQuantity * UnitPrice), 2) AS gross_revenue_usd,

    -- Average Discount applied to orders
    ROUND(AVG(DiscountApplied) * 100, 2) AS avg_discount_percentage,

    -- Net Revenue after discount
    ROUND(SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)), 2) AS net_revenue_usd,

    -- Total Cost
    ROUND(SUM(OrderQuantity * UnitCost), 2) AS total_cost_usd,

    -- Net Profit
    ROUND(SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) - SUM(OrderQuantity * UnitCost), 2) AS net_profit_usd,

    -- Profit Margin (%)
    ROUND(
        (SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) - SUM(OrderQuantity * UnitCost)) /
        SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)) * 100,
        2
    ) AS profit_margin_percentage
FROM SupplyChainSales
GROUP BY SalesChannel
ORDER BY net_revenue_usd DESC;


-- -------------------------------------------------------------------------
-- 3. Monthly & Seasonal Sales Trends
-- Description: Analyzes monthly transactional revenue to identify demand spikes.
-- -------------------------------------------------------------------------
SELECT
    YEAR(OrderDate) AS order_year,
    MONTH(OrderDate) AS order_month,
    COUNT(OrderNumber) AS monthly_order_count,
    ROUND(SUM(OrderQuantity * UnitPrice * (1 - DiscountApplied)), 2) AS net_revenue_usd
FROM SupplyChainSales
GROUP BY YEAR(OrderDate), MONTH(OrderDate)
ORDER BY order_year ASC, order_month ASC;


-- -------------------------------------------------------------------------
-- 4. Warehouse Operational & Delivery Efficiency
-- Description: Analyzes average delivery lead times (ShipDate to DeliveryDate)
--              and average order processing time (OrderDate to ShipDate).
-- -------------------------------------------------------------------------
SELECT
    WarehouseCode,
    COUNT(OrderNumber) AS total_orders_fulfilled,
    ROUND(AVG(DATEDIFF(ShipDate, OrderDate)), 2) AS avg_days_order_to_ship,
    ROUND(AVG(DATEDIFF(DeliveryDate, ShipDate)), 2) AS avg_days_ship_to_delivery,
    ROUND(AVG(DATEDIFF(DeliveryDate, OrderDate)), 2) AS avg_total_fulfillment_days
FROM SupplyChainSales
GROUP BY WarehouseCode
ORDER BY avg_total_fulfillment_days ASC;


-- -------------------------------------------------------------------------
-- 5. Deep-Dive Order Profitability Audit
-- Description: Evaluates individual order-level financials to detect
--              potentially unprofitable transactions due to aggressive discounting.
-- -------------------------------------------------------------------------
SELECT
    OrderNumber,
    ProductID,
    OrderQuantity,
    UnitPrice,
    DiscountApplied,
    ROUND((OrderQuantity * UnitPrice * (1 - DiscountApplied)), 2) AS order_net_revenue_usd,
    ROUND((OrderQuantity * UnitCost), 2) AS order_cost_usd,
    ROUND((OrderQuantity * UnitPrice * (1 - DiscountApplied)) - (OrderQuantity * UnitCost), 2) AS order_profit_usd,
    CASE
        WHEN (UnitPrice * (1 - DiscountApplied)) < UnitCost THEN 'UNPROFITABLE'
        ELSE 'PROFITABLE'
    END AS profitability_status
FROM SupplyChainSales
ORDER BY order_profit_usd ASC
LIMIT 10;
