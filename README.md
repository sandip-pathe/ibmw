# Fintech Compliance Engine

Production-grade compliance automation platform for fintech companies. Analyzes code repositories against RBI regulations using AST-aware parsing, vector embeddings, and LLM reasoning.

## Architecture

**Tech Stack:**
- FastAPI (async Python 3.11+)
- Neon Postgres + pgvector
- Redis (caching + job queue)
- Azure OpenAI (embeddings + LLM)
- Azure Blob Storage
- Tree-sitter (AST parsing)
- GitHub App integration

**Pipeline:**
1. GitHub App → Webhook → Clone repo → Parse code
2. AST chunking → Embed → Store in pgvector
3. Regulation chunks (pre-loaded or PDF OCR)
4. Vector similarity search (rule ↔ code)
5. LLM reasoning → Compliance verdict

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- GitHub App (optional for full flow)

## Setup Options

### Option 1: Local Python Virtual Environment (Recommended for Development)

**Benefits:** Direct Python debugging, faster iteration, full IDE support

#### 1. Clone Repository
```bash
git clone <your-repo>
cd ibmw/backend
```

#### 2. Run Setup Script

**Linux/Mac:**
```bash
chmod +x scripts/setup-local.sh
./scripts/setup-local.sh
```

**Windows:**
```bash
scripts\setup-local.bat
```

This script will:
- Create Python virtual environment
- Install dependencies from `requirements.txt`
- Create `.env` from `.env.example`

#### 3. Configure Environment
```bash
# Edit .env with your credentials
nano .env  # or use your preferred editor
```

#### 4. Start Docker Services (Postgres & Redis only)
```bash
cd ..  # Back to ibmw root
docker-compose up -d postgres redis
```

#### 5. Run Migrations
```bash
cd backend
docker exec -i compliance-postgres psql -U postgres -d compliance < migrations/001_create_tables.sql
```

#### 6. Activate Virtual Environment & Start Services

**Terminal 1 - FastAPI:**
```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 - RQ Worker:**
```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
rq worker --url redis://localhost:6379/0
```

#### 7. Seed Demo Data (Optional)
```bash
python scripts/seed_demo_data.py
```

#### 8. Access API
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

### Option 2: Full Docker Setup

**Benefits:** Isolated environment, easy teardown, production-like setup

#### 1. Clone Repository
```bash
git clone <your-repo>
cd ibmw
```

#### 2. Configure Environment
```bash
cd backend
cp .env.example .env
# Edit .env with your credentials
```

#### 3. Start All Services
```bash
cd ..  # Back to ibmw root
docker-compose up -d
```

This starts:
- PostgreSQL (with pgvector)
- Redis
- FastAPI app
- RQ worker

#### 4. Run Migrations
```bash
docker exec -i compliance-postgres psql -U postgres -d compliance < backend/migrations/001_create_tables.sql
```

#### 5. Seed Demo Data (Optional)
```bash
docker exec compliance-api python scripts/seed_demo_data.py
```

#### 6. Access API
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### Stop Services
```bash
docker-compose down
# Or with volume cleanup:
docker-compose down -v
```

## Environment Variables

### Required (Core)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Neon/Postgres connection | `postgresql+asyncpg://user:pass@localhost:5432/compliance` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `ADMIN_API_KEY` | Admin endpoint auth | `your-secret-key-here` |

### Required (Azure OpenAI)

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | `abc123...` |
| `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` | Embedding deployment name | `text-embedding-3-small` |
| `AZURE_OPENAI_DEPLOYMENT_LLM` | LLM deployment name | `gpt-4o-mini` |

### Required (GitHub App)

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_APP_ID` | GitHub App ID | `123456` |
| `GITHUB_PRIVATE_KEY_PATH` | Path to private key | `./github-app-key.pem` |
| `GITHUB_WEBHOOK_SECRET` | Webhook secret | `your-webhook-secret` |

### Optional (Features)

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDINGS_PROVIDER` | `azure` | `azure` or `openai` |
| `LLM_PROVIDER` | `azure` | `azure` or `openai` |
| `OPENAI_API_KEY` | - | Fallback OpenAI key |
| `ENABLE_GITHUB_CHECKS` | `false` | Post compliance results as GitHub Checks |
| `ENABLE_DOC_INTELLIGENCE` | `false` | Enable Azure Document Intelligence for PDFs |
| `BLOB_ENABLED` | `true` | Use Azure Blob (false = local filesystem) |
| `BLOB_CONNECTION_STRING` | - | Azure Blob connection string |
| `BLOB_CONTAINER_NAME` | `compliance-data` | Blob container name |
| `LOG_LEVEL` | `INFO` | Logging level |

## GitHub App Setup

See `scripts/create-github-app.md` for detailed instructions.

