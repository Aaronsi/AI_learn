-- Small fixture: lightweight commerce snapshot
-- Recreates schema and seeds minimal data

BEGIN;
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
SET search_path TO public;

-- Types
CREATE TYPE order_status AS ENUM ('pending', 'paid', 'shipped', 'cancelled');

-- Tables
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    status order_status NOT NULL DEFAULT 'pending',
    order_date DATE NOT NULL,
    total NUMERIC(12,2) NOT NULL DEFAULT 0
);
CREATE INDEX idx_orders_date ON orders(order_date);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10,2) NOT NULL
);

-- View
CREATE VIEW active_customers AS
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) > 0;

-- Seed data
INSERT INTO customers (name, email) VALUES
 ('Alice','alice@example.com'),
 ('Bob','bob@example.com'),
 ('Carol','carol@example.com');

INSERT INTO products (sku, name, price, stock) VALUES
 ('SKU-100', 'Notebook', 5.50, 200),
 ('SKU-200', 'Pen', 1.20, 500),
 ('SKU-300', 'Backpack', 35.00, 50);

INSERT INTO orders (customer_id, status, order_date, total) VALUES
 (1, 'paid', CURRENT_DATE - 5, 46.70),
 (2, 'shipped', CURRENT_DATE - 2, 42.20);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
 (1, 1, 2, 5.50),
 (1, 3, 1, 35.00),
 (2, 2, 10, 1.20),
 (2, 1, 1, 5.50);

COMMIT;

