-- Medium fixture: product analytics with sessions/events
-- Includes enum, composite type, indexes, view, and moderate data volume

BEGIN;
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
SET search_path TO public;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Types
CREATE TYPE device_type AS ENUM ('web', 'ios', 'android');
CREATE TYPE geo_point AS (
    lat NUMERIC(9,6),
    lon NUMERIC(9,6)
);

-- Dimension tables
CREATE TABLE dim_users (
    user_id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    country CHAR(2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE dim_devices (
    device_id SERIAL PRIMARY KEY,
    device device_type NOT NULL,
    os_version TEXT,
    app_version TEXT
);

CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL REFERENCES dim_users(user_id),
    device_id INT NOT NULL REFERENCES dim_devices(device_id),
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    location geo_point
);
CREATE INDEX idx_sessions_started_at ON sessions(started_at);

-- Fact table
CREATE TABLE events (
    event_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES dim_users(user_id),
    event_name TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_events_time ON events(event_time);
CREATE INDEX idx_events_name ON events(event_name);

-- Views
CREATE VIEW daily_active_users AS
SELECT DATE(event_time) AS event_date, COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY 1
ORDER BY 1 DESC;

CREATE VIEW event_funnel AS
SELECT user_id,
       COUNT(*) FILTER (WHERE event_name = 'view_item') AS view_item_cnt,
       COUNT(*) FILTER (WHERE event_name = 'add_to_cart') AS add_to_cart_cnt,
       COUNT(*) FILTER (WHERE event_name = 'checkout') AS checkout_cnt
FROM events
GROUP BY user_id;

-- Seed data (moderate volume)
INSERT INTO dim_users (email, country) VALUES
 ('alice@example.com','US'),
 ('bob@example.com','US'),
 ('carol@example.com','GB'),
 ('dave@example.com','DE'),
 ('eva@example.com','FR'),
 ('frank@example.com','US'),
 ('grace@example.com','CA'),
 ('heidi@example.com','AU');

INSERT INTO dim_devices (device, os_version, app_version) VALUES
 ('web', 'Chrome 122', '1.0.0'),
 ('ios', '17.3', '1.1.0'),
 ('android', '14', '1.1.0'),
 ('web', 'Firefox 118', '1.0.1');

-- Sessions
INSERT INTO sessions (user_id, device_id, started_at, ended_at, location) VALUES
 (1,1, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '30 min', (37.7749, -122.4194)),
 (2,2, NOW() - INTERVAL '1 days', NOW() - INTERVAL '1 days' + INTERVAL '25 min', (40.7128, -74.0060)),
 (3,3, NOW() - INTERVAL '1 days', NOW() - INTERVAL '1 days' + INTERVAL '40 min', (51.5074, -0.1278)),
 (4,4, NOW() - INTERVAL '12 hours', NOW() - INTERVAL '11 hours', (52.5200, 13.4050)),
 (5,1, NOW() - INTERVAL '6 hours', NOW() - INTERVAL '5 hours', (48.8566, 2.3522)),
 (6,2, NOW() - INTERVAL '3 hours', NOW() - INTERVAL '2 hours', (34.0522, -118.2437)),
 (7,3, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '90 minutes', (45.4215, -75.6972)),
 (8,4, NOW() - INTERVAL '1 hours', NOW() - INTERVAL '30 minutes', (33.8688, 151.2093));

-- Events (~80 rows)
INSERT INTO events (session_id, user_id, event_name, event_time, properties)
SELECT s.session_id, s.user_id, e.event_name, s.started_at + (i * INTERVAL '2 minutes'), e.props
FROM sessions s
JOIN (
    VALUES
        ('view_item'::text, jsonb_build_object('item_id', 1001)),
        ('add_to_cart',    jsonb_build_object('item_id', 1001)),
        ('view_item',      jsonb_build_object('item_id', 1002)),
        ('checkout',       jsonb_build_object('cart_value', 59.99)),
        ('view_item',      jsonb_build_object('item_id', 1003))
) AS e(event_name, props) ON TRUE
JOIN generate_series(0,4) AS i ON TRUE
WHERE s.user_id <= 4; -- first 4 users get 25 events each (approx)

-- Extra events for variety
INSERT INTO events (session_id, user_id, event_name, event_time, properties)
SELECT s.session_id, s.user_id, 'view_item', s.started_at + INTERVAL '10 minutes', jsonb_build_object('item_id', 2001)
FROM sessions s WHERE s.user_id IN (5,6,7,8);

INSERT INTO events (session_id, user_id, event_name, event_time, properties)
SELECT s.session_id, s.user_id, 'add_to_cart', s.started_at + INTERVAL '12 minutes', jsonb_build_object('item_id', 2001)
FROM sessions s WHERE s.user_id IN (6,7,8);

INSERT INTO events (session_id, user_id, event_name, event_time, properties)
SELECT s.session_id, s.user_id, 'checkout', s.started_at + INTERVAL '15 minutes', jsonb_build_object('cart_value', 120.00)
FROM sessions s WHERE s.user_id IN (7,8);

COMMIT;

