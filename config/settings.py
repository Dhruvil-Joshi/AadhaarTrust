import os
from pathlib import Path

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Model paths
MODEL_DIR = BASE_DIR / "models"
FORGERY_MODEL_PATH = MODEL_DIR / "paths" / "forgery" / "best_acc.pth"
SPLICING_REGION_DETECTION_PATH = MODEL_DIR / "paths" / "forgery" / "aadhaar_splicing_detection.pt"
QR_DETECTION_MODEL_PATH = MODEL_DIR / "paths" / "qr" / "best.pt"  # Fixed: actual file is best.pt
# Alternative paths (if models are in different locations)
AADHAAR_REGION_DETECTION_PATH = MODEL_DIR / "paths" / "aadhaar_region_detection" / "best.pt"
AADHAAR_MAIN_PIPELINE_PATH = MODEL_DIR / "paths" / "aadhaar_pipeline" / "best.pt"
# Data paths
# Data paths
DATA_DIR = BASE_DIR / "temp_data"
INPUT_DIR = BASE_DIR / "temp_input"
OUTPUT_DIR = BASE_DIR / "temp_output"
TEMP_PROCESSING_DIR = BASE_DIR / "temp_processing"
REPORTS_DIR = OUTPUT_DIR / "reports"
SPLICING_MAPS_DIR = OUTPUT_DIR / "splicing_maps"
NOISEPRINT_IMAGES_DIR = OUTPUT_DIR / "noiseprint_images"
REFINED_IMAGES_DIR = OUTPUT_DIR / "refined_images"
PROCESSED_IMAGES_DIR = OUTPUT_DIR / "processed_images"
MANUAL_REVIEW_DIR = BASE_DIR / "temp_manual_review"

# Log paths
LOG_DIR = BASE_DIR / "logs"
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"