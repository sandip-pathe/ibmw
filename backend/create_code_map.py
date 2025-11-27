"""
Apply code_map migration with all required fields and constraints.
"""
import asyncio
import asyncpg
from app.config import get_settings

settings = get_settings()

async def create_code_map_table():
    print("🔌 Connecting to database...")
    conn = await asyncpg.connect(settings.database_url)
    
    try:
        # Create table with all required columns
        sql = """
        -- Code Map Table for Repository Indexing (Complete Schema)
        CREATE TABLE IF NOT EXISTS code_map (
            chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            repo_id UUID NOT NULL REFERENCES repos(repo_id) ON DELETE CASCADE,
            file_path TEXT NOT NULL,
            language VARCHAR(50),
            start_line INTEGER,
            end_line INTEGER,
            chunk_text TEXT NOT NULL,
            chunk_hash VARCHAR(64) NOT NULL,
            file_hash VARCHAR(64),
            ast_node_type VARCHAR(50),
            nl_summary TEXT,
            embedding vector(1536),
            metadata JSONB DEFAULT '{}',
            call_links JSONB DEFAULT '[]',
            variables JSONB DEFAULT '{}',
            config_keys JSONB DEFAULT '{}',
            semantic_tags JSONB DEFAULT '[]',
            previous_hash VARCHAR(64),
            delta_type VARCHAR(20),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Add missing columns if table already exists (idempotent migration)
        ALTER TABLE code_map ADD COLUMN IF NOT EXISTS call_links JSONB DEFAULT '[]';
        ALTER TABLE code_map ADD COLUMN IF NOT EXISTS variables JSONB DEFAULT '{}';
        ALTER TABLE code_map ADD COLUMN IF NOT EXISTS config_keys JSONB DEFAULT '{}';
        ALTER TABLE code_map ADD COLUMN IF NOT EXISTS semantic_tags JSONB DEFAULT '[]';
        ALTER TABLE code_map ADD COLUMN IF NOT EXISTS previous_hash VARCHAR(64);
        ALTER TABLE code_map ADD COLUMN IF NOT EXISTS delta_type VARCHAR(20);

        -- Create UNIQUE constraint on chunk_hash (required for ON CONFLICT)
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'code_map_chunk_hash_unique' 
                AND conrelid = 'code_map'::regclass
            ) THEN
                ALTER TABLE code_map ADD CONSTRAINT code_map_chunk_hash_unique UNIQUE (chunk_hash);
            END IF;
        END $$;

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_code_map_repo ON code_map(repo_id);
        CREATE INDEX IF NOT EXISTS idx_code_map_file ON code_map(file_path);
        CREATE INDEX IF NOT EXISTS idx_code_map_hash ON code_map(chunk_hash);
        CREATE INDEX IF NOT EXISTS idx_code_map_embedding ON code_map USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        """
        
        await conn.execute(sql)
        print("✅ code_map table schema updated successfully!")
        print("   ✓ Added columns: call_links, variables, config_keys, semantic_tags, previous_hash, delta_type")
        print("   ✓ Created UNIQUE constraint on chunk_hash")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_code_map_table())
