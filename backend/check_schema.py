import asyncio
import asyncpg
from app.config import get_settings

async def check_schema():
    settings = get_settings()
    conn = await asyncpg.connect(settings.database_url)
    
    rows = await conn.fetch("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name='code_map' 
        ORDER BY ordinal_position
    """)
    
    print("\n=== code_map table schema ===")
    for row in rows:
        print(f"{row['column_name']:25} {row['data_type']:15} ({row['udt_name']})")
    
    await conn.close()

asyncio.run(check_schema())
