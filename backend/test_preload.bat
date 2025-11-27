@echo off
REM Test Preload Regulation Script
REM This script tests loading the demo regulation into the database

echo ========================================
echo Testing Preload Regulation Service
echo ========================================

cd /d %~dp0
call venv\Scripts\activate.bat

python -c "import asyncio; from app.services.preloaded_regulations import preloaded_regulation_service; from app.database import db; exec('async def test():\n    await db.connect()\n    result = await preloaded_regulation_service.ensure_regulation_loaded()\n    print(\"Result:\", result)\n    async with db.acquire() as conn:\n        count = await conn.fetchval(\"SELECT COUNT(*) FROM regulation_chunks WHERE rule_id = $1\", \"RBI-PA-MD-2020\")\n        print(f\"Chunks in DB: {count}\")\n\nasyncio.run(test())')"

echo.
echo ========================================
echo Test Complete
echo ========================================
pause
