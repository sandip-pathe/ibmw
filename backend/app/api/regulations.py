from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.core.security import verify_admin_api_key
from app.services.regulation_ingestion import regulation_service
from app.services.rss_scraper import rss_agent
from app.services.preloaded_regulations import preloaded_regulation_service
from app.models.schemas import SuccessResponse

router = APIRouter(prefix="/regulations", tags=["Regulations"])

# ==========================================
# ⚠️ DEMO MODE: PRELOADED REGULATION
# ==========================================
@router.post("/preload-demo")
async def preload_demo_regulation():
    """
    DEMO MODE: Auto-load the Payment Aggregator regulation.
    
    This endpoint is called automatically when the user selects
    the "Payment Aggregator" category. It ensures the regulation
    is loaded and returns metadata.
    
    Returns:
        - rule_id: Regulation identifier
        - title: Full regulation title
        - chunk_count: Number of chunks stored
        - status: "already_loaded" or "newly_loaded"
    """
    try:
        result = await preloaded_regulation_service.ensure_regulation_loaded()
        return SuccessResponse(
            message="Demo regulation ready",
            data=result
        )
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to load demo regulation: {e}")

@router.get("/preload-demo/metadata")
async def get_demo_regulation_metadata():
    """
    Get metadata for the preloaded demo regulation.
    """
    metadata = await preloaded_regulation_service.get_regulation_metadata()
    
    if not metadata:
        raise HTTPException(404, "Demo regulation not loaded yet")
    
    return SuccessResponse(
        message="Demo regulation metadata",
        data=metadata
    )

@router.get("/preload-demo/chunks")
async def get_demo_regulation_chunks(limit: int = 10, offset: int = 0):
    """
    Get chunks from the demo regulation.
    """
    chunks = await preloaded_regulation_service.get_regulation_chunks(
        limit=limit,
        offset=offset
    )
    
    return SuccessResponse(
        message=f"Retrieved {len(chunks)} chunks",
        data={"chunks": chunks}
    )

# ==========================================
# UPLOAD DISABLED FOR DEMO
# ==========================================
# @router.post("/upload", dependencies=[Depends(verify_admin_api_key)])
# async def upload_manual_regulation(
#     file: UploadFile = File(...),
#     regulator: str = Form(...),
#     doc_type: str = Form(...),
#     publish_date: str = Form(...),
#     title: str = Form(...)
# ):
#     """
#     Manual PDF Upload Endpoint.
#     
#     ⚠️ DISABLED FOR HACKATHON DEMO
#     This feature is disabled for the demo version.
#     Only the preloaded Payment Aggregator regulation is available.
#     """
#     raise HTTPException(
#         503,
#         "Upload feature disabled for demo. Using preloaded regulation."
#     )
    
#     content = await file.read()
    
#     metadata = {
#         "regulator": regulator,
#         "type": doc_type,
#         "date": publish_date,
#         "title": title,
#         "source_url": None,
#         "status": "active" # Manual uploads are trusted
#     }

#     try:
#         doc_id = await regulation_service.ingest_document(
#             content=content,
#             filename=file.filename or "uploaded_file.pdf",           metadata=metadata
#         )
#         return SuccessResponse(message="Uploaded successfully", data={"id": str(doc_id)})
#     except Exception as e:
#         raise HTTPException(500, f"Upload failed: {e}")

@router.post("/rss/trigger", dependencies=[Depends(verify_admin_api_key)])
async def trigger_rss():
    """Force run the scraper."""
    res = await rss_agent.run_scrape_cycle()
    return SuccessResponse(message="Scrape complete", data=res)