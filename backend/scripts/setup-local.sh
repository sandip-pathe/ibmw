#!/bin/bash
set -e

echo "🐍 Setting up Local Python Development Environment"
echo "=================================================="

# Check Python version
if ! command -v python3.11 &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11+ not found. Please install Python 3.11 or later."
    exit 1
fi

# Determine Python command
PYTHON_CMD=""
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+' | head -1)
    if [[ "$(printf '%s\n' "3.11" "$PYTHON_VERSION" | sort -V | head -n1)" = "3.11" ]]; then
        PYTHON_CMD="python3"
    else
        echo "❌ Python 3.11+ required, found version $PYTHON_VERSION"
        exit 1
    fi
fi

echo "✅ Found Python: $PYTHON_CMD ($($PYTHON_CMD --version))"

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your credentials before running the app"
fi

echo ""
echo "=================================================="
echo "✅ Local development environment ready!"
echo ""
echo "📍 Next steps:"
echo "   1. Activate the virtual environment:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Update your .env file with credentials"
echo ""
echo "   3. Start Docker services (Postgres & Redis):"
echo "      docker-compose up -d postgres redis"
echo ""
echo "   4. Run migrations:"
echo "      docker exec -i compliance-postgres psql -U postgres -d compliance < migrations/001_create_tables.sql"
echo ""
echo "   5. Seed demo data (optional):"
echo "      python scripts/seed_demo_data.py"
echo ""
echo "   6. Start the FastAPI server:"
echo "      uvicorn app.main:app --reload"
echo ""
echo "   7. Start the worker (in another terminal):"
echo "      source venv/bin/activate"
echo "      rq worker --url redis://localhost:6379/0"
echo ""
echo "🌐 Access the application:"
echo "   API:      http://localhost:8000"
echo "   Docs:     http://localhost:8000/docs"
echo "   Redoc:    http://localhost:8000/redoc"
echo ""
