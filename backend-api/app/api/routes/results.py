"""
Results Endpoint
"""
from fastapi import APIRouter, HTTPException
from app.models.response import ResultsResponse, Reports
from app.services.job_queue import job_queue
from datetime import datetime

router = APIRouter()


@router.get("/results/{job_id}", response_model=ResultsResponse)
async def get_results(job_id: str):
    """
    Get validation results
    """
    job_data = job_queue.get_result(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Build reports URLs
    reports = Reports(
        pdf_url=f"/api/v1/download/{job_id}/report.pdf",
        html_url=f"/api/v1/download/{job_id}/report.html",
        json_url=f"/api/v1/download/{job_id}/data.json"
    )
    
    return ResultsResponse(
        job_id=job_id,
        status=job_data["status"],
        validation_result=job_data.get("validation_result"),
        reports=reports,
        timestamp=job_data["created_at"],
        processing_time=job_data.get("processing_time")
    )
