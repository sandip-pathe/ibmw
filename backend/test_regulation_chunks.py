"""Test regulation_chunks table"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    print("Connecting to database...")
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    # Check if table exists
    exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'regulation_chunks'
        )
    """)
    print(f"regulation_chunks table exists: {exists}")
    
    if exists:
        # Check columns
        cols = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'regulation_chunks'
            ORDER BY ordinal_position
        """)
        print("\nColumns:")
        for col in cols:
            print(f"  {col['column_name']}: {col['data_type']}")
        
        # Check row count
        count = await conn.fetchval("SELECT COUNT(*) FROM regulation_chunks")
        print(f"\nTotal rows: {count}")
        
        # Check policy_rules table too
        pr_count = await conn.fetchval("SELECT COUNT(*) FROM policy_rules")
        print(f"policy_rules rows: {pr_count}")
        
        if pr_count > 0:
            rules = await conn.fetch("SELECT rule_code, category FROM policy_rules")
            print("\nExisting rules:")
            for rule in rules:
                print(f"  {rule['rule_code']}: {rule['category']}")
    
    await conn.close()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
