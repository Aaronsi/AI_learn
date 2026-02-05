# Migration to uv Package Manager

This document explains the migration from traditional `pip` + `venv` to `uv` package manager.

## What Changed

### Before (pip + venv)
```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run
python -m app.main
```

### After (uv)
```bash
# Setup
uv sync

# Run
uv run python -m app.main
# or
uv run uvicorn backend.app.main:app --reload
```

## Benefits of uv

1. **Faster**: 10-100x faster than pip
2. **Simpler**: No need to manually manage virtual environments
3. **Reliable**: Lock file ensures reproducible builds
4. **Modern**: Built in Rust, designed for modern Python workflows

## Migration Steps

### 1. Dependencies Moved to pyproject.toml

All dependencies from `backend/requirements.txt` are now in the root `pyproject.toml`:

```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.31.0",
    "pydantic>=2.9.2",
    "pydantic-settings>=2.5.2",
    "httpx>=0.27.2",
    "pyyaml>=6.0.2",
    "blake3>=0.4.1",
    "python-multipart>=0.0.12",
]
```

### 2. Virtual Environment

- **Old**: `backend/venv/` (manually created)
- **New**: `.venv/` in project root (automatically managed by uv)

The old `backend/venv/` directory can be safely deleted:
```bash
rm -rf backend/venv
```

### 3. Running Commands

All Python commands should now be prefixed with `uv run`:

```bash
# Instead of activating venv and running python
uv run python script.py

# Instead of activating venv and running uvicorn
uv run uvicorn backend.app.main:app --reload
```

### 4. Adding Dependencies

```bash
# Add a runtime dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# This automatically updates pyproject.toml and uv.lock
```

### 5. Startup Scripts

New convenience scripts have been added:

- `start-backend.bat` (Windows)
- `start-backend.sh` (Linux/Mac)

These scripts automatically use `uv run` to start the backend server.

## Common Commands

| Task | Old Command | New Command |
|------|-------------|-------------|
| Install deps | `pip install -r requirements.txt` | `uv sync` |
| Add package | `pip install package` | `uv add package` |
| Run script | `python script.py` | `uv run python script.py` |
| Start server | `python -m app.main` | `uv run python -m app.main` |
| Update deps | `pip install --upgrade package` | `uv add package@latest` |

## Troubleshooting

### "uv: command not found"

Install uv:
- Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- Linux/Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Dependencies not found

Run `uv sync` to install all dependencies.

### Old venv conflicts

Delete the old virtual environment:
```bash
rm -rf backend/venv
```

## Documentation Updates

The following files have been updated to reflect the uv migration:

- `README.md` - Main project documentation
- `backend/README.md` - Backend setup instructions
- `backend/CLAUDE.md` - Backend development guide
- `pyproject.toml` - Python project configuration
- `uv.lock` - Locked dependency versions

## Backward Compatibility

The old `backend/requirements.txt` file is kept for reference but is no longer used. All dependency management should be done through `pyproject.toml` and `uv` commands.
