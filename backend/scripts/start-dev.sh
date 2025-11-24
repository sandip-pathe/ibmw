#!/bin/bash
set -e

echo "🚀 Starting Fintech Compliance Engine (Development)"
echo "=================================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please update it with your credentials."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

echo ""
echo "📦 Starting Docker containers..."
docker-compose up -d postgres redis

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if postgres is ready
echo "🔍 Checking PostgreSQL..."
until docker exec compliance-postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Check if redis is ready
echo "🔍 Checking Redis..."
until docker exec compliance-redis redis-cli ping > /dev/null 2>&1; do
    echo "   Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

echo ""
echo "🗄️  Running database migrations..."
docker exec -i compliance-postgres psql -U postgres -d compliance < migrations/001_create_tables.sql
echo "✅ Migrations completed"

echo ""
echo "🌱 Seeding demo data (optional)..."
if [ "${ENABLE_DEMO_SEED:-true}" = "true" ]; then
    python scripts/seed_demo_data.py
    echo "✅ Demo data seeded"
else
    echo "⏭️  Skipping demo data (ENABLE_DEMO_SEED=false)"
fi

echo ""
echo "=================================================="
echo "✅ Development environment ready!"
echo ""
echo "📍 Endpoints:"
echo "   API:      http://localhost:8000"
echo "   Docs:     http://localhost:8000/docs"
echo "   Redoc:    http://localhost:8000/redoc"
echo "   Postgres: localhost:5432"
echo "   Redis:    localhost:6379"
echo ""
echo "🏃 Starting services..."
echo "   - FastAPI: docker-compose up api"
echo "   - Worker:  docker-compose up worker"
echo ""
echo "Or start all services:"
echo "   docker-compose up"
echo ""
