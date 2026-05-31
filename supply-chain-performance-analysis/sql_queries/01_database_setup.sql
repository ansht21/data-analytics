-- =========================================================================
-- Project: Supply Chain Inventory Optimization & Performance Analysis
-- Script: 01_Database_Setup.sql
-- Description: Creates the database schema and handles the bulk import of
--              raw supply chain transaction data.
-- =========================================================================

-- 1. Create and initialize the database
CREATE DATABASE IF NOT EXISTS SupplyChainDB;
USE SupplyChainDB;

-- 2. Drop the table if it already exists to ensure a clean setup
DROP TABLE IF EXISTS SupplyChainSales;

-- 3. Create the transactions table schema with appropriate data types
CREATE TABLE SupplyChainSales (
    OrderNumber VARCHAR(20) NOT NULL,
    SalesChannel VARCHAR(50),
    WarehouseCode VARCHAR(20),
    ProcuredDate DATE,
    OrderDate DATE,
    ShipDate DATE,
    DeliveryDate DATE,
    CurrencyCode VARCHAR(10),
    SalesTeamID INT,
    CustomerID INT,
    StoreID INT,
    ProductID INT,
    OrderQuantity INT,
    DiscountApplied DECIMAL(5,4), -- Stores discount values (e.g., 0.0500 for 5%)
    UnitCost DECIMAL(10,2),       -- Cost per unit in USD
    UnitPrice DECIMAL(10,2),      -- Selling price per unit in USD
    PRIMARY KEY (OrderNumber)
);

-- Note: MySQL require checking local_infile variables or secure_file_priv paths
-- to load local dataset files into the database.
-- SHOW VARIABLES LIKE 'secure_file_priv';

-- 4. Bulk Import Transaction Data
-- Ensure the file path matches the location of your raw dataset.
-- Replace 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Supplychain_Data.csv'
-- with the appropriate file path.
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Supplychain_Data.csv'
INTO TABLE SupplyChainSales
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    OrderNumber,
    SalesChannel,
    WarehouseCode,
    @ProcuredDate,
    @OrderDate,
    @ShipDate,
    @DeliveryDate,
    CurrencyCode,
    SalesTeamID,
    CustomerID,
    StoreID,
    ProductID,
    OrderQuantity,
    DiscountApplied,
    UnitCost,
    UnitPrice
)
SET
    ProcuredDate = STR_TO_DATE(@ProcuredDate, '%Y-%m-%d'),
    OrderDate = STR_TO_DATE(@OrderDate, '%Y-%m-%d'),
    ShipDate = STR_TO_DATE(@ShipDate, '%Y-%m-%d'),
    DeliveryDate = STR_TO_DATE(@DeliveryDate, '%Y-%m-%d');

-- 5. Data Validation Check
SELECT COUNT(*) AS total_rows_imported FROM SupplyChainSales;
