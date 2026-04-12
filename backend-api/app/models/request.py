"""
Request Models
"""
from pydantic import BaseModel
from typing import Optional


class ManualReviewDecision(BaseModel):
    """Manual review decision request"""
    decision: str  # "APPROVED" | "REJECTED"
    reviewer_notes: Optional[str] = None
    reviewer_id: Optional[str] = None
