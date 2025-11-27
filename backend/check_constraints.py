import asyncio
import asyncpg
from app.config import get_settings

async def check_constraints():
    settings = get_settings()
    conn = await asyncpg.connect(settings.database_url)
    
    # Check constraints
    constraints = await conn.fetch("""
        SELECT conname, contype 
        FROM pg_constraint 
        WHERE conrelid = 'code_map'::regclass
    """)
    
    print("\n=== code_map constraints ===")
    for row in constraints:
        constraint_type = {
            'p': 'PRIMARY KEY',
            'u': 'UNIQUE',
            'f': 'FOREIGN KEY',
            'c': 'CHECK'
        }.get(row['contype'], row['contype'])
        print(f"{row['conname']:30} {constraint_type}")
    
    # Check indexes
    indexes = await conn.fetch("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'code_map'
    """)
    
    print("\n=== code_map indexes ===")
    for row in indexes:
        print(f"{row['indexname']:30}")
        print(f"  {row['indexdef']}")
    
    await conn.close()

asyncio.run(check_constraints())
