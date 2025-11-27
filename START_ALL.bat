@echo off
echo ============================================
echo Starting Fintech Compliance Engine
echo ============================================
echo.

REM Kill existing processes
echo [0/4] Stopping existing services...
taskkill /FI "WindowTitle eq Backend API*" /F >nul 2>&1
taskkill /FI "WindowTitle eq RQ Worker*" /F >nul 2>&1
taskkill /FI "WindowTitle eq Frontend*" /F >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start Redis
echo [1/4] Starting Redis...
cd /d "%~dp0"
docker compose up -d redis
timeout /t 3 /nobreak >nul

REM Start Backend
echo [2/4] Starting Backend API...
start "Backend API" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

REM Start Worker
echo [3/4] Starting Worker...
start "RQ Worker" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && python -m app.workers.indexing_worker"
timeout /t 3 /nobreak >nul

REM Start Frontend
echo [4/4] Starting Frontend...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo All services started!
echo ============================================
echo.
echo Redis:    docker (port 6379)
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo Worker:   Running in background
echo.
echo Press any key to exit this window...
pause >nul
