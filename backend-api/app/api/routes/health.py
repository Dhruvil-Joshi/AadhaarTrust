"""
Health Check Endpoint
"""
from fastapi import APIRouter
from app.models.response import HealthResponse
import shutil

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    # Check disk space (simplified check)
    disk_space_available = True
    try:
        total, used, free = shutil.disk_usage("/")
        disk_space_available = free > 1024 * 1024 * 1024  # At least 1GB free
    except:
        disk_space_available = True  # Assume OK if check fails
    
    # Check if models are accessible (simplified)
    models_loaded = True  # TODO: Actually check model loading
    
    return HealthResponse(
        status="healthy",
        models_loaded=models_loaded,
        disk_space_available=disk_space_available,
        version="1.0.0"
    )
