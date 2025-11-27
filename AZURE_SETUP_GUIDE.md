# Azure OpenAI Embedding Deployment Setup

## Current Issue
Your `.env` file specifies `AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-3-small` but this deployment doesn't exist in your Azure OpenAI resource.

## Solution: Create the Embedding Deployment

### Step 1: Go to Azure OpenAI Studio
1. Open https://oai.azure.com/
2. Sign in with your Azure account
3. Select your resource: **mh25** (from your endpoint: https://mh25.openai.azure.com/)

### Step 2: Navigate to Deployments
1. Click on **"Deployments"** in the left sidebar
2. You should see your existing deployment: **gpt-4o**

### Step 3: Create Text Embedding Deployment
1. Click **"+ Create new deployment"**
2. Fill in the form:
   - **Model**: Select **text-embedding-ada-002** (most common and reliable)
     - OR select **text-embedding-3-small** if available in your region
   - **Deployment name**: `text-embedding-ada-002` (match the model name for simplicity)
   - **Model version**: Auto-update to default
   - **Deployment type**: Standard
   - **Tokens per Minute Rate Limit**: 120K (or higher based on your quota)

3. Click **"Create"**

### Step 4: Wait for Deployment (1-2 minutes)
The deployment status will show as "Creating" then change to "Succeeded"

### Step 5: Update Your .env File

Once the deployment is created, update your `.env` file:

```bash
# If you created text-embedding-ada-002 deployment:
AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-ada-002

# OR if you created text-embedding-3-small deployment:
AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-3-small
```

### Step 6: Restart the Worker
```bash
# Stop the worker (Ctrl+C in worker terminal)
cd /c/x/ibmw/backend
source ./venv/Scripts/activate
python -m app.workers.indexing_worker
```

## Alternative: Check Existing Deployments via Azure Portal

If you prefer the Azure Portal:
1. Go to https://portal.azure.com/
2. Search for "Azure OpenAI" in the search bar
3. Click on your resource (likely named **mh25** or similar)
4. In the left menu, click **"Model deployments"**
5. Click **"Manage Deployments"** - this will open Azure OpenAI Studio

## Common Deployment Names

- **text-embedding-ada-002** - Most widely used, 1536 dimensions
- **text-embedding-3-small** - Newer model, 1536 dimensions, better performance
- **text-embedding-3-large** - Highest quality, 3072 dimensions (requires more compute)

## Recommended Configuration

For your use case (code compliance), I recommend:
- **Model**: text-embedding-ada-002 (proven, reliable, cheaper)
- **Deployment Name**: text-embedding-ada-002
- **Rate Limit**: 120K tokens/min (sufficient for most workloads)

## Troubleshooting

### If deployment creation fails:
1. Check your Azure subscription has quota for embeddings
2. Verify your region (East US 2) supports the model
3. Try a different model version
4. Contact Azure support for quota increase

### After creating deployment:
Your `.env` should have:
```
AZURE_OPENAI_ENDPOINT=https://mh25.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-ada-002
EMBEDDINGS_PROVIDER=azure
```

## Next Steps After Setup
1. Update `.env` file with correct deployment name
2. Restart worker
3. Trigger a new indexing job from the frontend
4. Worker should successfully generate embeddings and index the repository
