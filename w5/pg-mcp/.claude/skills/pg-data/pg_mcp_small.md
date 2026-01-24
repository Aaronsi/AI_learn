# pg_mcp_small Database Reference

Database: `pg_mcp_small`
Connection: `postgres://postgres:postgres@localhost:5432/pg_mcp_small`
Domain: E-commerce / Order Management System

## Overview

A small e-commerce database with customers, products, orders, and order items. Suitable for basic retail/order management queries.

## Tables

### customers (3 rows)
Customer information.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| customer_id | integer | NO | auto_increment | Primary key |
| name | text | NO | - | Customer name |
| email | text | NO | - | Email (unique) |
| created_at | timestamptz | NO | now() | Registration time |

### products (3 rows)
Product catalog.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| product_id | integer | NO | auto_increment | Primary key |
| sku | text | NO | - | Stock keeping unit (unique) |
| name | text | NO | - | Product name |
| price | numeric(10,2) | NO | - | Product price |
| stock | integer | NO | 0 | Current stock quantity |
| created_at | timestamptz | NO | now() | Creation time |

### orders (2 rows)
Customer orders.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| order_id | integer | NO | auto_increment | Primary key |
| customer_id | integer | NO | - | FK to customers |
| status | order_status | NO | 'pending' | Order status enum |
| order_date | date | NO | - | Order date |
| total | numeric(12,2) | NO | 0 | Order total |

### order_items (4 rows)
Line items in orders.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| order_item_id | integer | NO | auto_increment | Primary key |
| order_id | integer | NO | - | FK to orders |
| product_id | integer | NO | - | FK to products |
| quantity | integer | NO | - | Quantity ordered |
| unit_price | numeric(10,2) | NO | - | Price at order time |

## Views

### active_customers
Customers who have placed at least one order.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | integer | Customer ID |
| name | text | Customer name |
| order_count | bigint | Number of orders |

```sql
SELECT c.customer_id, c.name, count(o.order_id) AS order_count
FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING count(o.order_id) > 0;
```

## Custom Types

### order_status (enum)
Values: `pending`, `paid`, `shipped`, `cancelled`

## Indexes

| Index | Table | Type | Columns |
|-------|-------|------|---------|
| customers_pkey | customers | UNIQUE | customer_id |
| customers_email_key | customers | UNIQUE | email |
| products_pkey | products | UNIQUE | product_id |
| products_sku_key | products | UNIQUE | sku |
| orders_pkey | orders | UNIQUE | order_id |
| idx_orders_date | orders | INDEX | order_date |
| order_items_pkey | order_items | UNIQUE | order_item_id |

## Foreign Keys

| Table | Column | References |
|-------|--------|------------|
| orders | customer_id | customers(customer_id) |
| order_items | order_id | orders(order_id) |
| order_items | product_id | products(product_id) |

## Common Query Patterns

1. **Get customer orders with items**: Join customers -> orders -> order_items -> products
2. **Order totals by customer**: GROUP BY customer_id with SUM
3. **Products in stock**: WHERE stock > 0
4. **Orders by status**: WHERE status = 'pending'/'paid'/'shipped'/'cancelled'
5. **Revenue by product**: Join order_items with products, GROUP BY product
