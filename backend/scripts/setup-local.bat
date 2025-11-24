@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Setting up Local Python Development Environment (Windows)
echo ========================================================
echo.

REM Check if Python 3.11+ is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11 or later.
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Found Python: %PYTHON_VERSION%

REM Create virtual environment
if exist "venv\" (
    echo [WARNING] Virtual environment already exists. Skipping creation.
) else (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo [INFO] Installing dependencies from requirements.txt...
pip install -r requirements.txt
echo [OK] Dependencies installed

REM Check if .env exists
if not exist ".env" (
    echo [INFO] Creating .env file from .env.example...
    copy .env.example .env
    echo [WARNING] Please update .env with your credentials before running the app
)

echo.
echo ========================================================
echo Local development environment ready!
echo ========================================================
echo.
echo Next steps:
echo   1. Activate the virtual environment:
echo      venv\Scripts\activate
echo.
echo   2. Update your .env file with credentials
echo.
echo   3. Start Docker services (Postgres ^& Redis):
echo      docker-compose up -d postgres redis
echo.
echo   4. Run migrations:
echo      docker exec -i compliance-postgres psql -U postgres -d compliance ^< migrations/001_create_tables.sql
echo.
echo   5. Seed demo data (optional):
echo      python scripts\seed_demo_data.py
echo.
echo   6. Start the FastAPI server:
echo      uvicorn app.main:app --reload
echo.
echo   7. Start the worker (in another terminal):
echo      venv\Scripts\activate
echo      rq worker --url redis://localhost:6379/0
echo.
echo Access the application:
echo   API:      http://localhost:8000
echo   Docs:     http://localhost:8000/docs
echo   Redoc:    http://localhost:8000/redoc
echo.

pause
