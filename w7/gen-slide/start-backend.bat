@echo off
REM Start GenSlides Backend Server

echo Starting GenSlides Backend...
echo.
echo Using uv to run the server...
echo Backend will be available at: http://localhost:8000
echo API docs will be available at: http://localhost:8000/docs
echo.

cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
