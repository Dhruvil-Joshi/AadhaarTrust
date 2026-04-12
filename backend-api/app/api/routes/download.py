"""
Download Endpoint
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.services.job_queue import job_queue
from app.core.config import settings
from app.services.file_manager import file_manager

router = APIRouter()


@router.get("/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    """
    Download generated reports and files
    """
    job_data = job_queue.get_result(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Map file types to paths
    file_path = None
    
    if file_type == "report.pdf":
        file_path = settings.REPORTS_DIR / f"{job_id}_report.pdf"
    elif file_type == "report.html":
        file_path = settings.REPORTS_DIR / f"{job_id}_report.html"
    elif file_type == "data.json":
        file_path = settings.REPORTS_DIR / f"{job_id}_data.json"
    elif file_type == "annotated_forgery.jpg":
        file_path = settings.SPLICING_MAPS_DIR / f"{job_id}_annotated.jpg"
    elif file_type == "splicing_map.png":
        # Find splicing map for this job
        splicing_maps = list(settings.SPLICING_MAPS_DIR.glob("*.png")) + \
                      list(settings.SPLICING_MAPS_DIR.glob("*.jpg"))
        if splicing_maps:
            file_path = splicing_maps[-1]  # Most recent
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )
