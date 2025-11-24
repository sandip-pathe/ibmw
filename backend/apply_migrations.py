import asyncio
import os
from app.database import db
from app.config import get_settings

async def run_migrations():
    print(f"🔌 Connecting to database: {get_settings().database_url.split('@')[1]}")
    await db.connect()
    
    # ADD '001_create_tables.sql' TO THE START OF THIS LIST
    migration_files = [
        "migrations/001_create_tables.sql",      # <--- Added this
        "migrations/002_add_oauth_support.sql",
        "migrations/003_agentic_compliance.sql"
    ]
    
    for filename in migration_files:
        if os.path.exists(filename):
            print(f"📄 Applying {filename}...")
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    sql_content = f.read()
                    
                async with db.acquire() as conn:
                    await conn.execute(sql_content)
                    
                print(f"✅ Successfully applied {filename}")
            except Exception as e:
                # It's okay if 001 fails slightly on 'CREATE EXTENSION IF NOT EXISTS vector'
                # if it was already installed manually, but we need the tables.
                print(f"❌ Failed to apply {filename}: {e}")
        else:
            print(f"⚠️ File not found: {filename}")
            
    await db.disconnect()
    print("🏁 Migration process finished.")

if __name__ == "__main__":
    asyncio.run(run_migrations())