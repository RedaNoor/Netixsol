# Enterprise Analytics Pipeline using AdventureWorks

## Project Documentation Report

**Author:** Rida Noor  
**Database:** AdventureWorks (PostgreSQL)  
**Language:** SQL (PostgreSQL)  
**Tools:** PostgreSQL, pgAdmin 4, Jupyter Notebook, Python, Pandas, SQLAlchemy, Matplotlib

---

# Table of Contents

- Introduction
- Project Objectives
- Scope
- Tools and Technologies
- Database Overview
- Methodology
- System Architecture
- Implementation
- KPI Layer
- Executive Dashboard
- Analysis & Business Insights
- Challenges Faced
- Screenshots
- Conclusion

---

# Introduction

This project implements a reusable enterprise analytics layer on top of the AdventureWorks operational database. Instead of querying transactional tables directly for every business report, the project introduces a multi-stage SQL pipeline that transforms operational data into reusable analytical datasets.

The solution separates operational processing from business reporting by introducing dedicated **analytics** and **kpi** schemas. Materialized views are used for computationally intensive transformations, while KPI views generate reusable business metrics from these datasets. Finally, an executive summary consolidates organization-wide performance indicators into a single dashboard-ready view.

The project demonstrates advanced SQL concepts including:

- Common Table Expressions (CTEs)
- Materialized Views
- Window Functions
- Ranking Functions
- Conditional Aggregation
- CASE Expressions
- Schema-based Data Organization

---

# Project Objectives

The primary objectives of this project were to:

- Build a reusable analytics layer without modifying the AdventureWorks operational database.
- Design a chained SQL pipeline where every stage depends on previous transformations.
- Separate raw transactional data from reporting datasets.
- Generate reusable KPIs across multiple business domains.
- Demonstrate advanced SQL techniques including:
  - Window Functions
  - Ranking Functions
  - Common Table Expressions (CTEs)
  - Conditional Aggregation
  - CASE WHEN logic
  - Materialized Views
- Produce an executive summary suitable for dashboards and business reporting.

---

# Scope

The project analyzes the AdventureWorks enterprise database across multiple functional areas, including:

- Sales
- Customers
- Products
- Employees
- Sales Territories
- Inventory
- Purchasing
- Vendors

The project does not modify any operational tables. All analytical transformations are implemented within dedicated schemas.

---

# Tools and Technologies

| Tool | Purpose |
|------|----------|
| PostgreSQL | Database Management System |
| pgAdmin 4 | SQL Development |
| SQL | Data Transformation & KPI Generation |
| AdventureWorks | Enterprise Sample Database |
| Python | Dashboard Development |
| Pandas | Data Analysis |
| SQLAlchemy | Database Connectivity |
| Matplotlib | Data Visualization |

---

# Database Overview

AdventureWorks is a sample enterprise database representing a manufacturing and retail organization.

## Primary Schemas

- Sales
- Production
- Purchasing
- Person
- HumanResources

## Major Tables Used

- Sales.SalesOrderHeader
- Sales.SalesOrderDetail
- Sales.Customer
- Production.Product
- Production.ProductInventory
- Sales.SalesPerson
- Sales.SalesTerritory
- Purchasing.Vendor
- Purchasing.PurchaseOrderHeader
- Purchasing.PurchaseOrderDetail

---

# Methodology

The project follows a layered analytics architecture.

## Stage 0 – Schema Creation

Two dedicated schemas are created:

- analytics
- kpi

This separates analytical objects from the operational database.

---

## Stage 1 – Analytics Layer

Stage 1 builds reusable **Materialized Views**.

### Analytics Views

- analytics.vw_sales_line_analytics
- analytics.vw_customer_analytics
- analytics.vw_product_analytics
- analytics.vw_employee_analytics
- analytics.vw_territory_analytics
- analytics.vw_inventory_analytics
- analytics.vw_purchase_line_analytics
- analytics.vw_vendor_analytics

Indexes are created on frequently queried columns to improve reporting performance.

---

## Stage 2 – KPI Layer

Business KPIs are generated from the analytics layer.

### Sales KPIs

- Monthly Revenue
- Quarterly Revenue
- Best & Worst Products

### Customer KPIs

- Customer Segmentation
- Customer Lifetime Value
- Customer Retention

### Product KPIs

- Product Profitability
- Category Performance
- Product Rankings

### Employee KPIs

- Salesperson Rankings
- Employee Revenue Contribution

### Territory KPIs

- Regional Revenue
- Regional Growth

### Inventory KPIs

- Inventory Health
- Low Stock Products

### Purchasing KPIs

- Supplier Performance
- Purchasing Trends

---

## Stage 3 – Executive Dashboard

A single executive summary view combines KPIs from all business domains into one dashboard-ready dataset.

---

# System Architecture

