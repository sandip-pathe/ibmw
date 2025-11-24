from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.core.security import verify_admin_api_key
from app.services.regulation_ingestion import regulation_service
from app.services.rss_scraper import rss_agent
from app.models.schemas import SuccessResponse

router = APIRouter(prefix="/regulations", tags=["Regulations"])

@router.post("/upload", dependencies=[Depends(verify_admin_api_key)])
async def upload_manual_regulation(
    file: UploadFile = File(...),
    regulator: str = Form(...),
    doc_type: str = Form(...),
    publish_date: str = Form(...),
    title: str = Form(...)
):
    """
    Manual PDF Upload Endpoint.
    """
    content = await file.read()
    
    metadata = {
        "regulator": regulator,
        "type": doc_type,
        "date": publish_date,
        "title": title,
        "source_url": None,
        "status": "active" # Manual uploads are trusted
    }

    try:
        doc_id = await regulation_service.ingest_document(
            content=content,
            filename=file.filename or "uploaded_file.pdf",           metadata=metadata
        )
        return SuccessResponse(message="Uploaded successfully", data={"id": str(doc_id)})
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {e}")

@router.post("/rss/trigger", dependencies=[Depends(verify_admin_api_key)])
async def trigger_rss():
    """Force run the scraper."""
    res = await rss_agent.run_scrape_cycle()
    return SuccessResponse(message="Scrape complete", data=res)