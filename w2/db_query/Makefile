PORT ?= 8000
BACKEND_DIR = backend
FRONTEND_DIR = frontend

.PHONY: help install dev start stop test clean format lint check frontend-install frontend-dev

help:
	@echo "DB Query Tool - Available commands:"
	@echo ""
	@echo "  make install          - Install all dependencies (backend + frontend)"
	@echo "  make dev              - Start backend development server (reload enabled)"
	@echo "  make start            - Start backend production server"
	@echo "  make frontend-install - Install frontend dependencies"
	@echo "  make frontend-dev     - Start frontend development server"
	@echo "  make stop             - Stop server (if running)"
	@echo "  make test             - Run tests"
	@echo "  make format           - Format code with black"
	@echo "  make lint             - Lint code with ruff"
	@echo "  make check            - Run format and lint checks"
	@echo "  make clean            - Clean cache and temporary files"
	@echo ""
	@echo "Environment variables:"
	@echo "  PORT                  - Server port (default: $(PORT))"

# Install dependencies
install: frontend-install
	@echo "Installing backend dependencies..."
	cd $(BACKEND_DIR) && uv sync

# Install frontend dependencies
frontend-install:
	@echo "Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install

# Start frontend development server
frontend-dev:
	@echo "Starting frontend development server..."
	cd $(FRONTEND_DIR) && npm run dev

# Development server with auto-reload
dev:
	@echo "Starting development server on port $(PORT)..."
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --port $(PORT)

# Production server
start:
	@echo "Starting production server on port $(PORT)..."
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --host 0.0.0.0 --port $(PORT)

# Stop server (if running)
stop:
	@echo "Stopping server..."
	@-pkill -f "uvicorn app.main:app" || true

# Run tests
test:
	@echo "Running tests..."
	cd $(BACKEND_DIR) && uv run pytest -v

# Format code
format:
	@echo "Formatting code..."
	cd $(BACKEND_DIR) && uv run black app/ tests/ || echo "black not installed, skipping"

# Lint code
lint:
	@echo "Linting code..."
	cd $(BACKEND_DIR) && uv run ruff check app/ tests/ || echo "ruff not installed, skipping"

# Run format and lint checks
check: format lint
	@echo "All checks completed"

# Clean cache and temporary files
clean:
	@echo "Cleaning cache files..."
	find $(BACKEND_DIR) -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type f -name "*.pyc" -delete 2>/dev/null || true
	find $(BACKEND_DIR) -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@echo "Clean completed"

# Upgrade dependencies
upgrade:
	@echo "Upgrading dependencies..."
	cd $(BACKEND_DIR) && uv sync --upgrade

# Show outdated packages
outdated:
	@echo "Checking for outdated packages..."
	cd $(BACKEND_DIR) && uv pip list --outdated

# Show installed packages
list:
	@echo "Installed packages:"
	cd $(BACKEND_DIR) && uv pip list

# Health check
health:
	@echo "Checking server health..."
	@curl -s http://localhost:$(PORT)/health | python -m json.tool || echo "Server not running"

