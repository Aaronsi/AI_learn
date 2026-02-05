# GenSlides Backend

AI-powered slide image generator using Volcano Ark's Doubao-Seed-1.8 model.

## Overview

GenSlides is a FastAPI-based backend service that generates professional slide images from markdown content using AI. It features content-based caching, style customization, and comprehensive project management.

## Architecture

The application follows a clean layered architecture:

```
API Layer (FastAPI endpoints)
    ↓
Service Layer (Business logic)
    ↓
Repository Layer (Data access)
    ↓
Storage (File system + YAML)
```

### Key Components

- **API Endpoints**: RESTful endpoints for slides, images, and styles
- **Services**: Business logic for slide management, image generation, and style handling
- **Repositories**: Data access layer for slides and images
- **Clients**: Volcano Ark API integration
- **Models**: Pydantic models for validation and serialization

## Features

- **Slide Management**: CRUD operations for slide projects
- **Image Generation**: AI-powered image generation with content-based caching
- **Style Customization**: Generate and apply custom visual styles
- **Cost Tracking**: Track API usage costs per project
- **Content Hashing**: Blake3 hashing for efficient image caching
- **Async Operations**: Full async/await support for optimal performance

## Installation

### Prerequisites

- Python 3.12 or higher
- uv (Python package manager)
- Volcano Ark API key

### Setup

1. Clone the repository and navigate to the project root directory:

```bash
cd gen-slide
```

2. Install dependencies using uv:

```bash
uv sync
```

This will create a virtual environment and install all dependencies defined in `pyproject.toml`.

3. Configure environment variables:

```bash
cd backend
cp .env.example .env
# Edit .env and add your Volcano Ark API key
```

## Configuration

Edit `.env` file with your settings:

```env
ARK_API_KEY=your_actual_api_key
ARK_API_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL_ID=doubao-seed-1-8-251228
HOST=0.0.0.0
PORT=8000
SLIDES_BASE_PATH=./slides
```

## Running the Application

### Development Mode

**Important**: Always run commands from the backend directory to ensure proper module resolution.

From the project root:

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the startup scripts from project root:

```bash
# Windows
start-backend.bat

# Linux/Mac
./start-backend.sh
```

Or run directly from backend directory:

```bash
cd backend
uv run python -m app.main
```

### Production Mode

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Note**: The `uv run` command automatically uses the virtual environment managed by uv in the project root (`.venv/`). You don't need to manually activate any virtual environment.

## API Documentation

Once running, access the interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Slides

- `GET /api/slides/{slug}` - Get project details
- `POST /api/slides/{slug}` - Create new project
- `PUT /api/slides/{slug}` - Update project title
- `PUT /api/slides/{slug}/reorder` - Reorder slides
- `POST /api/slides/{slug}/slides` - Create new slide
- `DELETE /api/slides/{slug}/slides/{sid}` - Delete slide
- `GET /api/slides/{slug}/cost` - Get total cost

### Images

- `POST /api/slides/{slug}/generate/{sid}` - Generate image for slide
- `GET /api/slides/{slug}/images/{sid}` - List images for slide
- `GET /api/slides/{slug}/images/{sid}/{hash}.jpg` - Get specific image

### Style

- `POST /api/slides/{slug}/style/generate` - Generate style reference
- `POST /api/slides/{slug}/style/select` - Select project style
- `GET /api/slides/{slug}/style` - Get current style

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry
│   ├── config.py                 # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py             # Route aggregation
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── slides.py         # Slides CRUD endpoints
│   │       ├── images.py         # Image endpoints
│   │       └── style.py          # Style endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── slide_service.py      # Slide business logic
│   │   ├── image_service.py      # Image generation logic
│   │   └── style_service.py      # Style selection logic
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── slide_repository.py   # Slide data access
│   │   └── image_repository.py   # Image file access
│   ├── models/
│   │   ├── __init__.py
│   │   ├── slide.py              # Slide models
│   │   └── api_schemas.py        # API request/response schemas
│   ├── clients/
│   │   ├── __init__.py
│   │   └── ark_client.py         # Volcano Ark API client
│   └── utils/
│       ├── __init__.py
│       ├── hash.py               # Blake3 hash utility
│       └── yaml_handler.py       # YAML file handling
├── requirements.txt
├── .env.example
└── README.md
```

## Data Storage

Projects are stored in the file system:

```
slides/
└── {slug}/
    ├── outline.yml              # Project metadata and slides
    └── images/
        └── {sid}/
            └── {hash}.jpg       # Generated images
```

## Content-Based Caching

Images are cached based on Blake3 hash of slide content:

1. When generating an image, content is hashed
2. If an image exists for that hash, it's reused (zero cost)
3. Otherwise, a new image is generated via Ark API
4. Hash ensures images stay in sync with content

## Error Handling

The application uses proper HTTP status codes:

- `200 OK` - Successful GET/PUT requests
- `201 Created` - Successful POST requests
- `204 No Content` - Successful DELETE requests
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `500 Internal Server Error` - Server errors

## Logging

Logs are written to stdout with the format:

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Development

### Code Style

- Follow PEP 8 guidelines
- Use type hints throughout
- Write docstrings in Google style
- Keep functions focused and testable

### Type Checking

```bash
mypy app --strict
```

### Testing

```bash
pytest tests/ -v
```

## Security Considerations

- API keys are loaded from environment variables
- CORS is configured for specific origins
- Input validation via Pydantic models
- No SQL injection risk (file-based storage)

## Performance Optimization

- Async/await throughout for I/O operations
- Content-based caching reduces API calls
- Immutable image URLs with long cache headers
- Efficient Blake3 hashing algorithm

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **API key errors**: Check `.env` file configuration
3. **Port conflicts**: Change PORT in `.env`
4. **Permission errors**: Check SLIDES_BASE_PATH permissions

## License

Copyright 2026. All rights reserved.

## Support

For issues and questions, please refer to the project documentation.
