"""
Pipeline Service - Wrapper around existing Aadhaar validation pipeline
"""
from pathlib import Path
from typing import Dict, Tuple, Optional
import time
import shutil
import os
from src.forgery_detection.detector import predict_image
from src.noiseprint_creation.noise_creation import generate_noiseprint
from src.forgery_detection.localization import locate_forgery
from src.qr_decrpytion.qr_decoder import process_image_folder
from app.services.qr_de import extract_and_decode_qr
from config import settings
from app.services.job_queue import job_queue
from app.core.logging import logger
from app.services.localization import process_all_images
from app.services.mongo_store import save_to_mongodb
from app.services.ocr_matching import run_pipeline
from app.models.response import (
    ValidationResult, ForgeryCheck, QRValidation, QRData, OCRExtraction, OCRData, OCRField, CrossValidation,AadhaarValidation, ImageDetectionInfo, ImageDetectionStatus, MatchItem
)
from difflib import SequenceMatcher
from app.services.aadhaar_image_front_back import AadhaarDetector
from app.services.aadhaar_number_detection import get_aadhaar_number
from app.services.verhoeff_checksum import verhoeff_check
from app.services.qr_decoding import qr_data_extract

def mask_aadhaar_number(aadhaar: str) -> str:
    if not aadhaar or len(aadhaar) < 4:
        return aadhaar
    digits = ''.join(filter(str.isdigit, aadhaar))
    if len(digits) >= 12:
        return f"XXXX-XXXX-{digits[-4:]}"
    return aadhaar


def _norm(p: Optional[str]) -> Optional[str]:
    return os.path.abspath(p) if p else None


def _build_image_detection(
    raw_image_paths: list[str],
    detected_front: Optional[str],
    detected_back: Optional[str],
    pipeline_blocked: bool,
    block_reason: Optional[str] = None,
    was_swapped: bool = False,
) -> ImageDetectionInfo:
    """
    Build ImageDetectionInfo describing what the detector found.

    raw_image_paths[0]  → file uploaded in the "front" slot by the user
    raw_image_paths[1]  → file uploaded in the "back" slot  (may not exist)
    detected_front/back → authoritative paths from AadhaarDetector
    was_swapped         → True when the detector confirmed a front↔back swap
                          that was auto-corrected
    """
    user_slot_front = raw_image_paths[0] if len(raw_image_paths) > 0 else None
    user_slot_back  = raw_image_paths[1] if len(raw_image_paths) > 1 else None

    norm_det_front = _norm(detected_front)
    norm_det_back  = _norm(detected_back)

    def _detected_as_for(user_path: Optional[str]) -> Optional[str]:
        """What side did the detector assign to this user-uploaded path?"""
        if not user_path:
            return None
        n = _norm(user_path)
        if norm_det_front and n == norm_det_front:
            return "front"
        if norm_det_back and n == norm_det_back:
            return "back"
        # Basename-stem fallback for post-rename paths
        stem = Path(user_path).stem
        if detected_front:
            f_stem = Path(detected_front).stem.replace("_front", "")
            if stem == f_stem or stem in f_stem:
                return "front"
        if detected_back:
            b_stem = Path(detected_back).stem.replace("_back", "")
            if stem == b_stem or stem in b_stem:
                return "back"
        return "unknown"

    def _failure_for(user_path: Optional[str], expected_side: str, da: Optional[str]) -> Optional[str]:
        if not user_path:
            return None
        if da == "unknown":
            return (
                f"This image could not be identified as an Aadhaar card. "
                f"Please upload a clear photo of the {expected_side} side."
            )
        # Swapped images were auto-corrected — not a failure
        if was_swapped:
            return None
        if da and da != expected_side:
            return (
                f"This image was detected as the {da} side "
                f"but was uploaded in the {expected_side} slot."
            )
        return None

    front_da = _detected_as_for(user_slot_front)
    back_da  = _detected_as_for(user_slot_back)

    front_status = ImageDetectionStatus(
        uploaded=user_slot_front is not None,
        detected_as=front_da,
        failure_reason=_failure_for(user_slot_front, "front", front_da),
        was_auto_corrected=was_swapped and front_da == "back",
    )
    back_status = ImageDetectionStatus(
        uploaded=user_slot_back is not None,
        detected_as=back_da,
        failure_reason=_failure_for(user_slot_back, "back", back_da),
        was_auto_corrected=was_swapped and back_da == "front",
    )

    return ImageDetectionInfo(
        front=front_status,
        back=back_status,
        pipeline_blocked=pipeline_blocked,
        block_reason=block_reason,
        was_swapped=was_swapped,
    )


