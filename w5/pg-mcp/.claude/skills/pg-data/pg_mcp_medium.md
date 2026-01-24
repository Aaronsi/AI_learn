# pg_mcp_medium Database Reference

Database: `pg_mcp_medium`
Connection: `postgres://postgres:postgres@localhost:5432/pg_mcp_medium`
Domain: User Analytics / Event Tracking System

## Overview

An analytics database tracking user sessions, events, and devices. Suitable for user behavior analysis, funnel analysis, and DAU/MAU metrics.

## Tables

### dim_users (8 rows)
User dimension table.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| user_id | integer | NO | auto_increment | Primary key |
| email | text | NO | - | Email (unique) |
| country | char(2) | NO | - | Country code (ISO 2-letter) |
| created_at | timestamptz | NO | now() | Registration time |

### dim_devices (4 rows)
Device dimension table.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| device_id | integer | NO | auto_increment | Primary key |
| device | device_type | NO | - | Device type enum |
| os_version | text | YES | - | OS version string |
| app_version | text | YES | - | Application version |

### sessions (8 rows)
User sessions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| session_id | uuid | NO | gen_random_uuid() | Primary key |
| user_id | integer | NO | - | FK to dim_users |
| device_id | integer | NO | - | FK to dim_devices |
| started_at | timestamptz | NO | - | Session start time |
| ended_at | timestamptz | YES | - | Session end time |
| location | point | YES | - | Geographic location |

### events (109 rows)
User events/actions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| event_id | bigint | NO | auto_increment | Primary key |
| session_id | uuid | NO | - | FK to sessions |
| user_id | integer | NO | - | FK to dim_users |
| event_name | text | NO | - | Event name (e.g., 'view_item', 'add_to_cart', 'checkout') |
| event_time | timestamptz | NO | - | Event timestamp |
| properties | jsonb | NO | '{}' | Event properties (flexible JSON) |

## Views

### daily_active_users
Daily active user counts.

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date |
| dau | bigint | Count of distinct users |

```sql
SELECT date(event_time) AS event_date, count(DISTINCT user_id) AS dau
FROM events
GROUP BY date(event_time)
ORDER BY date(event_time) DESC;
```

### event_funnel
Conversion funnel per user.

| Column | Type | Description |
|--------|------|-------------|
| user_id | integer | User ID |
| view_item_cnt | bigint | View item events count |
| add_to_cart_cnt | bigint | Add to cart events count |
| checkout_cnt | bigint | Checkout events count |

```sql
SELECT user_id,
    count(*) FILTER (WHERE event_name = 'view_item') AS view_item_cnt,
    count(*) FILTER (WHERE event_name = 'add_to_cart') AS add_to_cart_cnt,
    count(*) FILTER (WHERE event_name = 'checkout') AS checkout_cnt
FROM events
GROUP BY user_id;
```

## Custom Types

### device_type (enum)
Values: `web`, `ios`, `android`

## Indexes

| Index | Table | Type | Columns |
|-------|-------|------|---------|
| dim_users_pkey | dim_users | UNIQUE | user_id |
| dim_users_email_key | dim_users | UNIQUE | email |
| dim_devices_pkey | dim_devices | UNIQUE | device_id |
| sessions_pkey | sessions | UNIQUE | session_id |
| idx_sessions_started_at | sessions | INDEX | started_at |
| events_pkey | events | UNIQUE | event_id |
| idx_events_time | events | INDEX | event_time |
| idx_events_name | events | INDEX | event_name |

## Foreign Keys

| Table | Column | References |
|-------|--------|------------|
| sessions | user_id | dim_users(user_id) |
| sessions | device_id | dim_devices(device_id) |
| events | session_id | sessions(session_id) |
| events | user_id | dim_users(user_id) |

## Common Query Patterns

1. **DAU/MAU**: COUNT(DISTINCT user_id) grouped by date
2. **Session duration**: ended_at - started_at
3. **Events by type**: GROUP BY event_name with COUNT
4. **Funnel analysis**: Use FILTER clause or CASE WHEN for each step
5. **User journey**: ORDER BY event_time for a user_id
6. **Country breakdown**: GROUP BY country in dim_users
7. **Device breakdown**: JOIN with dim_devices, GROUP BY device
8. **JSONB queries**: Use properties->>'key' or properties @> '{"key":"value"}'
