-- Large fixture: supply chain and inventory with richer schema and data
-- Includes multiple tables, views, enums, indexes, and ~100+ rows

BEGIN;
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
SET search_path TO public;

-- Types
CREATE TYPE shipment_status AS ENUM ('created', 'in_transit', 'delivered', 'delayed', 'cancelled');
CREATE TYPE priority_level AS ENUM ('low', 'medium', 'high');

-- Core tables
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    contact_email TEXT,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    priority priority_level NOT NULL DEFAULT 'medium',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE warehouses (
    warehouse_id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    city TEXT NOT NULL,
    country CHAR(2) NOT NULL,
    capacity INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE items (
    item_id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_cost NUMERIC(12,2) NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    item_id INT NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
    quantity INT NOT NULL CHECK (quantity >= 0),
    safety_stock INT NOT NULL DEFAULT 10,
    last_restocked DATE NOT NULL DEFAULT CURRENT_DATE
);
CREATE UNIQUE INDEX idx_inventory_unique ON inventory(warehouse_id, item_id);

CREATE TABLE purchase_orders (
    po_id SERIAL PRIMARY KEY,
    supplier_id INT NOT NULL REFERENCES suppliers(supplier_id),
    warehouse_id INT NOT NULL REFERENCES warehouses(warehouse_id),
    status shipment_status NOT NULL DEFAULT 'created',
    po_date DATE NOT NULL,
    expected_date DATE,
    total_cost NUMERIC(14,2) NOT NULL DEFAULT 0
);

CREATE TABLE po_items (
    po_item_id SERIAL PRIMARY KEY,
    po_id INT NOT NULL REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
    item_id INT NOT NULL REFERENCES items(item_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_cost NUMERIC(12,2) NOT NULL
);

CREATE TABLE shipments (
    shipment_id SERIAL PRIMARY KEY,
    po_id INT NOT NULL REFERENCES purchase_orders(po_id),
    status shipment_status NOT NULL DEFAULT 'created',
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    tracking_no TEXT
);
CREATE INDEX idx_shipments_status ON shipments(status);

CREATE TABLE receipts (
    receipt_id SERIAL PRIMARY KEY,
    shipment_id INT NOT NULL REFERENCES shipments(shipment_id) ON DELETE CASCADE,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    received_by TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE audits (
    audit_id BIGSERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL REFERENCES warehouses(warehouse_id),
    item_id INT NOT NULL REFERENCES items(item_id),
    counted_qty INT NOT NULL,
    recorded_qty INT NOT NULL,
    variance INT GENERATED ALWAYS AS (counted_qty - recorded_qty) STORED,
    audited_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audits_variance ON audits(variance);

-- Views
CREATE VIEW inventory_health AS
SELECT w.code AS warehouse_code,
       i.sku,
       inv.quantity,
       inv.safety_stock,
       (inv.quantity - inv.safety_stock) AS over_safety
FROM inventory inv
JOIN warehouses w ON w.warehouse_id = inv.warehouse_id
JOIN items i ON i.item_id = inv.item_id;

CREATE VIEW supplier_performance AS
SELECT s.supplier_id, s.name,
       COUNT(po.po_id) AS po_count,
       AVG(po.total_cost) AS avg_po_cost,
       SUM(CASE WHEN po.status = 'delivered' THEN 1 ELSE 0 END) AS delivered_pos
FROM suppliers s
LEFT JOIN purchase_orders po ON po.supplier_id = s.supplier_id
GROUP BY s.supplier_id, s.name;

-- Seed suppliers (10)
INSERT INTO suppliers (name, contact_email, rating, priority) VALUES
 ('Alpha Supply','alpha@supply.com',4,'high'::priority_level),
 ('Beta Traders','beta@traders.com',5,'high'::priority_level),
 ('Gamma Goods','gamma@goods.com',3,'medium'::priority_level),
 ('Delta Imports','delta@imports.com',4,'medium'::priority_level),
 ('Epsilon Wholesale','epsilon@wholesale.com',2,'low'::priority_level),
 ('Zeta Logistics','zeta@logistics.com',5,'high'::priority_level),
 ('Eta Partners','eta@partners.com',3,'medium'::priority_level),
 ('Theta Supply','theta@supply.com',4,'medium'::priority_level),
 ('Iota Distribution','iota@distribution.com',5,'high'::priority_level),
 ('Kappa Sourcing','kappa@sourcing.com',2,'low'::priority_level);

-- Warehouses (6)
INSERT INTO warehouses (code, city, country, capacity) VALUES
 ('SFO','San Francisco','US',50000),
 ('LAX','Los Angeles','US',60000),
 ('NYC','New York','US',70000),
 ('LHR','London','GB',55000),
 ('BER','Berlin','DE',45000),
 ('SYD','Sydney','AU',40000);

-- Items (20)
INSERT INTO items (sku, name, category, unit_cost, unit_price) VALUES
 ('SKU-001','Widget A','widgets',5.00,8.50),
 ('SKU-002','Widget B','widgets',6.50,10.00),
 ('SKU-003','Widget C','widgets',7.00,11.50),
 ('SKU-004','Gadget A','gadgets',12.00,18.00),
 ('SKU-005','Gadget B','gadgets',15.00,23.00),
 ('SKU-006','Gadget C','gadgets',18.00,27.00),
 ('SKU-007','Tool A','tools',9.00,14.00),
 ('SKU-008','Tool B','tools',11.00,17.00),
 ('SKU-009','Tool C','tools',13.00,20.00),
 ('SKU-010','Accessory A','accessories',3.00,6.00),
 ('SKU-011','Accessory B','accessories',4.00,7.00),
 ('SKU-012','Accessory C','accessories',4.50,7.50),
 ('SKU-013','Spare A','spares',2.50,5.00),
 ('SKU-014','Spare B','spares',3.50,6.50),
 ('SKU-015','Spare C','spares',4.00,7.00),
 ('SKU-016','Premium Widget','widgets',20.00,35.00),
 ('SKU-017','Premium Gadget','gadgets',25.00,42.00),
 ('SKU-018','Premium Tool','tools',22.00,38.00),
 ('SKU-019','Bundle Kit','kits',30.00,55.00),
 ('SKU-020','Seasonal Pack','kits',18.00,32.00);

-- Inventory (populate cross of top warehouses/items)
INSERT INTO inventory (warehouse_id, item_id, quantity, safety_stock, last_restocked)
SELECT w.warehouse_id,
       i.item_id,
       (random()*200 + 50)::INT,
       20,
       CURRENT_DATE - ((random()*30)::INT) * INTERVAL '1 day'
FROM warehouses w
JOIN items i ON i.item_id <= 12; -- first 12 items in all warehouses

-- Purchase orders (15)
INSERT INTO purchase_orders (supplier_id, warehouse_id, status, po_date, expected_date, total_cost)
VALUES
 (1,1,'delivered'::shipment_status, CURRENT_DATE - 30, CURRENT_DATE - 20, 25000),
 (2,2,'delivered'::shipment_status, CURRENT_DATE - 25, CURRENT_DATE - 15, 18000),
 (3,3,'in_transit'::shipment_status, CURRENT_DATE - 10, CURRENT_DATE + 5, 12000),
 (4,4,'created'::shipment_status, CURRENT_DATE - 5, CURRENT_DATE + 10, 9000),
 (5,5,'delayed'::shipment_status, CURRENT_DATE - 20, CURRENT_DATE - 2, 15000),
 (6,6,'delivered'::shipment_status, CURRENT_DATE - 18, CURRENT_DATE - 8, 21000),
 (7,1,'in_transit'::shipment_status, CURRENT_DATE - 7, CURRENT_DATE + 7, 8000),
 (8,2,'delivered'::shipment_status, CURRENT_DATE - 40, CURRENT_DATE - 25, 30000),
 (9,3,'delivered'::shipment_status, CURRENT_DATE - 50, CURRENT_DATE - 35, 27000),
 (10,4,'created'::shipment_status, CURRENT_DATE - 3, CURRENT_DATE + 12, 11000),
 (2,5,'delivered'::shipment_status, CURRENT_DATE - 15, CURRENT_DATE - 5, 16000),
 (3,6,'delayed'::shipment_status, CURRENT_DATE - 12, CURRENT_DATE + 2, 14000),
 (1,2,'delivered'::shipment_status, CURRENT_DATE - 45, CURRENT_DATE - 30, 19000),
 (4,3,'in_transit'::shipment_status, CURRENT_DATE - 8, CURRENT_DATE + 4, 13000),
 (5,1,'created'::shipment_status, CURRENT_DATE - 2, CURRENT_DATE + 14, 7000);

-- PO items (~60 rows)
INSERT INTO po_items (po_id, item_id, quantity, unit_cost)
SELECT po.po_id, i.item_id, (random()*50 + 10)::INT, i.unit_cost
FROM purchase_orders po
JOIN items i ON i.item_id <= 12;

-- Shipments and receipts
INSERT INTO shipments (po_id, status, shipped_at, delivered_at, tracking_no)
SELECT po_id,
       CASE WHEN status = 'delivered' THEN 'delivered'::shipment_status
            WHEN status = 'in_transit' THEN 'in_transit'::shipment_status
            ELSE 'created'::shipment_status END,
       CURRENT_TIMESTAMP - INTERVAL '5 days',
       CASE WHEN status = 'delivered' THEN CURRENT_TIMESTAMP - INTERVAL '2 days' ELSE NULL END,
       concat('TRK', po_id, lpad((random()*10000)::INT::TEXT, 5, '0'))
FROM purchase_orders;

INSERT INTO receipts (shipment_id, received_at, received_by, notes)
SELECT shipment_id,
       delivered_at + INTERVAL '2 hours',
       'system',
       'Auto-receipted'
FROM shipments
WHERE delivered_at IS NOT NULL;

-- Audits (~30 rows)
INSERT INTO audits (warehouse_id, item_id, counted_qty, recorded_qty, audited_at)
SELECT (random()*5 + 1)::INT,
       (random()*12 + 1)::INT,
       (random()*300 + 20)::INT,
       (random()*300 + 20)::INT,
       NOW() - (random()*10)::INT * INTERVAL '1 day'
FROM generate_series(1,30);

COMMIT;

