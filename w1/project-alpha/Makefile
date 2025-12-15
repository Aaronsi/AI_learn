PORT ?= 8000

.PHONY: help w1-install w1-backend-install w1-frontend-install w1-backend-dev w1-frontend-dev w1-start-app w1-dev

help:
	@echo "Available targets:"
	@echo "  w1-install          Install all dependencies (backend + frontend)"
	@echo "  w1-backend-install  Install backend deps via uv"
	@echo "  w1-frontend-install Install frontend deps via npm"
	@echo "  w1-backend-dev      Start FastAPI dev server (PORT=$(PORT))"
	@echo "  w1-frontend-dev     Start Vite dev server"
	@echo "  w1-start-app        Alias for w1-backend-dev"
	@echo "  w1-dev              Start backend and frontend (parallel)"

w1-install: w1-backend-install w1-frontend-install

w1-backend-install:
	cd backend && uv sync

w1-frontend-install:
	npm --prefix frontend install

w1-backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --port $(PORT)

w1-frontend-dev:
	npm --prefix frontend run dev

w1-start-app: w1-backend-dev

w1-dev:
	$(MAKE) -j2 w1-backend-dev w1-frontend-dev

