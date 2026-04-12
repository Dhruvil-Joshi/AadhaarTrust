"""
Upload Endpoint
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Optional
from app.models.response import UploadResponse
from app.services.file_manager import file_manager
from app.services.job_queue import job_queue
from app.services.pipeline_service import run_validation_pipeline
from app.core.config import settings
from app.core.logging import logger
import uuid

router = APIRouter()


def validate_file(file: UploadFile, content: bytes) -> None:
    """Validate extension and size for any uploaded file"""
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024)}MB"
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    front_file: UploadFile = File(...),
    back_file: Optional[UploadFile] = File(None),
):
    """
    Upload Aadhaar image(s) for validation.
    front_file is required, back_file is optional.
    Pipeline receives [front_path] or [front_path, back_path].
    """
    job_id = str(uuid.uuid4())

    # --- Front image (required) ---
    front_content = await front_file.read()
    validate_file(front_file, front_content)
    front_path = file_manager.save_uploaded_file(front_content, front_file.filename, job_id)

    # --- Back image ---
    back_path = None
    if back_file and back_file.filename:
        back_content = await back_file.read()
        validate_file(back_file, back_content)
        back_path = file_manager.save_uploaded_file(
            back_content, f"back_{back_file.filename}", job_id
        )

    # [front_path] or [front_path, back_path]
    image_paths = [str(front_path)]
    if back_path:
        image_paths.append(str(back_path))

    # Create job and start pipeline
    job_queue.create_job_with_id(job_id, image_paths[0])
    background_tasks.add_task(run_validation_pipeline, job_id, image_paths)

    logger.info(f"[Job {job_id}] {len(image_paths)} file(s) uploaded, pipeline starting")

    return UploadResponse(
        job_id=job_id,
        status="processing",
        message="Image uploaded successfully. Validation in progress."
    )

# """
# Upload Endpoint
# """
# from fastapi import APIRouter, UploadFile, File, HTTPException
# from app.models.response import UploadResponse
# from app.services.file_manager import file_manager
# from app.services.job_queue import job_queue
# from app.services.pipeline_service import run_validation_pipeline
# from app.core.config import settings
# from app.core.logging import logger
# from fastapi import BackgroundTasks
# import uuid

# router = APIRouter()


# @router.post("/upload", response_model=UploadResponse)
# async def upload_file(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...)
# ):
#     """
#     Upload Aadhaar image for validation
#     """
#     # Validate file extension
#     file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
#     if file_ext not in settings.ALLOWED_EXTENSIONS:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
#         )
    
#     # Read file content
#     file_content = await file.read()
    
#     # Validate file size
#     if len(file_content) > settings.MAX_FILE_SIZE:
#         raise HTTPException(
#             status_code=400,
#             detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024)}MB"
#         )
    
#     # Create job ID first
#     job_id = str(uuid.uuid4())
    
#     # Save file
#     file_path = file_manager.save_uploaded_file(file_content, file.filename, job_id)
    
#     # Create job in queue with the same job_id
#     job_queue.create_job_with_id(job_id, str(file_path))
    
#     # Start background validation
#     background_tasks.add_task(run_validation_pipeline, job_id, str(file_path))
    
#     logger.info(f"File uploaded: {file.filename}, Job ID: {job_id}")
    
#     return UploadResponse(
#         job_id=job_id,
#         status="processing",
#         message="Image uploaded successfully. Validation in progress."
#     )
