# Backend Development Guide

IMPORTANT: This project uses **uv** for Python package management. Always use `uv` commands instead of `pip` or `venv`.

## Technology Stack

- **Language**: Python 3.12+
- **Package Manager**: uv
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Validation**: Pydantic v2
- **HTTP Client**: httpx
- **Hashing**: blake3
- **Configuration**: pydantic-settings

## Quick Start

### Installation

From the project root directory:

```bash
# Install all dependencies
uv sync

# Or add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name
```

### Running the Server

**Important**: Always run commands from the backend directory to ensure proper module resolution.

**Option 1: Using startup scripts (recommended)**

From project root:

Windows:
```bash
start-backend.bat
```

Linux/Mac:
```bash
./start-backend.sh
```

**Option 2: Using uv run directly**

From backend directory:
```bash
cd backend

# Development mode with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main module
uv run python -m app.main

# Production mode
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Why from backend directory?**
The backend code uses relative imports like `from app.api.router import api_router`. When running from the backend directory, Python can correctly resolve these imports. The `uv run` command automatically uses the virtual environment from the project root (`.venv/`), so you get the best of both worlds.

## Architecture Principles

### SOLID Principles

1. **Single Responsibility Principle (SRP)**
   - Each module has one reason to change
   - API routes handle HTTP concerns only
   - Services contain business logic
   - Repositories handle data access

2. **Open/Closed Principle (OCP)**
   - Use dependency injection for extensibility
   - Abstract base classes for repositories
   - Configuration-driven behavior

3. **Liskov Substitution Principle (LSP)**
   - Repository interfaces are substitutable
   - Service layer doesn't depend on concrete implementations

4. **Interface Segregation Principle (ISP)**
   - Small, focused interfaces
   - Clients depend only on methods they use

5. **Dependency Inversion Principle (DIP)**
   - High-level modules depend on abstractions
   - Use FastAPI's dependency injection system

### DRY (Don't Repeat Yourself)

- Eliminate code duplication
- Extract common logic into reusable functions/classes
- Use inheritance and composition appropriately
- Centralize configuration and constants
- Share common utilities across modules

### YAGNI (You Aren't Gonna Need It)

- Implement features only when required
- Avoid premature optimization
- No speculative generality
- Start simple, refactor when needed

### KISS (Keep It Simple, Stupid)

- Prefer simple solutions over complex ones
- Clear, readable code over clever code
- Straightforward data flows
- Minimal abstractions

## Code Organization

```
backend/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoint definitions
│   │       ├── slides.py    # Slide-related endpoints
│   │       └── health.py    # Health check endpoints
│   ├── services/            # Business logic layer
│   │   ├── slide_service.py
│   │   └── llm_service.py
│   ├── repositories/        # Data access layer
│   │   └── slide_repository.py
│   ├── models/              # SQLAlchemy models
│   │   └── slide.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── slide.py         # Request/response models
│   │   └── common.py        # Shared schemas
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings management
│   │   ├── database.py      # Database connection
│   │   └── dependencies.py  # DI container
│   └── utils/               # Utility functions
│       ├── errors.py        # Custom exceptions
│       └── logging.py       # Logging configuration
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
└── main.py                  # Application entry point
```

### Layer Responsibilities

**API Layer** (`app/api/routes/`)
- HTTP request/response handling
- Input validation (via Pydantic)
- Authentication/authorization
- Dependency injection
- No business logic

**Service Layer** (`app/services/`)
- Business logic implementation
- Orchestration of multiple repositories
- Transaction management
- Domain rules enforcement
- No HTTP concerns

**Repository Layer** (`app/repositories/`)
- Database queries
- Data persistence
- Query optimization
- No business logic

**Models** (`app/models/`)
- SQLAlchemy ORM models
- Database schema definition
- Relationships

**Schemas** (`app/schemas/`)
- Pydantic models for validation
- Request/response DTOs
- Data transformation

## Best Practices

### FastAPI Patterns

1. **Dependency Injection**
```python
from fastapi import Depends
from app.core.dependencies import get_slide_service

@router.post("/slides")
async def create_slide(
    request: SlideCreateRequest,
    service: SlideService = Depends(get_slide_service)
):
    return await service.create_slide(request)
