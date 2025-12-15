# DB Query Tool Backend

Database query tool backend built with FastAPI, SQLite, and PostgreSQL support.

## Features

- Database connection management
- Metadata extraction and storage
- SQL query execution with validation
- Natural language to SQL generation (using DeepSeek API)

## Setup

### Prerequisites

- Python 3.12+
- uv package manager

### Installation

1. Install dependencies:
```bash
uv sync
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and set DeepSeek_API_KEY
```

3. Run the server:
```bash
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

- `GET /api/v1/dbs` - Get all database connections
- `PUT /api/v1/dbs/{name}` - Add or update a database connection
- `GET /api/v1/dbs/{name}` - Get database metadata
- `POST /api/v1/dbs/{name}/query` - Execute SQL query
- `POST /api/v1/dbs/{name}/query/natural` - Natural language query

## Environment Variables

- `DeepSeek_API_KEY` - DeepSeek API key (required)
- `DEEPSEEK_BASE_URL` - DeepSeek API base URL (default: https://api.deepseek.com)
- `SQLITE_DB_PATH` - SQLite database path (default: ~/.db_query/db_query.db)
- `APP_PORT` - Server port (default: 8000)
- `LOG_LEVEL` - Log level (default: INFO)

