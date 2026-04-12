"""
Manual Review Endpoint
"""
from fastapi import APIRouter, HTTPException
from app.models.response import ManualReviewResponse, ManualReviewItem
from app.models.request import ManualReviewDecision
from app.services.job_queue import job_queue
from typing import List

router = APIRouter()


@router.get("/manual-review", response_model=ManualReviewResponse)
async def get_manual_review_queue():
    """
    Get list of jobs pending manual review
    """
    # Get all jobs with MANUAL_REVIEW status
    pending_reviews: List[ManualReviewItem] = []
    
    for job_id, job_data in job_queue.jobs.items():
        if job_data.get("status") == "completed":
            result = job_data.get("validation_result")
            if result and result.overall_status == "MANUAL_REVIEW":
                pending_reviews.append(ManualReviewItem(
                    job_id=job_id,
                    upload_timestamp=job_data["created_at"],
                    reason="QR decode failed or validation ambiguous",
                    thumbnail_url=f"/api/v1/download/{job_id}/thumbnail.jpg"
                ))
    
    return ManualReviewResponse(
        pending_reviews=pending_reviews,
        total_count=len(pending_reviews)
    )


@router.post("/manual-review/{job_id}")
async def submit_manual_review(job_id: str, decision: ManualReviewDecision):
    """
    Submit manual review decision
    """
    job_data = job_queue.get_result(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update job with manual review decision
    # TODO: Store decision in database or file
    
    return {
        "job_id": job_id,
        "decision": decision.decision,
        "message": "Manual review decision recorded"
    }
