# pg_mcp_large Database Reference

Database: `pg_mcp_large`
Connection: `postgres://postgres:postgres@localhost:5432/pg_mcp_large`
Domain: Warehouse / Inventory Management System

## Overview

A comprehensive warehouse and inventory management database with suppliers, warehouses, items, purchase orders, shipments, receipts, and audits. Suitable for supply chain, inventory, and procurement queries.

## Tables

### suppliers (10 rows)
Supplier/vendor information.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| supplier_id | integer | NO | auto_increment | Primary key |
| name | text | NO | - | Supplier name |
| contact_email | text | YES | - | Contact email |
| rating | integer | YES | - | Supplier rating (1-5) |
| priority | priority_level | NO | 'medium' | Priority enum |
| created_at | timestamptz | NO | now() | Creation time |

### warehouses (6 rows)
Warehouse locations.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| warehouse_id | integer | NO | auto_increment | Primary key |
| code | text | NO | - | Warehouse code (unique) |
| city | text | NO | - | City name |
| country | char(2) | NO | - | Country code (ISO) |
| capacity | integer | NO | - | Storage capacity |
| created_at | timestamptz | NO | now() | Creation time |

### items (20 rows)
Product/item catalog.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| item_id | integer | NO | auto_increment | Primary key |
| sku | text | NO | - | SKU (unique) |
| name | text | NO | - | Item name |
| category | text | NO | - | Item category |
| unit_cost | numeric(12,2) | NO | - | Cost price |
| unit_price | numeric(12,2) | NO | - | Selling price |
| created_at | timestamptz | NO | now() | Creation time |

### inventory (72 rows)
Stock levels per warehouse-item combination.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| inventory_id | integer | NO | auto_increment | Primary key |
| warehouse_id | integer | NO | - | FK to warehouses |
| item_id | integer | NO | - | FK to items |
| quantity | integer | NO | - | Current quantity |
| safety_stock | integer | NO | 10 | Minimum stock level |
| last_restocked | date | NO | CURRENT_DATE | Last restock date |

### purchase_orders (15 rows)
Purchase orders to suppliers.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| po_id | integer | NO | auto_increment | Primary key |
| supplier_id | integer | NO | - | FK to suppliers |
| warehouse_id | integer | NO | - | FK to warehouses |
| status | shipment_status | NO | 'created' | Status enum |
| po_date | date | NO | - | Order date |
| expected_date | date | YES | - | Expected delivery |
| total_cost | numeric(14,2) | NO | 0 | Total order cost |

### po_items (180 rows)
Line items in purchase orders.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| po_item_id | integer | NO | auto_increment | Primary key |
| po_id | integer | NO | - | FK to purchase_orders |
| item_id | integer | NO | - | FK to items |
| quantity | integer | NO | - | Ordered quantity |
| unit_cost | numeric(12,2) | NO | - | Unit cost at order time |

### shipments (15 rows)
Shipments for purchase orders.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| shipment_id | integer | NO | auto_increment | Primary key |
| po_id | integer | NO | - | FK to purchase_orders |
| status | shipment_status | NO | 'created' | Status enum |
| shipped_at | timestamptz | YES | - | Ship timestamp |
| delivered_at | timestamptz | YES | - | Delivery timestamp |
| tracking_no | text | YES | - | Tracking number |

### receipts (7 rows)
Receiving records for shipments.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| receipt_id | integer | NO | auto_increment | Primary key |
| shipment_id | integer | NO | - | FK to shipments |
| received_at | timestamptz | NO | now() | Receipt timestamp |
| received_by | text | NO | - | Receiver name |
| notes | text | YES | - | Receipt notes |

### audits (30 rows)
Inventory audit records.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| audit_id | bigint | NO | auto_increment | Primary key |
| warehouse_id | integer | NO | - | FK to warehouses |
| item_id | integer | NO | - | FK to items |
| counted_qty | integer | NO | - | Physical count |
| recorded_qty | integer | NO | - | System quantity |
| variance | integer | YES | - | Difference (counted - recorded) |
| audited_at | timestamptz | NO | now() | Audit timestamp |