```

2. **Path Operations**
- Use appropriate HTTP methods (GET, POST, PUT, DELETE)
- Return proper status codes
- Use response models for type safety

3. **Request Validation**
- Use Pydantic models for all inputs
- Leverage Field validators
- Custom validators for complex rules

### Database Patterns

1. **Async SQLAlchemy**
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_slide(db: AsyncSession, slide_id: int):
    result = await db.execute(
        select(Slide).where(Slide.id == slide_id)
    )
    return result.scalar_one_or_none()
```

2. **Session Management**
- Use FastAPI dependency for session lifecycle
- Always use async context managers
- Commit explicitly in service layer

3. **Query Optimization**
- Use eager loading for relationships
- Index frequently queried columns
- Avoid N+1 queries

## Concurrency Handling

### Async/Await Pattern

1. **All I/O operations are async**
```python
async def create_slide(self, data: SlideCreateRequest) -> Slide:
    # Database I/O
    slide = await self.repository.create(data)

    # External API call
    content = await self.llm_service.generate_content(data.topic)

    return slide
```

2. **Concurrent Operations**
```python
import asyncio

# Run multiple operations concurrently
results = await asyncio.gather(
    self.llm_service.generate_title(topic),
    self.llm_service.generate_outline(topic),
    return_exceptions=True
)
```

3. **Background Tasks**
```python
from fastapi import BackgroundTasks

@router.post("/slides")
async def create_slide(
    request: SlideCreateRequest,
    background_tasks: BackgroundTasks
):
    slide = await service.create_slide(request)
    background_tasks.add_task(send_notification, slide.id)
    return slide
```

### Thread Safety

- Use async primitives (asyncio.Lock, asyncio.Semaphore)
- Avoid shared mutable state
- Database connections are managed per request

### Rate Limiting

- Implement rate limiting for LLM API calls
- Use semaphores to control concurrency
- Queue long-running tasks

## Error Handling

### Exception Hierarchy

```python
# app/utils/errors.py

class AppException(Exception):
    """Base exception for all application errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(AppException):
    def __init__(self, resource: str, id: Any):
        super().__init__(f"{resource} with id {id} not found", 404)

class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, 400)

class LLMServiceError(AppException):
    def __init__(self, message: str):
        super().__init__(f"LLM service error: {message}", 502)
```

### Error Handling Pattern

1. **Service Layer**
```python
async def get_slide(self, slide_id: int) -> Slide:
    slide = await self.repository.get_by_id(slide_id)
    if not slide:
        raise NotFoundError("Slide", slide_id)
    return slide
```

2. **API Layer**
```python
from fastapi import HTTPException
from app.utils.errors import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )
```

3. **External Service Calls**
```python
try:
    result = await llm_client.generate(prompt)
except httpx.TimeoutException:
    raise LLMServiceError("Request timeout")
except httpx.HTTPStatusError as e:
    raise LLMServiceError(f"HTTP {e.response.status_code}")
```

### Validation Errors

- Let Pydantic handle input validation
- FastAPI automatically returns 422 for validation errors
- Add custom validators for complex rules

## Logging

### Configuration

```python
# app/utils/logging.py

import logging
import sys
from app.core.config import settings

def setup_logging():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log")
        ]
    )
```

### Logging Patterns

1. **Structured Logging**
```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Slide created",
    extra={
        "slide_id": slide.id,
        "user_id": user.id,
        "duration_ms": duration
    }
)
```

2. **Log Levels**
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical issues requiring immediate attention

3. **What to Log**
- API requests/responses (excluding sensitive data)
- Database queries (in development)
- External service calls
- Errors with full context
- Performance metrics

4. **What NOT to Log**
- Passwords or secrets
- Personal identifiable information (PII)
- Full request bodies with sensitive data

### Request Logging Middleware

```python
import time
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "status_code": response.status_code,
            "duration_ms": duration * 1000
        }
    )
    return response
```

## Testing

### Unit Tests

- Test business logic in isolation
- Mock external dependencies
- Use pytest fixtures for setup

### Integration Tests

- Test API endpoints end-to-end
- Use test database
- Test error scenarios

### Test Structure

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_slide(client: AsyncClient, db_session):
    response = await client.post(
        "/api/slides",
        json={"topic": "Test Topic"}
    )
    assert response.status_code == 201
    assert response.json()["topic"] == "Test Topic"
```

## Configuration Management

- Use environment variables
- Pydantic Settings for validation
- Separate configs for dev/test/prod
- Never commit secrets

## Security

- Validate all inputs
- Use parameterized queries (SQLAlchemy handles this)
- Implement rate limiting
- CORS configuration
- API key authentication for LLM services
