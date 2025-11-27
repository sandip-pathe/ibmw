from fastapi import APIRouter, Query, HTTPException
from app.workers.job_queue import job_queue
from app.models.schemas import JobStatusResponse

router = APIRouter(prefix="/jobs", tags=["Job Status"])

@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job status for a given job_id."""
    status = job_queue.get_job_status(job_id)
    if not status or status.get("status") == "unknown":
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=str(status.get("id") or job_id),
        job_type="indexing",  # Could be dynamic if tracked
        status=status.get("status") or "queued",
        repo_id=None,  # Could be filled if tracked
        result=status.get("result"),
        error=status.get("exc_info"),
        created_at=status.get("created_at") or JobStatusResponse.__fields__["created_at"].default,
        started_at=status.get("started_at"),
        completed_at=status.get("ended_at"),
    )