**Required Permissions:**
- Repository contents: Read
- Repository metadata: Read
- Pull requests: Read (optional for PR analysis)
- Checks: Write (if `ENABLE_GITHUB_CHECKS=true`)

**Webhook Events:**
- `installation`
- `installation_repositories`
- `push`
- `pull_request` (optional)

**Webhook URL:** `https://your-domain.com/webhook`

## API Endpoints

### Public Endpoints
- `GET /health` - Health check
- `POST /webhook` - GitHub webhook receiver (validates signature)

### Admin Endpoints (require `X-API-Key: <ADMIN_API_KEY>`)
- `POST /installations/{installation_id}/sync` - Trigger manual repo sync
- `POST /analyze/rule` - Analyze code against a specific rule
- `POST /analyze/repo/{repo_id}/scan` - Full compliance scan
- `GET /admin/installations` - List all installations
- `GET /admin/repos` - List all repos

### Example cURL

Trigger manual sync
curl -X POST http://localhost:8000/installations/12345/sync
-H "X-API-Key: your-admin-key"

Analyze against rule
curl -X POST http://localhost:8000/analyze/rule
-H "X-API-Key: your-admin-key"
-H "Content-Type: application/json"
-d '{
"rule_text": "All API endpoints must implement rate limiting",
"repo_id": "repo-uuid",
"top_k": 10
}'

text

## Development

### Working with Virtual Environment

**Activate:**
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**Deactivate:**
```bash
deactivate
```

**Install new packages:**
```bash
pip install package-name
pip freeze > requirements.txt  # Update requirements
```

### Run Tests

pytest tests/ -v --cov=app --cov-report=html

text

### Code Quality

Format
black app/ tests/
isort app/ tests/

Lint
ruff check app/ tests/

Type check
mypy app/

text

## Deployment (Azure Container Apps)

### 1. Build & Push Image

docker build -t your-registry.azurecr.io/compliance-engine:latest .
docker push your-registry.azurecr.io/compliance-engine:latest

text

### 2. Create Container App

az containerapp create
--name compliance-engine
--resource-group your-rg
--image your-registry.azurecr.io/compliance-engine:latest
--environment your-env
--target-port 8000
--ingress external
--env-vars
DATABASE_URL=secretref:database-url
REDIS_URL=secretref:redis-url
AZURE_OPENAI_KEY=secretref:azure-openai-key
# ... add all required env vars

text

### 3. Deploy Worker (separate container)

az containerapp create
--name compliance-worker
--resource-group your-rg
--image your-registry.azurecr.io/compliance-engine:latest
--environment your-env
--command "python" "-m" "app.workers.indexing_worker"
--min-replicas 1
--max-replicas 5

text

## Security Checklist

- [ ] GitHub webhook signature validation enabled
- [ ] Admin API key stored in Azure Key Vault (not env vars in production)
- [ ] GitHub App private key rotated regularly
- [ ] Database uses SSL/TLS connections
- [ ] Rate limiting enabled on public endpoints
- [ ] CORS configured for allowed origins only
- [ ] Idempotency keys enforced for webhook events
- [ ] Secrets never logged or exposed in error messages
- [ ] Container runs as non-root user
- [ ] Network egress restricted to necessary endpoints

## Monitoring & Observability

- Structured logging via Loguru
- Health check endpoint: `/health`
- Metrics: (optional) Prometheus endpoint at `/metrics`
- Error tracking: integrate Sentry (set `SENTRY_DSN`)

## Architecture Decisions

### Why Tree-sitter?
Universal AST parser supporting 50+ languages. AST-aware chunking > naive text splitting for code analysis.

### Why pgvector?
Native Postgres extension. Simpler ops than Pinecone/Weaviate. HNSW index = fast similarity search at scale.

### Why RQ over Celery?
Lighter, simpler, perfect for job queue patterns. Celery is overkill for this use case.

### Why Azure OpenAI?
Enterprise compliance + your existing Azure credits. Pluggable abstraction allows OpenAI fallback.

## Troubleshooting

### Issue: `pgvector` extension not found
-- Connect to DB and run:
CREATE EXTENSION IF NOT EXISTS vector;

text

### Issue: Redis connection refused
Check Redis is running
docker ps | grep redis

Check connection
redis-cli ping

text

### Issue: GitHub webhook signature verification fails
- Verify `GITHUB_WEBHOOK_SECRET` matches GitHub App settings
- Check webhook payload is raw bytes (not parsed JSON)

### Issue: Embeddings provider errors
- Verify Azure deployment names match exactly
- Check API key has correct permissions
- Test with `curl` to Azure endpoint directly

## License

MIT

## Support

- Issues: GitHub Issues
- Docs: `/docs` endpoint
- Demo video: [link]