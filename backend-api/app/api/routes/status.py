"""
Status Endpoint
"""
from fastapi import APIRouter, HTTPException
from app.models.response import StatusResponse
from app.services.job_queue import job_queue

router = APIRouter()


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Get validation job status
    """
    status = job_queue.get_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return status
