"""Quick test script to check if backend endpoints work"""
import asyncio
import httpx

async def test_endpoints():
    async with httpx.AsyncClient() as client:
        # Test health
        try:
            resp = await client.get("http://localhost:8000/health")
            print(f"✅ Health check: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        # Test root
        try:
            resp = await client.get("http://localhost:8000/")
            print(f"✅ Root endpoint: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")
        
        # Test job status
        try:
            resp = await client.get("http://localhost:8000/jobs/d12978c6-adb2-4037-80b0-d60ed03ec2d9/status")
            print(f"✅ Job status: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"❌ Job status failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