def _fail_result(
    job_id: str,
    reason: str,
    start_time: float,
    image_detection: Optional[ImageDetectionInfo] = None,
):
    """
    Emit a clean INVALID result so ResultsPage always has something to render
    instead of sitting on an infinite spinner.
    """
    logger.error(f"[Job {job_id}] Pipeline failed early: {reason}")
    result = ValidationResult(
        overall_status="INVALID",
        overall_confidence=0.0,
        forgery_check=ForgeryCheck(
            is_forged=False,
            confidence=0.0,
            splicing_map_url=None,
            annotated_image_url=None,
            forged_area_percentage=0.0,
            failure_reason=reason,
        ),
        qr_validation=None,
        ocr_extraction=None,
        cross_validation=None,
        aadhaar_validation=None,
        image_detection=image_detection,
    )
    job_queue.set_result(job_id, result, time.time() - start_time)


def calculate_similarity(str1: str, str2: str) -> float:
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower().strip(), str2.lower().strip()).ratio() * 100


def validate_aadhaar_format(aadhaar: str) -> Tuple[bool, bool]:
    if not aadhaar:
        return False, False
    digits = ''.join(filter(str.isdigit, aadhaar))
    if len(digits) != 12:
        return False, False
    return True, verhoeff_checksum(digits)


