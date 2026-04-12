import gzip
import cv2
import zxingcpp
import numpy as np
import os
from io import BytesIO
from typing import Optional, Dict, Tuple
import xml.etree.ElementTree as ET
from ultralytics import YOLO
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

class QRConfig:
    """Configuration for QR code extraction and decoding"""
    # Get project root
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
    # Try to use settings from config, otherwise use relative paths
    try:
        from config import settings as app_settings
        QR_MODEL_PATH = getattr(app_settings, 'QR_DETECTION_MODEL_PATH', None) or (BASE_DIR / "models" / "paths" / "qr" / "best.pt")
    except Exception:
        # Fallback to relative path from project root
        QR_MODEL_PATH = BASE_DIR / "models" / "paths" / "qr" / "best.pt"
    
    # Validate model path exists
    if not QR_MODEL_PATH.exists():
        # Try alternatives
        alternatives = [
            BASE_DIR / "models" / "paths" / "qr" / "best.pt",
            BASE_DIR / "models" / "paths" / "qr" / "qr_detection_model.pth",
            BASE_DIR / "models" / "paths" / "qr" / "qr_detection_model.pt",
        ]
        for alt in alternatives:
            if alt.exists():
                QR_MODEL_PATH = alt
                break
        else:
            raise FileNotFoundError(
                f"QR model not found at: {QR_MODEL_PATH}\n"
                f"Tried alternatives: {alternatives}\n"
                f"Please ensure the QR model file exists in: {BASE_DIR / 'models' / 'paths' / 'qr'}"
            )
    
    # Output directory - ensure it exists
    OUTPUT_DIR = BASE_DIR / "extracted_qr_raw"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CONFIDENCE_THRESHOLD = 0.25
    QR_PADDING = 15
    
    # Field indices for Aadhaar QR (adjust based on your QR structure)
    FIELD_INDEX_VTC = 17  # Verification code index


# ============================================================================
# DECODING FUNCTIONS
# ============================================================================

def decode_qr_bigint(bigint_text: str) -> Dict:
    """
    Decode BigInteger QR code (compressed format)
    Returns parsed fields from decompressed data
    """
    try:
        print("📦 Decoding BigInteger QR format...")
        
        # Convert to integer and then bytes
        bigint_value = int(bigint_text)
        byte_array = bigint_value.to_bytes(
            (bigint_value.bit_length() + 7) // 8, 
            byteorder="big", 
            signed=False
        )
        
        # GZIP decompress
        with gzip.GzipFile(fileobj=BytesIO(byte_array)) as f:
            decompressed_bytes = f.read()
        
        # Parse fields (delimiter is 255)
        DELIM = 255
        fields = []
        start_index = 0
        
        while start_index < len(decompressed_bytes):
            try:
                delim_index = decompressed_bytes.index(DELIM, start_index)
            except ValueError:
                delim_index = len(decompressed_bytes)
            
            field_bytes = decompressed_bytes[start_index:delim_index]
            
            # First field is numeric indicator
            if len(fields) == 0:
                field_value = field_bytes[0] & 0b11
            else:
                try:
                    field_value = field_bytes.decode("ISO-8859-1")
                except:
                    field_value = str(field_bytes)
            
            fields.append(field_value)
            start_index = delim_index + 1
            
            # Stop at VTC field if configured
            if len(fields) > QRConfig.FIELD_INDEX_VTC:
                break
        
        # Map fields to Aadhaar structure (adjust indices as needed)
        data = {
            "format": "bigint",
            "email_mobile_indicator": fields[0] if len(fields) > 0 else None,
            "reference_id": fields[1] if len(fields) > 1 else None,
            "name": fields[2] if len(fields) > 2 else None,
            "dob": fields[3] if len(fields) > 3 else None,
            "gender": fields[4] if len(fields) > 4 else None,
            "address": " ".join(fields[5:11]) if len(fields) > 10 else None,
            "pin_code": fields[11] if len(fields) > 11 else None,
            "photo": fields[12] if len(fields) > 12 else None,
            "vtc": fields[QRConfig.FIELD_INDEX_VTC] if len(fields) > QRConfig.FIELD_INDEX_VTC else None,
            "raw_fields": fields
        }
        
        print(f"✓ Decoded {len(fields)} fields from BigInteger QR")
        return data
        
    except Exception as e:
        print(f"✗ Error decoding BigInteger: {e}")
        return {"format": "bigint", "error": str(e)}


