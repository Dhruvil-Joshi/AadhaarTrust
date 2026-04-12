"""
Response Models
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str


class StageDetails(BaseModel):
    stage_name: str
    stage_description: str
    current_attempt: Optional[int] = None
    total_attempts: Optional[int] = None


class StatusResponse(BaseModel):
    job_id: str
    status: str
    current_stage: Optional[str] = None
    progress_percentage: int
    stage_details: Optional[StageDetails] = None
    estimated_time_remaining: Optional[int] = None


class ForgeryCheck(BaseModel):
    is_forged: bool
    confidence: float
    splicing_map_url: Optional[str] = None
    annotated_image_url: Optional[str] = None
    forged_area_percentage: Optional[float] = None
    failure_reason: Optional[str] = None

# class QRField(BaseModel):
#     key: str
#     value: Optional[str] = None

class QRData(BaseModel):
    name: Optional[str] = None
    aadhaar_number: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None


# class QRValidation(BaseModel):
#     decoded: bool
#     attempt_number: Optional[int] = None
#     method: Optional[str] = None
#     data: Optional[QRData] = None
class QRValidation(BaseModel):
    decoded: bool
    attempt_number: Optional[int] = None
    method: Optional[str] = None
    data: Optional[List[str]] = None

class OCRField(BaseModel):
    value: Optional[str] = None
    confidence: float


class OCRData(BaseModel):
    name: Optional[OCRField] = None
    aadhaar_number: Optional[OCRField] = None
    dob: Optional[OCRField] = None
    gender: Optional[OCRField] = None
    address: Optional[OCRField] = None
    # fields: Dict[str, OCRField] = {}

# class OCRExtraction(BaseModel):
#     success: bool
#     data: Optional[OCRData] = None
class OCRExtraction(BaseModel):
    success: bool
    raw_text: Optional[str] = None

# class FieldMatch(BaseModel):
#     match: bool
#     similarity: float


# class CrossValidation(BaseModel):
#     name_match: Optional[FieldMatch] = None
#     aadhaar_match: Optional[FieldMatch] = None
#     dob_match: Optional[FieldMatch] = None
#     gender_match: Optional[FieldMatch] = None
#     address_match: Optional[FieldMatch] = None
#     overall_match: float

class MatchItem(BaseModel):
    qr_value: Optional[str] = None
    ocr_value: Optional[str] = None
    match: bool
    similarity: float

class CrossValidation(BaseModel):
    items: List[MatchItem]
    overall_match: float

class AadhaarValidation(BaseModel):
    format_valid: bool
    checksum_valid: bool


class ImageDetectionStatus(BaseModel):
    """Detection result for one uploaded image."""
    uploaded: bool
    # "front" | "back" | "unknown" | None
    # None means the image was not provided; "unknown" means it was provided
    # but the detector could not match it to any Aadhaar side.
    detected_as: Optional[str] = None
    detection_confidence: Optional[float] = None
    failure_reason: Optional[str] = None
    # True when this image was in the wrong slot but we auto-swapped it
    was_auto_corrected: bool = False


class ImageDetectionInfo(BaseModel):
    """Combined detection info for both uploaded images."""
    front: ImageDetectionStatus
    back: ImageDetectionStatus
    # True when the pipeline was stopped because of a detection problem
    pipeline_blocked: bool
    block_reason: Optional[str] = None
    # True when both images were valid Aadhaar sides but uploaded in swapped slots
    was_swapped: bool = False


class ValidationResult(BaseModel):
    overall_status: str  # "VALID" | "SUSPICIOUS" | "INVALID" | "MANUAL_REVIEW"
    overall_confidence: float
    forgery_check: Optional[ForgeryCheck] = None
    qr_validation: Optional[QRValidation] = None
    ocr_extraction: Optional[OCRExtraction] = None
    cross_validation: Optional[CrossValidation] = None
    aadhaar_validation: Optional[AadhaarValidation] = None
    image_detection: Optional[ImageDetectionInfo] = None


class Reports(BaseModel):
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None
    json_url: Optional[str] = None


class ResultsResponse(BaseModel):
    job_id: str
    status: str
    validation_result: Optional[ValidationResult] = None
    reports: Optional[Reports] = None
    timestamp: datetime
    processing_time: Optional[float] = None


class ManualReviewItem(BaseModel):
    job_id: str
    upload_timestamp: datetime
    reason: str
    thumbnail_url: Optional[str] = None


class ManualReviewResponse(BaseModel):
    pending_reviews: List[ManualReviewItem]
    total_count: int


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    disk_space_available: bool
    version: str