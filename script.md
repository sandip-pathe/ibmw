cd /c/x/ibmw && docker-compose up -d && cd backend && source ./venv/Scripts/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

uvicorn app.main:app --reload --host :: --port 8000