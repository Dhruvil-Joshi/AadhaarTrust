"""
FastAPI Application Entry Point
AadhaarTrust Backend API
"""
import sys
from pathlib import Path

# Add project root to system path to ensure 'src' module can be found
# File is at: .../backend-api/app/main.py
# Root is at: .../ (3 levels up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import upload, status, results, download, manual_review, health

app = FastAPI(
    title="AadhaarTrust API",
    description="Aadhaar Card Authentication & Forgery Detection System",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(status.router, prefix="/api/v1", tags=["status"])
app.include_router(results.router, prefix="/api/v1", tags=["results"])
app.include_router(download.router, prefix="/api/v1", tags=["download"])
app.include_router(manual_review.router, prefix="/api/v1", tags=["manual-review"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AadhaarTrust API",
        "version": "1.0.0",
        "status": "running"
    }
