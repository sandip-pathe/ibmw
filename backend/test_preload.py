"""Test preload regulation endpoint"""
import asyncio
from pathlib import Path
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.services.preloaded_regulations import preloaded_regulation_service
from app.database import db
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("Testing preload regulation service...")
    print(f"\nDemo regulation config:")
    print(f"  Rule ID: {preloaded_regulation_service.DEMO_REGULATION['rule_id']}")
    print(f"  Title: {preloaded_regulation_service.DEMO_REGULATION['title']}")
    print(f"  File path: {preloaded_regulation_service.DEMO_REGULATION['file_path']}")
    
    # Check if PDF exists
    pdf_path = preloaded_regulation_service.DEMO_REGULATION['file_path']
    if pdf_path.exists():
        print(f"\n✅ PDF file exists at: {pdf_path}")
        print(f"   File size: {pdf_path.stat().st_size / 1024:.2f} KB")
    else:
        print(f"\n❌ PDF file NOT FOUND at: {pdf_path}")
        return
    
    # Initialize database
    print("\nConnecting to database...")
    await db.connect()
    
    print("\n" + "="*60)
    print("Loading regulation...")
    print("="*60)
    
    try:
        result = await preloaded_regulation_service.ensure_regulation_loaded()
        print("\n✅ Success!")
        print(f"Status: {result['status']}")
        print(f"Rule ID: {result['rule_id']}")
        print(f"Title: {result['title']}")
        print(f"Chunk count: {result['chunk_count']}")
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
