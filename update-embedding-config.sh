#!/bin/bash
# Quick setup script to update embedding deployment name

echo "=================================="
echo "Azure OpenAI Embedding Setup"
echo "=================================="
echo ""
echo "Which embedding deployment did you create in Azure?"
echo "1) text-embedding-ada-002 (recommended)"
echo "2) text-embedding-3-small"
echo "3) text-embedding-3-large"
echo "4) Custom name"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
  1)
    DEPLOYMENT_NAME="text-embedding-ada-002"
    ;;
  2)
    DEPLOYMENT_NAME="text-embedding-3-small"
    ;;
  3)
    DEPLOYMENT_NAME="text-embedding-3-large"
    ;;
  4)
    read -p "Enter custom deployment name: " DEPLOYMENT_NAME
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

echo ""
echo "Updating .env file with deployment: $DEPLOYMENT_NAME"

# Update .env file
cd "$(dirname "$0")/backend"
sed -i "s/^AZURE_OPENAI_DEPLOYMENT_EMBEDDING=.*/AZURE_OPENAI_DEPLOYMENT_EMBEDDING=$DEPLOYMENT_NAME/" .env
sed -i "s/^AZURE_OPENAI_EMBEDDING_DEPLOYMENT=.*/AZURE_OPENAI_EMBEDDING_DEPLOYMENT=$DEPLOYMENT_NAME/" .env

echo "✅ Updated .env file"
echo ""
echo "Next steps:"
echo "1. Restart the worker:"
echo "   cd backend"
echo "   source ./venv/Scripts/activate"
echo "   python -m app.workers.indexing_worker"
echo ""
echo "2. Trigger a new indexing job from the frontend"
