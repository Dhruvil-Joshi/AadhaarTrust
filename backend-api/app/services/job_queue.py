"""
In-memory Job Queue Management
"""
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
from app.models.response import StatusResponse, ValidationResult
from app.core.logging import logger


class JobQueue:
    """In-memory job storage and management"""
    
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self._cleanup_interval = timedelta(hours=1)
    
    def create_job(self, file_path: str) -> str:
        """Create a new job and return job_id"""
        job_id = str(uuid.uuid4())
        self.create_job_with_id(job_id, file_path)
        return job_id
    
    def create_job_with_id(self, job_id: str, file_path: str):
        """Create a job with a specific job_id"""
        self.jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "file_path": file_path,
            "created_at": datetime.now(),
            "current_stage": "upload",
            "progress_percentage": 0,
            "stage_details": None,
            "validation_result": None,
            "error": None,
            "processing_time": None
        }
        
        logger.info(f"Created job {job_id} for file {file_path}")
    
    def update_status(
        self,
        job_id: str,
        status: Optional[str] = None,
        current_stage: Optional[str] = None,
        progress_percentage: Optional[int] = None,
        stage_details: Optional[Dict] = None,
        estimated_time: Optional[int] = None
    ):
        """Update job status"""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found")
            return
        
        if status:
            self.jobs[job_id]["status"] = status
        if current_stage:
            self.jobs[job_id]["current_stage"] = current_stage
        if progress_percentage is not None:
            self.jobs[job_id]["progress_percentage"] = progress_percentage
        if stage_details:
            self.jobs[job_id]["stage_details"] = stage_details
        if estimated_time is not None:
            self.jobs[job_id]["estimated_time_remaining"] = estimated_time
    
    def set_result(self, job_id: str, result: ValidationResult, processing_time: float):
        """Set validation result for completed job"""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found")
            return
        
        self.jobs[job_id]["validation_result"] = result
        self.jobs[job_id]["status"] = "completed"
        self.jobs[job_id]["processing_time"] = processing_time
        self.jobs[job_id]["progress_percentage"] = 100
    
    def set_error(self, job_id: str, error: str):
        """Set error for failed job"""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found")
            return
        
        self.jobs[job_id]["status"] = "failed"
        self.jobs[job_id]["error"] = error
        logger.error(f"Job {job_id} failed: {error}")
    
    def get_status(self, job_id: str) -> Optional[StatusResponse]:
        """Get job status"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        
        return StatusResponse(
            job_id=job["job_id"],
            status=job["status"],
            current_stage=job.get("current_stage"),
            progress_percentage=job.get("progress_percentage", 0),
            stage_details=job.get("stage_details"),
            estimated_time_remaining=job.get("estimated_time_remaining")
        )
    
    def get_result(self, job_id: str) -> Optional[Dict]:
        """Get complete job data"""
        return self.jobs.get(job_id)
    
    def cleanup_old_jobs(self):
        """Remove jobs older than cleanup interval"""
        now = datetime.now()
        to_remove = []
        
        for job_id, job in self.jobs.items():
            if now - job["created_at"] > self._cleanup_interval:
                to_remove.append(job_id)
        
        for job_id in to_remove:
            del self.jobs[job_id]
            logger.info(f"Cleaned up old job {job_id}")


# Global job queue instance
job_queue = JobQueue()
