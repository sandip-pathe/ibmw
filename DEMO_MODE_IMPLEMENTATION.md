# Demo Mode Implementation - Summary

## Overview
The compliance engine has been updated to use a **preloaded RBI Payment Aggregator regulation** for the hackathon demo, instead of requiring users to upload PDF files.

---

## Backend Changes

### 1. New Service: PDF Processor
**File:** `backend/app/services/pdf_processor.py`

**Purpose:** Extract and structure text from regulatory PDF files

**Key Methods:**
- `extract_text(pdf_path)` - Extracts all text from PDF using pypdf/PyPDF2
- `structure_sections(text)` - Detects numbered sections (e.g., "1.2 Introduction")
- `chunk_sections(sections, max_chunk_size=1000)` - Splits sections into semantic chunks

**Features:**
- Regex-based section detection: `r'^(\d+\.?\d*\.?\d*)\s+([A-Z][^\n]+)'`
- Paragraph-preserving chunking
- Maintains section context in each chunk

---

### 2. New Service: Preloaded Regulations
**File:** `backend/app/services/preloaded_regulations.py`

**Purpose:** Manage the single hardcoded demo regulation

**Configuration:**
```python
DEMO_REGULATION = {
    "rule_id": "RBI-PA-MD-2020",
    "title": "Master Direction on Regulation of Payment Aggregator",
    "category": "payment_aggregator",
    "regulatory_body": "RBI",
    "effective_date": "2020-03-17",
    "compliance_tag": "RBI-Payment-Aggregator",
    "file_path": Path(r"C:\Users\sandi\Downloads\Master Direction on Regulation of Payment Aggregator (PA).pdf")
}
```

**Key Methods:**
- `ensure_regulation_loaded()` - **Idempotent** - Loads regulation if not already in DB
- `get_regulation_metadata()` - Returns regulation info
- `get_regulation_chunks(limit, offset)` - Returns regulation chunks

**Workflow:**
1. Check if regulation exists by `rule_id`
2. If exists with chunks → return metadata (status: "already_loaded")
3. If not exists → process PDF:
   - Extract text
   - Structure sections
   - Chunk sections
   - Generate embeddings (via `embeddings_service`)
   - Store in `regulation_chunks` table
4. Return metadata (status: "newly_loaded")

**Database Schema Used:**
- **policy_rules table:** Stores regulation metadata
  - `rule_id` (UUID), `rule_code` (RBI-PA-MD-2020), `spec` (JSONB), `category` (text[])
  
- **regulation_chunks table:** Stores regulation chunks with embeddings
  - `chunk_id`, `rule_id`, `chunk_text`, `chunk_hash`, `chunk_index`
  - `embedding` (vector), `rule_section`, `metadata` (JSONB)

---

### 3. Updated API: Regulations Router
**File:** `backend/app/api/regulations.py`

**New Endpoints:**

#### POST `/regulations/preload-demo`
- **Purpose:** Auto-load the Payment Aggregator regulation
- **Returns:** 
  ```json
  {
    "message": "Demo regulation ready",
    "data": {
      "rule_id": "RBI-PA-MD-2020",
      "title": "Master Direction...",
      "chunk_count": 45,
      "status": "already_loaded" | "newly_loaded"
    }
  }
  ```
- **Error Handling:**
  - 404 if PDF file not found at specified path
  - 500 for processing errors

#### GET `/regulations/preload-demo/metadata`
- **Purpose:** Get metadata for preloaded regulation
- **Returns:** Regulation details (title, category, chunk_count, etc.)

#### GET `/regulations/preload-demo/chunks?limit=10&offset=0`
- **Purpose:** Retrieve regulation chunks (for debugging/display)
- **Returns:** Array of chunks with text, section, metadata

**Disabled Endpoints:**

#### POST `/regulations/upload` ❌ COMMENTED OUT
- Endpoint is commented out with error message:
  ```python
  raise HTTPException(503, "Upload feature disabled for demo. Using preloaded regulation.")
  ```
- Can be re-enabled by uncommenting the code

---

## Frontend Changes

### 1. Updated Page: Upload Regulation
**File:** `frontend/app/regulations/upload/page.tsx`

**Changes:**
- Added **demo mode banner** explaining upload is disabled
- Form is now **disabled** (`opacity-50`, `pointer-events-none`)
- All inputs have `disabled` attribute
- Submit button shows "Upload Disabled for Demo"

**Banner Content:**
```
Demo Mode Active
For this hackathon demo, regulation upload is disabled. 
The system uses a preloaded RBI Payment Aggregator regulation.
Simply select the "Payment Aggregator" category when scanning 
repositories, and the regulation will be automatically loaded.
```

---

### 2. Updated: API Client
**File:** `frontend/lib/api-client.ts`

**New Methods:**

```typescript
async preloadDemoRegulation() {
  // POST /regulations/preload-demo
  // Auto-loads the regulation if not already loaded
}

async getDemoRegulationMetadata() {
  // GET /regulations/preload-demo/metadata
  // Returns regulation metadata
}
```

**Modified Methods:**
- `uploadRegulation()` - Now throws error if used (disabled for demo)

---

## How It Works

### Demo Mode Workflow

1. **User selects "Payment Aggregator" category** in the compliance scan UI

2. **Frontend calls** `apiClient.preloadDemoRegulation()`

3. **Backend checks** if regulation exists:
   - Query `regulation_chunks` table for `rule_id = 'RBI-PA-MD-2020'`

