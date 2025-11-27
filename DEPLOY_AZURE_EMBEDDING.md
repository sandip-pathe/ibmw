# Deploy Azure OpenAI Embedding Model

## Prerequisites
- Azure subscription with Azure OpenAI access
- Existing Azure OpenAI resource: `mh25`
- Resource location: Your region (check portal)

## Method 1: Azure Portal (Recommended - No Installation Required)

### Steps:
1. Open https://portal.azure.com
2. Search for "Azure OpenAI" in the top search bar
3. Click on your resource: **mh25**
4. In the left menu, click **"Model deployments"** (or "Deployments")
5. Click **"+ Create new deployment"** button
6. Configure deployment:
   ```
   Select a model: text-embedding-ada-002
   Deployment name: text-embedding-ada-002
   Model version: 2 (or latest)
   Deployment type: Standard
   Tokens per minute rate limit: 120000 (120K)
   Content filter: Default
   ```
7. Click **"Create"**
8. Wait 1-2 minutes for deployment status to show "Succeeded"

### Verify Deployment:
- In "Model deployments" page, you should see:
  - ✅ `gpt-4o` (already deployed)
  - ✅ `text-embedding-ada-002` (newly deployed)

---

## Method 2: Azure CLI (If you prefer command line)

### Install Azure CLI:
**Windows:**
```powershell
# Download and run the MSI installer
winget install -e --id Microsoft.AzureCLI
```
OR download from: https://aka.ms/installazurecliwindows

### Deploy via CLI:
```bash
# 1. Login to Azure
az login

# 2. Find your resource group
az cognitiveservices account list --query "[?name=='mh25'].{Name:name, ResourceGroup:resourceGroup, Location:location}" -o table

# 3. Deploy the embedding model (replace <RESOURCE_GROUP> with actual value from step 2)
az cognitiveservices account deployment create \
  --name mh25 \
  --resource-group <RESOURCE_GROUP> \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI \
  --sku-name "Standard" \
  --sku-capacity 1

# 4. Verify deployment
az cognitiveservices account deployment list \
  --name mh25 \
  --resource-group <RESOURCE_GROUP> \
  -o table
```

---

## Method 3: Azure OpenAI Studio (Alternative Web UI)

1. Go to https://oai.azure.com/
2. Sign in with your Azure account
3. Select your subscription and resource (mh25)
4. Click **"Deployments"** in the left menu
5. Click **"+ Create new deployment"**
6. Select **"text-embedding-ada-002"** from the dropdown
7. Deployment name: `text-embedding-ada-002`
8. Click **"Create"**

---

## After Deployment: Verify Your Setup

### Update .env file (if needed):
Your current `.env` already has:
```env
AZURE_OPENAI_ENDPOINT=https://mh25.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-ada-002
```
✅ No changes needed!

### Restart Worker:
```bash
cd /c/x/ibmw/backend
source ./venv/Scripts/activate
python -m app.workers.indexing_worker
```

### Test Indexing:
1. Go to http://localhost:3000
2. Select a repository
3. Click "Index Repository"
4. Watch worker logs - should see:
   ```
   ✅ Generated embedding for text (1234 chars)
   ✅ Stored 54 chunks in vector database
   ✅ Indexing completed successfully
   ```

---

## Troubleshooting

### Issue: "Deployment not found"
- Verify deployment name is exactly: `text-embedding-ada-002`
- Check deployment status in Azure Portal (must be "Succeeded")
- Wait 2-3 minutes after creation before testing

### Issue: "Quota exceeded"
- Your subscription may have limited quota
- Request quota increase: Azure Portal → Azure OpenAI → Quotas
- Or reduce `Tokens per minute` to 50K

### Issue: "Model not available"
- `text-embedding-ada-002` might not be available in your region
- Alternative: Deploy `text-embedding-3-small` instead
- Update `.env`: `AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-3-small`

---

## Cost Estimation

**text-embedding-ada-002 pricing:**
- ~$0.0001 per 1K tokens
- Indexing 100 files (~500KB code) ≈ $0.05
- Very cheap compared to LLM calls

**Recommendation:** Start with 120K tokens/min, scale if needed.