```text
AdventureWorks Database
        │
        ▼
Stage 1 (analytics schema)
────────────────────────────────────
Sales Analytics
Customer Analytics
Product Analytics
Employee Analytics
Territory Analytics
Inventory Analytics
Purchase Analytics
Vendor Analytics
        │
        ▼
Stage 2 (kpi schema)
────────────────────────────────────
Revenue KPIs
Customer KPIs
Product KPIs
Employee KPIs
Territory KPIs
Inventory KPIs
Supplier KPIs
        │
        ▼
Stage 3
────────────────────────────────────
Executive Summary View
        │
        ▼
Python Notebook
Executive Dashboard
```

---

# Implementation

## Stage 1

The analytics layer contains eight materialized views that transform raw transactional data into reusable analytical datasets.

These views calculate:

- Revenue
- Cost
- Margin
- Customer Metrics
- Product Performance
- Employee Performance
- Territory Performance
- Inventory Status
- Purchasing Analytics
- Vendor Performance

---

## Stage 2

The KPI layer converts analytical datasets into business-ready metrics.

Examples include:

### Revenue Analysis

- Monthly Revenue Trends
- Quarterly Revenue Trends
- Month-over-Month Growth

### Customer Analytics

- Customer Segmentation (RFM)
- Customer Lifetime Value
- Customer Retention

### Product Analytics

- Product Profitability
- Product Rankings
- Category Performance

### Employee Analytics

- Salesperson Rankings
- Revenue Contribution

### Territory Analytics

- Regional Revenue
- Regional Growth

### Inventory Analytics

- Inventory Health
- Low Stock Products

### Purchasing Analytics

- Supplier Performance
- Purchasing Trends

---

## Stage 3

The Executive Summary View reports:

- Total Revenue
- Total Margin
- Overall Margin Percentage
- Purchasing Customers
- Registered Customers
- Latest Monthly Revenue
- Month-over-Month Growth
- Top Performing Territory
- Best Performing Product
- Customer Retention Rate

---

# Advanced SQL Features Used

This project demonstrates several advanced SQL techniques:

- Common Table Expressions (CTEs)
- Materialized Views
- Window Functions
  - LAG()
  - SUM() OVER()
  - ROW_NUMBER()
  - RANK()
  - DENSE_RANK()
  - NTILE()
- CASE Expressions
- Conditional Aggregation
- Aggregate Functions
- Date Functions
- Indexing
- Schema Design
- Layered SQL Pipeline

---

# Analysis

The SQL pipeline produces reusable analytical datasets that are consumed directly by a Jupyter Notebook.

The notebook visualizes:

- Monthly Revenue Trends
- Product Performance
- Customer Segmentation
- Customer Retention
- Salesperson Rankings
- Regional Revenue
- Inventory Health
- Executive KPI Summary

All business calculations are implemented inside SQL, allowing Python to focus solely on visualization and reporting.

---

# Business Insights

The analytics pipeline provides valuable business insights, including:

- Monthly and quarterly revenue trends.
- Identification of high-value and at-risk customers through RFM segmentation.
- Ranking of products based on revenue and profitability.
- Performance comparison of salespersons across territories.
- Regional sales performance and year-over-year growth.
- Inventory health monitoring for stock replenishment decisions.
- Supplier evaluation using rejection rates and on-time delivery metrics.
- Executive-level KPI reporting through a consolidated dashboard.

---

# Challenges Faced

During development, several challenges were addressed:

- Designing a reusable analytics pipeline instead of isolated SQL queries.
- Managing dependencies between materialized views and KPI views.
- Preventing divide-by-zero errors using `NULLIF()`.
- Improving performance through indexing.
- Reusing analytical datasets across multiple KPIs.
- Maintaining the correct refresh order for dependent materialized views.

---

# Screenshots

Include the following screenshots in the report:

1. AdventureWorks Database in pgAdmin
2. Successful SQL Pipeline Execution
3. `analytics.vw_sales_line_analytics`
4. Monthly Revenue KPI
5. Product Rankings
6. Salesperson Rankings
7. Customer Segmentation
8. Regional Revenue
9. Inventory Health
10. Executive Summary View

---

# Conclusion

This project successfully implements a scalable enterprise analytics framework using PostgreSQL and the AdventureWorks database. By separating operational data from reporting through dedicated **analytics** and **kpi** schemas, the solution improves maintainability, reusability, and performance.

Materialized views reduce repeated computation, while layered KPI views provide standardized business metrics across sales, customers, products, employees, territories, inventory, and purchasing. The final executive summary consolidates organization-wide performance indicators into a single reporting layer suitable for dashboards and executive decision-making.

The project demonstrates practical application of advanced SQL concepts, efficient data modeling techniques, and a complete end-to-end analytics pipeline capable of supporting business intelligence and future analytical extensions.