def decode_qr_xml(xml_text: str) -> Dict:
    """
    Decode XML QR code format
    Returns parsed XML attributes
    """
    try:
        print("📄 Decoding XML QR format...")
        
        root = ET.fromstring(xml_text)
        
        # Extract all attributes
        data = {
            "format": "xml",
            **root.attrib
        }
        
        # Common Aadhaar XML fields
        common_fields = ['uid', 'name', 'dob', 'gender', 'co', 'house', 
                        'street', 'lm', 'loc', 'vtc', 'po', 'dist', 'state', 'pc']
        
        print(f"✓ Decoded XML with {len(data)} attributes")
        return data
        
    except Exception as e:
        print(f"✗ Error decoding XML: {e}")
        return {"format": "xml", "error": str(e)}


def decode_qr_text(qr_result) -> Tuple[Optional[Dict], str]:
    """
    Decode QR code based on its format
    Returns (decoded_data, format_type)
    """
    if not qr_result or not qr_result.text:
        return None, "none"
    
    text = qr_result.text.strip()
    
    # Check format
    if text.startswith('<') or '<?xml' in text:
        return decode_qr_xml(text), "xml"
    elif text.isdigit():
        return decode_qr_bigint(text), "bigint"
    else:
        return {"format": "unknown", "text": text}, "unknown"


# ============================================================================
# QR DETECTION AND EXTRACTION
# ============================================================================

def extract_qr_regions(image_path: str, model_path: str) -> list:
    """
    Extract QR code regions using YOLO detection
    Returns list of cropped QR images
    """
    print(f"\n🔍 Extracting QR regions using YOLO...")
    
    # Load model
    if not Path(model_path).exists():
        print(f"✗ Model not found: {model_path}")
        return []
    
    model = YOLO(model_path)
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"✗ Cannot read image: {image_path}")
        return []
    
    # Create output directory
    QRConfig.OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Run detection
    results = model(image_path, conf=QRConfig.CONFIDENCE_THRESHOLD, save=False, verbose=False)
    
    qr_crops = []
    qr_count = 0
    h, w = img.shape[:2]
    
    for result in results:
        if result.boxes is None:
            continue
        
        for box in result.boxes:
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id].lower()
            
            if "qr" in class_name:
                qr_count += 1
                
                # Get bbox with padding
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                pad = QRConfig.QR_PADDING
                
                x1 = max(0, x1 - pad)
                y1 = max(0, y1 - pad)
                x2 = min(w, x2 + pad)
                y2 = min(h, y2 + pad)
                
                qr_crop = img[y1:y2, x1:x2]
                
                # Save cropped QR
                img_name = Path(image_path).stem
                save_path = QRConfig.OUTPUT_DIR / f"qr_{qr_count}_{img_name}.png"
                cv2.imwrite(str(save_path), qr_crop)
                
                qr_crops.append((qr_crop, str(save_path)))
                print(f"✓ QR #{qr_count} extracted → {save_path}")
    
    if qr_count == 0:
        print(f"✗ No QR codes detected in image")
    else:
        print(f"✓ Total {qr_count} QR code(s) extracted")
    
    return qr_crops


# ============================================================================
# PREPROCESSING AND ENHANCEMENT
# ============================================================================

