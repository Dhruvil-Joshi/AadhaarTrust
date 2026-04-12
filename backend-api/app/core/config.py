"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AadhaarTrust API"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 25 * 1024 * 1024  # 25MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
    
    # Temporary Storage
    TEMP_DIR: Path = Path("../temp_processing")
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Output Directories
    OUTPUT_DIR: Path = Path("../temp_output")
    REPORTS_DIR: Path = OUTPUT_DIR / "reports"
    SPLICING_MAPS_DIR: Path = OUTPUT_DIR / "splicing_maps"
    NOISEPRINT_IMAGES_DIR: Path = OUTPUT_DIR / "noiseprint_images"
    REFINED_IMAGES_DIR: Path = OUTPUT_DIR / "refined_images"
    PROCESSED_IMAGES_DIR: Path = OUTPUT_DIR / "processed_images"
    MANUAL_REVIEW_DIR: Path = Path("../temp_manual_review")
    
    # File Cleanup (in seconds)
    TEMP_FILE_TTL: int = 3600  # 1 hour
    
    # Job Settings
    JOB_TIMEOUT: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