## Views

### inventory_health
Inventory status showing safety stock levels.

| Column | Type | Description |
|--------|------|-------------|
| warehouse_code | text | Warehouse code |
| sku | text | Item SKU |
| quantity | integer | Current quantity |
| safety_stock | integer | Safety stock level |
| over_safety | integer | Quantity above safety (can be negative) |

```sql
SELECT w.code AS warehouse_code, i.sku, inv.quantity, inv.safety_stock,
       (inv.quantity - inv.safety_stock) AS over_safety
FROM inventory inv
JOIN warehouses w ON w.warehouse_id = inv.warehouse_id
JOIN items i ON i.item_id = inv.item_id;
```

### supplier_performance
Supplier metrics summary.

| Column | Type | Description |
|--------|------|-------------|
| supplier_id | integer | Supplier ID |
| name | text | Supplier name |
| po_count | bigint | Total PO count |
| avg_po_cost | numeric | Average PO cost |
| delivered_pos | bigint | Delivered PO count |

```sql
SELECT s.supplier_id, s.name, count(po.po_id) AS po_count,
       avg(po.total_cost) AS avg_po_cost,
       sum(CASE WHEN po.status = 'delivered' THEN 1 ELSE 0 END) AS delivered_pos
FROM suppliers s
LEFT JOIN purchase_orders po ON po.supplier_id = s.supplier_id
GROUP BY s.supplier_id, s.name;
```

## Custom Types

### shipment_status (enum)
Values: `created`, `in_transit`, `delivered`, `delayed`, `cancelled`

### priority_level (enum)
Values: `low`, `medium`, `high`

## Indexes

| Index | Table | Type | Columns |
|-------|-------|------|---------|
| suppliers_pkey | suppliers | UNIQUE | supplier_id |
| warehouses_pkey | warehouses | UNIQUE | warehouse_id |
| warehouses_code_key | warehouses | UNIQUE | code |
| items_pkey | items | UNIQUE | item_id |
| items_sku_key | items | UNIQUE | sku |
| inventory_pkey | inventory | UNIQUE | inventory_id |
| idx_inventory_unique | inventory | UNIQUE | warehouse_id, item_id |
| purchase_orders_pkey | purchase_orders | UNIQUE | po_id |
| po_items_pkey | po_items | UNIQUE | po_item_id |
| shipments_pkey | shipments | UNIQUE | shipment_id |
| idx_shipments_status | shipments | INDEX | status |
| receipts_pkey | receipts | UNIQUE | receipt_id |
| audits_pkey | audits | UNIQUE | audit_id |
| idx_audits_variance | audits | INDEX | variance |

## Foreign Keys

| Table | Column | References |
|-------|--------|------------|
| inventory | warehouse_id | warehouses(warehouse_id) |
| inventory | item_id | items(item_id) |
| purchase_orders | supplier_id | suppliers(supplier_id) |
| purchase_orders | warehouse_id | warehouses(warehouse_id) |
| po_items | po_id | purchase_orders(po_id) |
| po_items | item_id | items(item_id) |
| shipments | po_id | purchase_orders(po_id) |
| receipts | shipment_id | shipments(shipment_id) |
| audits | warehouse_id | warehouses(warehouse_id) |
| audits | item_id | items(item_id) |

## Common Query Patterns

1. **Low stock items**: WHERE quantity < safety_stock
2. **Inventory by warehouse**: GROUP BY warehouse_id with SUM(quantity)
3. **PO status tracking**: JOIN purchase_orders -> shipments -> receipts
4. **Supplier performance**: Aggregate POs by supplier, filter by status
5. **Audit variances**: WHERE variance != 0 or variance > threshold
6. **Items by category**: GROUP BY category
7. **Pending deliveries**: WHERE status IN ('created', 'in_transit')
8. **Cost analysis**: SUM(quantity * unit_cost) for inventory value
9. **Warehouse utilization**: Compare SUM(quantity) to capacity