def apply_preprocessing_techniques(img: np.ndarray) -> list:
    """
    Apply various preprocessing techniques to improve QR readability
    Returns list of (processed_image, technique_name) tuples
    """
    variations = []
    
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # 1. Original grayscale
    variations.append((gray, "grayscale"))
    
    # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    variations.append((enhanced, "clahe"))
    
    # 3. Sharpening
    kernel_sharp = np.array([[-1, -1, -1], 
                             [-1,  9, -1], 
                             [-1, -1, -1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel_sharp)
    variations.append((sharpened, "sharpened"))
    
    # 4. Otsu's thresholding
    _, thresh_otsu = cv2.threshold(gray, 0, 255, 
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variations.append((thresh_otsu, "otsu_threshold"))
    
    # 5. Adaptive thresholding
    thresh_adaptive = cv2.adaptiveThreshold(gray, 255, 
                                           cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 11, 2)
    variations.append((thresh_adaptive, "adaptive_threshold"))
    
    # 6. Bilateral filter (noise reduction)
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    variations.append((denoised, "bilateral_filter"))
    
    # 7. Gaussian blur + threshold
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh_blur = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
    variations.append((thresh_blur, "gaussian_blur_threshold"))
    
    # 8. Morphological operations
    kernel_morph = np.ones((3, 3), np.uint8)
    morph_close = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel_morph)
    variations.append((morph_close, "morphological_close"))
    
    # 9. Unsharp masking
    gaussian = cv2.GaussianBlur(gray, (9, 9), 10.0)
    unsharp = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
    variations.append((unsharp, "unsharp_mask"))
    
    # 10. High contrast
    normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    variations.append((normalized, "normalized"))
    
    return variations


def try_decode_with_variations(img: np.ndarray) -> Tuple[Optional[Dict], str, str]:
    """
    Try decoding QR with multiple preprocessing variations
    Returns (decoded_data, format, technique_used)
    """
    print("🔄 Trying multiple preprocessing techniques...")
    
    variations = apply_preprocessing_techniques(img)
    
    for processed_img, technique in variations:
        try:
            result = zxingcpp.read_barcode(processed_img)
            
            if result and result.text:
                print(f"✓ QR decoded successfully using: {technique}")
                decoded_data, format_type = decode_qr_text(result)
                return decoded_data, format_type, technique
                
        except Exception as e:
            continue
    
    print("✗ All preprocessing techniques failed")
    return None, "none", "none"


# ============================================================================
# MAIN QR EXTRACTION PIPELINE
# ============================================================================

def extract_and_decode_qr(image_path: str, model_path: Optional[str] = None) -> Dict:
    """
    Complete QR extraction and decoding pipeline
    
    Pipeline:
    1. Try direct decoding on original image
    2. Try basic preprocessing
    3. Extract QR region using YOLO
    4. Try advanced preprocessing on extracted region
    
    Returns complete QR data or error information
    """
    print("\n" + "="*70)
    print("           🔍 QR CODE EXTRACTION & DECODING PIPELINE")
    print("="*70)
    
    if model_path is None:
        model_path = str(QRConfig.QR_MODEL_PATH)
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        return {"success": False, "error": "Cannot load image", "image_path": image_path}
    
    print(f"\n📸 Processing: {Path(image_path).name}")
    
    # ========================================================================
    # STEP 1: Try direct decoding
    # ========================================================================
    print("\n[STEP 1] Attempting direct QR decoding...")
    try:
        result = zxingcpp.read_barcode(img)
        if result and result.text:
            print("✓ QR decoded directly from original image")
            decoded_data, format_type = decode_qr_text(result)
            
            if decoded_data:
                return {
                    "success": True,
                    "data": decoded_data,
                    "format": format_type,
                    "method": "direct_decode",
                    "image_path": image_path
                }
    except Exception as e:
        print(f"✗ Direct decode failed: {e}")
    
    # ========================================================================
    # STEP 2: Try with basic preprocessing
    # ========================================================================
    print("\n[STEP 2] Trying basic preprocessing techniques...")
    decoded_data, format_type, technique = try_decode_with_variations(img)
    
    if decoded_data:
        return {
            "success": True,
            "data": decoded_data,
            "format": format_type,
            "method": f"preprocessing_{technique}",
            "image_path": image_path
        }
    
    # ========================================================================
    # STEP 3: Extract QR region using YOLO
    # ========================================================================
    print("\n[STEP 3] Extracting QR regions using YOLO detection...")
    qr_crops = extract_qr_regions(image_path, model_path)
    
    if not qr_crops:
        return {
            "success": False,
            "error": "No QR code detected by YOLO",
            "method": "yolo_extraction_failed",
            "image_path": image_path
        }
    
    # ========================================================================
    # STEP 4: Try decoding extracted QR regions
    # ========================================================================
    print("\n[STEP 4] Decoding extracted QR regions...")
    
    for idx, (qr_crop, crop_path) in enumerate(qr_crops, 1):
        print(f"\n   Processing QR crop #{idx}...")
        
        # Try direct decode on crop
        try:
            result = zxingcpp.read_barcode(qr_crop)
            if result and result.text:
                print(f"   ✓ QR #{idx} decoded directly")
                decoded_data, format_type = decode_qr_text(result)
                
                if decoded_data:
                    return {
                        "success": True,
                        "data": decoded_data,
                        "format": format_type,
                        "method": f"yolo_extract_direct_crop_{idx}",
                        "crop_path": crop_path,
                        "image_path": image_path
                    }
        except Exception as e:
            print(f"   ✗ Direct decode on crop #{idx} failed")
        
        # Try with preprocessing
        decoded_data, format_type, technique = try_decode_with_variations(qr_crop)
        
        if decoded_data:
            return {
                "success": True,
                "data": decoded_data,
                "format": format_type,
                "method": f"yolo_extract_preprocessing_{technique}_crop_{idx}",
                "crop_path": crop_path,
                "image_path": image_path
            }
    
    # ========================================================================
    # All methods failed
    # ========================================================================
    print("\n✗ All decoding methods exhausted")
    return {
        "success": False,
        "error": "Could not decode QR code after all attempts",
        "methods_tried": ["direct", "preprocessing", "yolo_extraction", "crop_preprocessing"],
        "qr_regions_found": len(qr_crops),
        "image_path": image_path
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_qr_data(result: Dict):
    """Pretty print QR extraction results"""
    
    print("\n" + "="*70)
    print("                    📊 QR EXTRACTION RESULTS")
    print("="*70)
    
    if result["success"]:
        print("\n✅ STATUS: QR CODE SUCCESSFULLY DECODED\n")
        print(f"📄 Format: {result['format'].upper()}")
        print(f"🔧 Method: {result['method']}")
        print(f"📸 Source: {Path(result['image_path']).name}")
        
        if "crop_path" in result:
            print(f"✂️  Crop: {Path(result['crop_path']).name}")
        
        print("\n📋 Decoded Data:")
        print("-" * 70)
        
        data = result["data"]
        
        # Print based on format
        if data.get("format") == "xml":
            for key, value in data.items():
                if key != "format" and value:
                    print(f"   {key}: {value}")
        
        elif data.get("format") == "bigint":
            important_fields = ["name", "dob", "gender", "address", "pin_code", "vtc"]
            for field in important_fields:
                if field in data and data[field]:
                    print(f"   {field}: {data[field]}")
        
        else:
            for key, value in data.items():
                if value:
                    print(f"   {key}: {value}")
        
    else:
        print("\n❌ STATUS: QR CODE DECODING FAILED\n")
        print(f"🔴 Error: {result.get('error', 'Unknown error')}")
        print(f"📸 Source: {Path(result['image_path']).name}")
        
        if "methods_tried" in result:
            print(f"\n🔄 Methods attempted: {', '.join(result['methods_tried'])}")
        
        if "qr_regions_found" in result:
            print(f"📍 QR regions detected: {result['qr_regions_found']}")
    
    print("\n" + "="*70 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def qr_decoder(image_path):    
    result = extract_and_decode_qr(image_path)
    print_qr_data(result)
    return result