"""
Temporary File Management
"""
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logging import logger


class FileManager:
    """Manage temporary files and cleanup"""
    
    def __init__(self):
        self.temp_dir = settings.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def save_uploaded_file(self, file_content: bytes, filename: str, job_id: str) -> Path:
        """Save uploaded file to temporary directory"""
        job_dir = self.temp_dir / job_id
        job_dir.mkdir(exist_ok=True)
        
        file_path = job_dir / filename
        file_path.write_bytes(file_content)
        
        logger.info(f"Saved uploaded file: {file_path}")
        return file_path
    
    def get_job_dir(self, job_id: str) -> Path:
        """Get job-specific directory"""
        return self.temp_dir / job_id
    
    def cleanup_job_files(self, job_id: str):
        """Remove all files for a specific job"""
        job_dir = self.temp_dir / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)
            logger.info(f"Cleaned up files for job {job_id}")
    
    def cleanup_old_files(self):
        """Remove files older than TTL"""
        now = datetime.now()
        for job_dir in self.temp_dir.iterdir():
            if not job_dir.is_dir():
                continue
            
            # Check if directory is older than TTL
            mtime = datetime.fromtimestamp(job_dir.stat().st_mtime)
            if now - mtime > timedelta(seconds=settings.TEMP_FILE_TTL):
                shutil.rmtree(job_dir)
                logger.info(f"Cleaned up old job directory: {job_dir}")


# Global file manager instance
file_manager = FileManager()