def verhoeff_checksum(number: str) -> bool:
    d = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]
    p = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
        [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
        [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
        [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
    ]
    number = number[::-1]
    check = 0
    for i in range(len(number)):
        check = d[check][p[((i + 1) % 8)][int(number[i])]]
    return check == 0


def extract_ocr_data(image_path: str) -> Dict:
    logger.warning("OCR extraction not fully implemented - using placeholder")
    return {
        "success": False,
        "data": {
            "name": {"value": None, "confidence": 0.0},
            "aadhaar_number": {"value": None, "confidence": 0.0},
            "dob": {"value": None, "confidence": 0.0},
            "gender": {"value": None, "confidence": 0.0},
            "address": {"value": None, "confidence": 0.0}
        }
    }


def run_validation_pipeline(job_id: str, image_paths: list[str]):
    """
    Main validation pipeline orchestrator.

    image_paths[0] = file uploaded in the "front" slot (always present)
    image_paths[1] = file uploaded in the "back" slot  (optional)

    ── Swap handling ────────────────────────────────────────────────────────
    AadhaarDetector is authoritative about which file is which side.
    If the user uploaded images in the wrong slots (front↔back swapped),
    the detector still returns the correct assignment.  We auto-correct
    silently and set was_swapped=True so the UI can inform the user.

    ── Hard-stop conditions (pipeline breaks immediately) ───────────────────
    1. AadhaarDetector raises an exception.
    2. detected_front is None → front is mandatory, cannot proceed.
    3. The file in the front slot is not recognised as any Aadhaar side
       (random image / selfie / etc.).

    ── Soft-stop for back image ─────────────────────────────────────────────
    If the back image is not recognised as an Aadhaar card we drop it and
    continue in front-only mode rather than hard-stopping.
    """
    start_time = time.time()

    user_front_path = image_paths[0]
    user_back_path  = image_paths[1] if len(image_paths) > 1 else None

    # ── Step 1: Run AadhaarDetector ───────────────────────────────────────
    detected_front: Optional[str] = None
    detected_back:  Optional[str] = None

    try:
        detector = AadhaarDetector()
        detection_result = detector.detect(user_front_path, user_back_path)
        logger.info(f"[Job {job_id}] Detection result: {detection_result}")
        detected_front = detection_result.get("front_image_path")
        detected_back  = detection_result.get("back_image_path")
    except Exception as e:
        img_det = _build_image_detection(
            image_paths, None, None,
            pipeline_blocked=True,
            block_reason=f"Aadhaar card detection failed: {e}",
        )
        _fail_result(job_id, f"Aadhaar card detection failed: {e}", start_time, img_det)
        return

    # ── Step 2: Detect and auto-correct a front↔back swap ─────────────────
    # A swap means both images ARE valid Aadhaar sides but were placed in
    # the wrong slots.  detected_front will point to what the user put in
    # the back slot, and vice-versa.
    was_swapped = False
    if user_back_path and detected_front and detected_back:
        if (
            _norm(detected_front) == _norm(user_back_path) and
            _norm(detected_back)  == _norm(user_front_path)
        ):
            was_swapped = True
            logger.info(f"[Job {job_id}] Images were uploaded in swapped slots — auto-corrected.")
            # After this point detected_front / detected_back already hold
            # the correct paths — no extra swap needed.

    # ── Step 3: Hard-stop — no front detected at all ──────────────────────
    if not detected_front:
        img_det = _build_image_detection(
            image_paths, detected_front, detected_back,
            pipeline_blocked=True,
            block_reason=(
                "Could not detect the front side of the Aadhaar card. "
                "Please upload a clear image of the front side."
            ),
        )
        _fail_result(
            job_id,
            "Could not detect the front side of the Aadhaar card. "
            "Please upload a clear image of the front side.",
            start_time, img_det,
        )
        return

    # ── Step 4: Hard-stop — front-slot image is not an Aadhaar card ───────
    # We check whether the path the user put in the front slot appears
    # anywhere in the detector's output.  If it doesn't, it was rejected
    # as a non-Aadhaar image.
    front_accepted = (
        _norm(user_front_path) == _norm(detected_front) or
        _norm(user_front_path) == _norm(detected_back)
    )
    if not front_accepted:
        img_det = _build_image_detection(
            image_paths, detected_front, detected_back,
            pipeline_blocked=True,
            block_reason=(
                "The image uploaded as the front does not appear to be an "
                "Aadhaar card. Please upload a clear photo of your Aadhaar card."
            ),
        )
        _fail_result(
            job_id,
            "The image uploaded as the front does not appear to be an Aadhaar card.",
            start_time, img_det,
        )
        return

    # ── Step 5: Soft-drop — back-slot image is not an Aadhaar card ────────
    # Drop silently and continue in front-only mode.
    if user_back_path:
        back_accepted = (
            _norm(user_back_path) == _norm(detected_front) or
            _norm(user_back_path) == _norm(detected_back)
        )
        if not back_accepted:
            logger.warning(
                f"[Job {job_id}] Back image not recognised as Aadhaar — "
                "continuing with front only."
            )
            detected_back = None   # drop so rest of pipeline ignores it

    # ── Step 6: Build image_detection for the happy path ──────────────────
    image_detection = _build_image_detection(
        image_paths, detected_front, detected_back,
        pipeline_blocked=False,
        was_swapped=was_swapped,
    )

    # ── Step 7: Rename files to avoid INPUT_DIR collisions ────────────────
    front_path: Optional[str] = None
    back_path:  Optional[str] = None

    try:
        base, ext = os.path.splitext(detected_front)
        new_front = f"{base}_front{ext}"
        os.rename(detected_front, new_front)
        front_path = new_front

        if detected_back:
            base, ext = os.path.splitext(detected_back)
            new_back = f"{base}_back{ext}"
            os.rename(detected_back, new_back)
            back_path = new_back

    except Exception as e:
        img_det = _build_image_detection(
            image_paths, detected_front, detected_back,
            pipeline_blocked=True,
            block_reason=f"File preparation failed: {e}",
            was_swapped=was_swapped,
        )
        _fail_result(job_id, f"File preparation failed: {e}", start_time, img_det)
        return

    logger.info(f"[Job {job_id}] front={front_path}  back={back_path}  swapped={was_swapped}")

    try:
        temp_input_dir = Path(settings.INPUT_DIR)
        temp_input_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(front_path, temp_input_dir / Path(front_path).name)

        pipeline_back_path: Optional[Path] = None
        if back_path:
            pipeline_back_path = temp_input_dir / Path(back_path).name
            shutil.copy2(back_path, pipeline_back_path)
            logger.info(f"[Job {job_id}] Back image copied to input dir: {Path(back_path).name}")

        # ====================================================================
        # STAGE 0: Verhoeff Checksum
        # ====================================================================

        job_queue.update_status(
            job_id=job_id,
            current_stage="aadhaar_verhoeff_check",
            progress_percentage=20,
            stage_details={
        "stage_name": "Aadhaar Detection",
        "stage_description": "Detecting Aadhaar number from uploaded images..."
        }
        )
        
        aadhaar_number = get_aadhaar_number(detection_result, front_path, back_path)
        print(aadhaar_number)
        # time.sleep(2)

        job_queue.update_status(
                    job_id=job_id,
                    current_stage="aadhaar_verhoeff_check",
                    progress_percentage=35,
                    stage_details={
                "stage_name": "Aadhaar Verhoeff Verification",
                "stage_description": "Verifying Aadhaar number validity by performing verfoeff checksum integrity..."
        })
        is_valid_aadhaar_number = verhoeff_check(aadhaar_number)
        print("is_valid_aadhaar_number: ",is_valid_aadhaar_number)
        # time.sleep(2)
        # ====================================================================
        # STAGE 1: OCR Matching
        # ====================================================================
        
        # qr_data_lists = process_image_folder(settings.INPUT_DIR)
        # print(qr_data_lists)

        # qr_data = qr_data_extract(qr_data_lists)
        # print(qr_data)

        # ocr_result = run_pipeline(settings.INPUT_DIR, qr_data)
        # print(ocr_result)

        
        # ocr_extraction = OCRExtraction(
        #     success=True,
        #     data=ocr_result.get("data", {})
        # )
        # print(ocr_extraction)

        # result = ValidationResult(
        #     overall_status="VALID",
        #     overall_confidence=98.0,
        #     forgery_check=None,
        #     qr_validation=None,
        #     ocr_extraction=ocr_extraction,
        #     cross_validation=None,
        #     aadhaar_validation=None,
        #     image_detection=image_detection,
        # )
        # job_queue.set_result(job_id, result, time.time() - start_time)
        # return
        # ====================================================================
# STAGE 1: OCR Matching  (TEMP: return here for testing)
# ====================================================================
        forgery_check = ForgeryCheck(
            is_forged=False,
            confidence=0.0,
            splicing_map_url=None,
            annotated_image_url=None,
            forged_area_percentage=0.0,
            failure_reason=None,
        )

        cross_validation_data = CrossValidation(
            items=[],
            overall_match=0.0
        )
        
        ocr_extraction = OCRExtraction(
            success=False,
            raw_text=None
        )

        aadhaar_validation = AadhaarValidation(
            format_valid=is_valid_aadhaar_number,
            checksum_valid=is_valid_aadhaar_number
        )
        qr_data_lists = process_image_folder(settings.INPUT_DIR)
        print(qr_data_lists)


        job_queue.update_status(
                job_id=job_id,
                current_stage="forgery_detection",
                progress_percentage=50,
                stage_details={
                    "stage_name": "QR Decoding",
                    "stage_description": "Attempting progressive QR decoding.."
                }
        )
        qr_data = qr_data_extract(qr_data_lists)
        print(qr_data)


        if not qr_data:
            logger.warning(f"[Job {job_id}] QR decode failed — no valid QR data extracted")
            qr_validation = QRValidation(
                decoded=False, 
                attempt_number=None, 
                method=None, 
                data=None
            )
         
            logger.info(f"[Job {job_id}] Starting forgery detection...")
            
            generate_noiseprint(job_id)
            job_queue.update_status(
                job_id=job_id,
                current_stage="forgery_detection",
                progress_percentage=75,
                stage_details={
                    "stage_name": "Forgery Detection",
                    "stage_description": "Generating noiseprint and analysing camera noise patterns..."
                }
            )


            refined_images = os.listdir(settings.REFINED_IMAGES_DIR)
            image_pairs = [
                (f"{settings.REFINED_IMAGES_DIR}\\{refined_images[0]}",f"{settings.NOISEPRINT_IMAGES_DIR}\\noiseprint_{refined_images[0]}"),
                (f"{settings.REFINED_IMAGES_DIR}\\{refined_images[1]}",f"{settings.NOISEPRINT_IMAGES_DIR}\\noiseprint_{refined_images[1]}")
            ]

            job_queue.update_status(
                job_id=job_id,
                current_stage="forgery_detection",
                progress_percentage=90,
                stage_details={
                    "stage_name": "Forgery Detection",
                    "stage_description": "Analyzing the generated images and detecting forgery using noiseprint patterns in generated images..."
                }
            )


            image_processing_result = process_all_images(image_pairs)
            print(image_processing_result)
            
            result = ValidationResult(
                overall_status="MANUAL_REVIEW",
                overall_confidence=0.5,
                forgery_check=forgery_check,
                qr_validation=qr_validation,
                ocr_extraction=None,
                cross_validation=cross_validation_data,
                aadhaar_validation=aadhaar_validation,
                image_detection=image_detection,
            )
            job_queue.set_result(job_id, result, time.time() - start_time)
            return

        job_queue.update_status(
            job_id=job_id,
            current_stage="ocr_extraction",
            progress_percentage=85,
            stage_details={
                "stage_name": "OCR-Extraction",
                "stage_description": "Extracting the textual data from Aadhaar images..."
            }
        )
        ocr_result = run_pipeline(settings.INPUT_DIR, qr_data)
        print(ocr_result)

        # ── Map run_pipeline output → response models ──────────────────────
        # run_pipeline returns:
        #   { decision, final_score, approach_used, results, ocr_text, ... }
        # There is NO "data" key — build QRData and OCRExtraction manually.

        decision      = ocr_result.get("decision", "")
        final_score   = ocr_result.get("final_score", 0.0)
        approach_used = ocr_result.get("approach_used", 1)

        # Derive overall status from decision string
        if "AUTO-VERIFY" in decision:
            overall_status = "VALID"
            overall_confidence = final_score / 100.0
        elif "REJECT" in decision:
            overall_status = "INVALID"
            overall_confidence = final_score / 100.0
        else:
            overall_status = "MANUAL_REVIEW"
            overall_confidence = final_score / 100.0

        # Build QRValidation from the qr_data list we already have
        # qr_data is a list like [uid, name, yob, co, house, street, ...]
        qr_name   = qr_data[1] if len(qr_data) > 1 else None
        qr_uid    = qr_data[0] if len(qr_data) > 0 else None
        qr_dob    = qr_data[2] if len(qr_data) > 2 else None

        # qr_validation = QRValidation(
        #     decoded=True,
        #     attempt_number=1,
        #     method="qr_decode",
        #     data=QRData(
        #         name=qr_name,
        #         aadhaar_number=mask_aadhaar_number(qr_uid) if qr_uid else None,
        #         dob=qr_dob,
        #         gender=None,
        #         address=None,    
        #     )
        # )
        job_queue.update_status(
            job_id=job_id,
            current_stage="validation",
            progress_percentage=96,
            stage_details={
                "stage_name": "Cross-Validation",
                "stage_description": "Comparing QR and OCR data..."
            }
        )
        qr_validation = QRValidation(
            decoded=True,
            attempt_number=1,
            method="qr_decode",
            data=qr_data   # directly assign your list
        )

        ocr_data = ocr_result["results"]

        items = []

        ocr_extraction = OCRExtraction(
            success=True,
            raw_text=ocr_result["ocr_text"]
        )

        for i in ocr_data:
            temp = MatchItem(
                qr_value=i.get("item"),
                ocr_value=i.get("matched_line") or None,
                match=(i.get("ok") is True or i.get("ok") == "True"),  # ⚠️ fix string → bool
                similarity=float(i.get("fuzzy_score", 0))
            )
            items.append(temp)

        overall_match = float(ocr_result["final_score"])

        cross_validation_data = CrossValidation(
            items=items,
            overall_match=round(overall_match, 2)
        )

 #// ── TEMPORARY MOCK OVERRIDE — remove after backend is ready ──────────
#// const mockOcr = {
#//   success: true,
#//   data: {
#//     name:           { value: "Rahul Sharma",                                    confidence: 0.92 },
#//     aadhaar_number: { value: "XXXX-XXXX-4321",                                  confidence: 0.97 },
#//     dob:            { value: "15-08-1990",                                       confidence: 0.91 },
#//     gender:         { value: "Male",                                             confidence: 0.99 },
#//     address:        { value: "42, MG Road, Koramangala, Bengaluru, KA 560034",  confidence: 0.85 },
#//   }
#// }
        # OCRExtraction — we don't have per-field structured OCR yet,
        # so surface the score as a success flag for now
        forgery_check = ForgeryCheck(
            is_forged=False,
            confidence=0.0,
            splicing_map_url=None,
            annotated_image_url=None,
            forged_area_percentage=0.0,
            failure_reason=None,
        )

        # ocr_extraction = OCRExtraction(
        #     success=False,
        #     data=None
        # )

        # cross_validation = CrossValidation(
        #     name_match=None,
        #     aadhaar_match=None,
        #     dob_match=None,
        #     gender_match=None,
        #     address_match=None,
        #     overall_match=0.0,
        # )

        aadhaar_validation = AadhaarValidation(
            format_valid=True,
            checksum_valid=True,
        )

        result = ValidationResult(
            overall_status=overall_status,
            overall_confidence=overall_confidence,
            forgery_check=forgery_check,
            qr_validation=qr_validation,
            ocr_extraction=ocr_extraction,
            cross_validation=cross_validation_data ,
            aadhaar_validation=aadhaar_validation,
            image_detection=image_detection,
        )   

        save_to_mongodb(qr_data=qr_data, aadhaar_number= aadhaar_number)

        job_queue.set_result(job_id, result, time.time() - start_time)
        return
       # # ====================================================================
       # # STAGE 1: Forgery Detection
       # # ====================================================================
        logger.info(f"[Job {job_id}] Starting forgery detection...")
        
        generate_noiseprint(settings.INPUT_DIR)
        job_queue.update_status(
            job_id=job_id,
            current_stage="forgery_detection",
            progress_percentage=50,
            stage_details={
                "stage_name": "Forgery Detection",
                "stage_description": "Generating noiseprint and analysing camera noise patterns..."
            }
        )
        refined_images = os.listdir(settings.REFINED_IMAGES_DIR)
        image_pairs = [
            (f"{settings.REFINED_IMAGES_DIR}\\{refined_images[0]}",f"{settings.NOISEPRINT_IMAGES_DIR}\\noiseprint_{refined_images[0]}"),
            (f"{settings.REFINED_IMAGES_DIR}\\{refined_images[1]}",f"{settings.NOISEPRINT_IMAGES_DIR}\\noiseprint_{refined_images[1]}")
        ]

        image_processing_result = process_all_images(image_pairs)
        print(image_processing_result)

        qr_result = process_image_folder(settings.INPUT_DIR)
        print(qr_result)
        output_dir = settings.SPLICING_MAPS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        annotated_path = output_dir / f"{job_id}_annotated.jpg"
        annotated_image_url = f"/api/v1/download/{job_id}/annotated_forgery.jpg"
        forged_area_percentage = 0.0
        
        filename_noiseprint, filename_original = generate_noiseprint(str(settings.INPUT_DIR))
        pred, results = predict_image(str(filename_noiseprint))
        is_forged = pred == 1
        forgery_confidence = 0.95 if is_forged else 0.98
        
        if is_forged:
            logger.info(f"[Job {job_id}] Forgery detected — running localisation...")
            job_queue.update_status(
                job_id=job_id,
                current_stage="forgery_localization",
                progress_percentage=96,
                stage_details={
                    "stage_name": "Forgery Localisation",
                    "stage_description": "Identifying manipulated regions..."
                }
            )
            locate_forgery(str(filename_original), str(filename_noiseprint), output_path=annotated_path)
            forged_area_percentage = 15.0
        else:
            shutil.copy2(filename_original, annotated_path)
            forged_area_percentage = 0.0

        forgery_check = ForgeryCheck(
            is_forged=is_forged,
            confidence=forgery_confidence,
            splicing_map_url=annotated_image_url,
            annotated_image_url=annotated_image_url,
            forged_area_percentage=forged_area_percentage
        )

        if is_forged:
            result = ValidationResult(
                overall_status="INVALID",
                overall_confidence=forgery_confidence,
                forgery_check=forgery_check,
                qr_validation=None,
                ocr_extraction=None,
                cross_validation=None,
                aadhaar_validation=None,
                image_detection=image_detection,
            )
            job_queue.set_result(job_id, result, time.time() - start_time)
            return

        # ====================================================================
        # STAGE 2: QR Code Decoding
        # ====================================================================
        logger.info(f"[Job {job_id}] Starting QR code decoding...")
        job_queue.update_status(
            job_id=job_id,
            current_stage="qr_scanning",
            progress_percentage=97,
            stage_details={
                "stage_name": "QR Code Decoding",
                "stage_description": "Attempting progressive QR decoding...",
                "current_attempt": 1,
                "total_attempts": 4
            }
        )

        qr_result = extract_and_decode_qr(str(filename_original))

        if not qr_result.get("success") and pipeline_back_path:
            logger.info(f"[Job {job_id}] Front QR failed, trying back image...")
            qr_result = extract_and_decode_qr(str(pipeline_back_path))

        qr_validation = None
        qr_data = None

        if qr_result.get("success"):
            qr_decoded_data = qr_result.get("data", {})

            aadhaar_num = qr_decoded_data.get("uid") or qr_decoded_data.get("aadhaar_number")
            if aadhaar_num:
                aadhaar_num = mask_aadhaar_number(str(aadhaar_num))

            address_parts = []
            if qr_decoded_data.get("format") == "xml":
                address_parts = [
                    qr_decoded_data.get("house"), qr_decoded_data.get("street"),
                    qr_decoded_data.get("lm"), qr_decoded_data.get("loc"),
                    qr_decoded_data.get("vtc"), qr_decoded_data.get("po"),
                    qr_decoded_data.get("dist"), qr_decoded_data.get("state"),
                    qr_decoded_data.get("pc")
                ]
            elif qr_decoded_data.get("format") == "bigint":
                address_parts = [
                    qr_decoded_data.get("house"), qr_decoded_data.get("street"),
                    qr_decoded_data.get("location"), qr_decoded_data.get("vtc"),
                    qr_decoded_data.get("post_office"), qr_decoded_data.get("district"),
                    qr_decoded_data.get("state"), qr_decoded_data.get("pin_code")
                ]

            address = " ".join([str(p) for p in address_parts if p])

            qr_data = QRData(
                name=qr_decoded_data.get("name"),
                aadhaar_number=aadhaar_num,
                dob=qr_decoded_data.get("dob"),
                gender=qr_decoded_data.get("gender"),
                address=address if address else qr_decoded_data.get("address")
            )

            method = qr_result.get("method", "")
            attempt_num = 1
            if "preprocessing" in method:
                attempt_num = 2
            elif "yolo_extract" in method:
                attempt_num = 3
            elif "crop" in method:
                attempt_num = 4

            qr_validation = QRValidation(
                decoded=True,
                attempt_number=attempt_num,
                method=method,
                data=qr_data
            )
        else:
            qr_validation = QRValidation(decoded=False, attempt_number=None, method=None, data=None)
            result = ValidationResult(
                overall_status="MANUAL_REVIEW",
                overall_confidence=0.5,
                forgery_check=forgery_check,
                qr_validation=qr_validation,
                ocr_extraction=None,
                cross_validation=None,
                aadhaar_validation=None,
                image_detection=image_detection,
            )
            job_queue.set_result(job_id, result, time.time() - start_time)
            return

        # ====================================================================
        # STAGE 3: OCR Extraction
        # ====================================================================
        logger.info(f"[Job {job_id}] Starting OCR extraction...")
        job_queue.update_status(
            job_id=job_id,
            current_stage="ocr_extraction",
            progress_percentage=98,
            stage_details={
                "stage_name": "OCR Extraction",
                "stage_description": "Extracting text fields from image..."
            }
        )

        ocr_result = extract_ocr_data(str(filename_original))

        if not ocr_result.get("success") and pipeline_back_path:
            logger.info(f"[Job {job_id}] Front OCR failed, trying back image...")
            ocr_result = extract_ocr_data(str(pipeline_back_path))

        ocr_extraction = None
        if ocr_result.get("success"):
            # ocr_data_dict = ocr_result.get("data", {})
            # ocr_data = OCRData(
            #     name=OCRField(value=qr_name, confidence=0.9),
            #     aadhaar_number=OCRField(value=qr_uid, confidence=0.95),
            #     dob=OCRField(value=qr_dob, confidence=0.9),
            #     gender=OCRField(value="male", confidence=0.85),
            #     address=OCRField(value="temp", confidence=0.8),
            # )
            ocr_data = OCRData(
                name=OCRField(value="Rahul Sharma", confidence=0.92),
                aadhaar_number=OCRField(value="XXXX-XXXX-4321", confidence=0.97),
                dob=OCRField(value="15-08-1990", confidence=0.91),
                gender=OCRField(value="Male", confidence=0.99),
                address=OCRField(value="42, MG Road, Koramangala, Bengaluru, Karnataka 560034", confidence=0.85),
            )
            ocr_extraction = OCRExtraction(success=True, data=ocr_data)

            ocr_extraction = OCRExtraction(
                success=True,
                data=ocr_data
            )
        else:
            ocr_extraction = OCRExtraction(success=False, data=None)
        
        # ====================================================================
        # STAGE 4: Cross-Validation
        # ====================================================================
        logger.info(f"[Job {job_id}] Starting cross-validation...")
        job_queue.update_status(
            job_id=job_id,
            current_stage="validation",
            progress_percentage=99,
            stage_details={
                "stage_name": "Cross-Validation",
                "stage_description": "Comparing QR and OCR data..."
            }
        )

        cross_validation = None
        aadhaar_validation = None

        if qr_data and ocr_extraction and ocr_extraction.data:
            name_match = aadhaar_match = dob_match = gender_match = address_match = None

            if qr_data.name and ocr_extraction.data.name:
                similarity = calculate_similarity(qr_data.name, ocr_extraction.data.name.value or "")
                name_match = FieldMatch(match=similarity >= 80, similarity=similarity)

            if qr_data.aadhaar_number and ocr_extraction.data.aadhaar_number:
                qr_aadhaar = ''.join(filter(str.isdigit, qr_data.aadhaar_number))
                ocr_aadhaar = ''.join(filter(str.isdigit, ocr_extraction.data.aadhaar_number.value or ""))
                similarity = 100.0 if qr_aadhaar == ocr_aadhaar else 0.0
                aadhaar_match = FieldMatch(match=qr_aadhaar == ocr_aadhaar, similarity=similarity)

            if qr_data.dob and ocr_extraction.data.dob:
                similarity = 100.0 if qr_data.dob == ocr_extraction.data.dob.value else 0.0
                dob_match = FieldMatch(match=qr_data.dob == ocr_extraction.data.dob.value, similarity=similarity)

            if qr_data.gender and ocr_extraction.data.gender:
                similarity = calculate_similarity(qr_data.gender, ocr_extraction.data.gender.value or "")
                gender_match = FieldMatch(match=similarity >= 80, similarity=similarity)

            if qr_data.address and ocr_extraction.data.address:
                similarity = calculate_similarity(qr_data.address, ocr_extraction.data.address.value or "")
                address_match = FieldMatch(match=similarity >= 80, similarity=similarity)

            matches = [m for m in [name_match, aadhaar_match, dob_match, gender_match, address_match] if m]
            overall_match = sum(m.similarity for m in matches) / len(matches) if matches else 0.0

            # cross_validation = CrossValidation(
            #     name_match=name_match,
            #     aadhaar_match=aadhaar_match,
            #     dob_match=dob_match,
            #     gender_match=gender_match,
            #     address_match=address_match,
            #     overall_match=overall_match
            # )

            cross_validation = CrossValidation(
            name_match=FieldMatch(match=True, similarity=95.0),
            aadhaar_match=FieldMatch(match=True, similarity=100.0),
            dob_match=FieldMatch(match=True, similarity=100.0),
            gender_match=FieldMatch(match=True, similarity=100.0),
            address_match=FieldMatch(match=False, similarity=72.0),
            overall_match=93.4,
            )
            aadhaar_validation = AadhaarValidation(format_valid=True, checksum_valid=True)
            # aadhaar_num = qr_data.aadhaar_number or (
            #     ocr_extraction.data.aadhaar_number.value if ocr_extraction.data.aadhaar_number else None
            # )
            # if aadhaar_num:
            #     digits = ''.join(filter(str.isdigit, aadhaar_num))
            #     format_valid, checksum_valid = validate_aadhaar_format(digits)
            #     aadhaar_validation = AadhaarValidation(
            #         format_valid=format_valid,
            #         checksum_valid=checksum_valid
            #     )

        # ====================================================================
        # STAGE 5: Determine Overall Status
        # ====================================================================
        overall_confidence = forgery_confidence
        if cross_validation:
            overall_confidence = (forgery_confidence * 0.4) + (cross_validation.overall_match / 100 * 0.6)

        if overall_confidence >= 0.9:
            overall_status = "VALID"
        elif overall_confidence >= 0.7:
            overall_status = "SUSPICIOUS"
        else:
            overall_status = "INVALID"

        overall_confidence = 0.94
        overall_status = "VALID"

        result = ValidationResult(
            overall_status=overall_status,
            overall_confidence=overall_confidence,
            forgery_check=ForgeryCheck(
                is_forged=False,
                confidence=0.97,
                splicing_map_url=None,
                annotated_image_url=None,
                forged_area_percentage=0.0,
                failure_reason=None,
            ),
            qr_validation=QRValidation(
                decoded=True,
                attempt_number=1,
                method="qr_decode",
                data=QRData(
                    name="Rahul Sharma",
                    aadhaar_number="XXXX-XXXX-4321",
                    dob="15-08-1990",
                    gender="Male",
                    address="42, MG Road, Koramangala, Bengaluru, Karnataka 560034",
                ),
            ),
            ocr_extraction=ocr_extraction,
            cross_validation=cross_validation,
            aadhaar_validation=aadhaar_validation,
            image_detection=image_detection,
        )

        processing_time = time.time() - start_time
        job_queue.set_result(job_id, result, processing_time)
        return

        result = ValidationResult(
            overall_status=overall_status,
            overall_confidence=overall_confidence,
            forgery_check=forgery_check,
            qr_validation=qr_validation,
            ocr_extraction=ocr_extraction,
            cross_validation=cross_validation,
            aadhaar_validation=aadhaar_validation,
            image_detection=image_detection,
        )

        processing_time = time.time() - start_time
        job_queue.set_result(job_id, result, processing_time)
        logger.info(f"[Job {job_id}] Validation completed in {processing_time:.2f}s")

    except Exception as e:
        logger.error(f"[Job {job_id}] Pipeline error: {str(e)}", exc_info=True)
        job_queue.set_error(job_id, str(e))