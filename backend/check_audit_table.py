import asyncio
from app.database import db

async def check():
    await db.connect()
    async with db.acquire() as conn:
        result = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'audit_cases')"
        )
        print(f"audit_cases table exists: {result}")
        
        if not result:
            print("\nApplying migration 007_audit_cases.sql...")
            with open("migrations/007_audit_cases.sql", "r") as f:
                sql = f.read()
            await conn.execute(sql)
            print("✅ Migration 007 applied successfully")
    
    await db.disconnect()

asyncio.run(check())