4. **If not loaded:**
   - Extract text from PDF: `C:\Users\sandi\Downloads\Master Direction on Regulation of Payment Aggregator (PA).pdf`
   - Structure into sections using regex
   - Chunk sections (max 1000 chars per chunk)
   - Generate embeddings for each chunk
   - Store in database

5. **If already loaded:**
   - Skip processing
   - Return metadata immediately

6. **Frontend receives** metadata with chunk count and status

7. **User proceeds** to run compliance scan against preloaded regulation

---

## Database Tables

### policy_rules
Stores regulation metadata:
```sql
CREATE TABLE policy_rules (
    rule_id UUID PRIMARY KEY,
    rule_code VARCHAR(100) NOT NULL,     -- 'RBI-PA-MD-2020'
    spec JSONB NOT NULL,                  -- {title, regulatory_body, file_path}
    category TEXT[],                      -- ['payment_aggregator']
    severity VARCHAR(20),                 -- 'high'
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    UNIQUE (rule_code, version)
);
```

### regulation_chunks
Stores regulation chunks with embeddings:
```sql
CREATE TABLE regulation_chunks (
    chunk_id UUID PRIMARY KEY,
    rule_id VARCHAR(255) NOT NULL,       -- 'RBI-PA-MD-2020'
    chunk_text TEXT NOT NULL,
    chunk_hash VARCHAR(64) NOT NULL,     -- For deduplication
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(1536),              -- OpenAI embedding
    rule_section VARCHAR(500),           -- '1.2 Introduction'
    metadata JSONB,                      -- {section_number, section_title, chunk_index}
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## File Locations

### Backend Files Created/Modified
1. ✅ `backend/app/services/pdf_processor.py` (NEW)
2. ✅ `backend/app/services/preloaded_regulations.py` (NEW)
3. ✅ `backend/app/api/regulations.py` (MODIFIED)

### Frontend Files Modified
1. ✅ `frontend/app/regulations/upload/page.tsx` (MODIFIED)
2. ✅ `frontend/lib/api-client.ts` (MODIFIED)

### Dependencies
- **pypdf** (version 4.0.1) - Already in `requirements.txt`
- No new frontend dependencies needed

---

## Testing Steps

### 1. Start Backend
```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Test Preload Endpoint
```bash
curl -X POST http://localhost:8000/regulations/preload-demo
```

**Expected Response (first time):**
```json
{
  "message": "Demo regulation ready",
  "data": {
    "rule_id": "RBI-PA-MD-2020",
    "title": "Master Direction on Regulation of Payment Aggregator",
    "chunk_count": 45,
    "status": "newly_loaded"
  }
}
```

**Expected Response (subsequent calls):**
```json
{
  "status": "already_loaded"
}
```

### 3. Verify Database
```sql
-- Check policy_rules
SELECT rule_code, spec, category FROM policy_rules 
WHERE rule_code = 'RBI-PA-MD-2020';

-- Check regulation chunks
SELECT COUNT(*), rule_id FROM regulation_chunks 
WHERE rule_id = 'RBI-PA-MD-2020' 
GROUP BY rule_id;
```

### 4. Test Frontend
1. Navigate to `/regulations/upload`
2. Verify demo mode banner is visible
3. Verify form is disabled
4. Check API client methods are available

---

## Configuration

### PDF File Location
**Path:** `C:\Users\sandi\Downloads\Master Direction on Regulation of Payment Aggregator (PA).pdf`

**To change:**
1. Update `DEMO_REGULATION["file_path"]` in `backend/app/services/preloaded_regulations.py`

### Regulation Metadata
**To change regulation details:**
1. Edit `DEMO_REGULATION` dictionary in `backend/app/services/preloaded_regulations.py`

---

## Re-enabling Upload Feature

To restore upload functionality:

### Backend
1. Uncomment the `/regulations/upload` endpoint in `backend/app/api/regulations.py`
2. Remove the `raise HTTPException(503, ...)` line

### Frontend
1. Remove demo mode banner from `frontend/app/regulations/upload/page.tsx`
2. Remove `disabled` attributes from form inputs
3. Restore the upload handler logic
4. Update API client to allow uploads

---

## Error Handling

### PDF Not Found
If PDF file doesn't exist at specified path:
```
FileNotFoundError: Demo regulation PDF not found at: C:\Users\sandi\Downloads\...
Please ensure the file exists at the specified location.
```

**Fix:** Download the PDF or update the path in `DEMO_REGULATION`

### Database Connection Issues
If database is unreachable:
```
HTTPException 500: Failed to load demo regulation: connection error
```

**Fix:** Check database connection string in `.env`

### Embedding Service Issues
If embeddings fail to generate:
```
Warning: Failed to process chunk X: embedding generation failed
```

**Fix:** Check Azure OpenAI credentials in `.env`

---

## Next Steps

1. **Test end-to-end flow:**
   - Preload regulation
   - Index a repository
   - Run compliance scan against preloaded regulation

2. **Add compliance matching:**
   - Vector similarity search between code chunks and regulation chunks
   - Generate compliance reports

3. **Frontend integration:**
   - Call `preloadDemoRegulation()` when user selects "Payment Aggregator"
   - Display regulation metadata in UI
   - Show loading state during processing

---

## Notes

- **Idempotency:** The preload endpoint can be called multiple times safely
- **Performance:** Processing happens only once; subsequent calls return cached data
- **Scalability:** Can extend to support multiple regulations by updating `DEMO_REGULATION` to a list
- **Embeddings:** Uses Azure OpenAI `text-embedding-ada-002` (1536 dimensions)
- **Chunking:** Max 1000 characters per chunk, preserving paragraph boundaries

