import gzip
import cv2
import zxingcpp
import numpy as np
from io import BytesIO
from typing import Optional, Dict, Tuple
import xml.etree.ElementTree as ET
from ultralytics import YOLO
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

class QRConfig:
    QR_MODEL_PATH = Path(r"C:\Users\dhruv\OneDrive\Desktop\Aadhaar_Detection\Aadhaar_Trust\aadhaar_full_pipeline\detect\train\weights\best.pt")
    OUTPUT_DIR = Path("extracted_qr_raw")
    CONFIDENCE_THRESHOLD = 0.25
    QR_PADDING = 15
    FIELD_INDEX_VTC = 17


# ============================================================================
# LOAD MODEL ONCE (IMPORTANT 🚀)
# ============================================================================

MODEL2 = YOLO(QRConfig.QR_MODEL_PATH)


# ============================================================================
# DECODING FUNCTIONS
# ============================================================================

def decode_qr_bigint(bigint_text: str) -> Dict:
    try:
        bigint_value = int(bigint_text)
        byte_array = bigint_value.to_bytes((bigint_value.bit_length() + 7) // 8, byteorder="big")

        with gzip.GzipFile(fileobj=BytesIO(byte_array)) as f:
            decompressed_bytes = f.read()

        DELIM = 255
        fields, start = [], 0

        while start < len(decompressed_bytes):
            try:
                end = decompressed_bytes.index(DELIM, start)
            except ValueError:
                end = len(decompressed_bytes)

            field_bytes = decompressed_bytes[start:end]

            if len(fields) == 0:
                value = field_bytes[0] & 0b11
            else:
                try:
                    value = field_bytes.decode("ISO-8859-1")
                except:
                    value = str(field_bytes)

            fields.append(value)
            start = end + 1

            if len(fields) > QRConfig.FIELD_INDEX_VTC:
                break
        fields.append(decompressed_bytes)
        return {
            "format": "bigint",
            "qr_values": fields   # ✅ FULL RAW STRUCTURE
        }

    except Exception as e:
        return {"format": "bigint", "error": str(e)}


def decode_qr_xml(xml_text: str) -> Dict:
    try:
        root = ET.fromstring(xml_text)
        return {"format": "xml", **root.attrib}
    except Exception as e:
        return {"format": "xml", "error": str(e)}


def decode_qr_text(result) -> Tuple[Optional[Dict], str]:
    if not result or not result.text:
        return None, "none"

    text = result.text.strip()

    if text.startswith("<"):
        return decode_qr_xml(text), "xml"
    elif text.isdigit():
        return decode_qr_bigint(text), "bigint"
    else:
        return {"format": "unknown", "text": text}, "unknown"


# ============================================================================
# QR DETECTION USING MODEL2
# ============================================================================

def extract_qr_regions(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return []

    QRConfig.OUTPUT_DIR.mkdir(exist_ok=True)

    results = MODEL2(image_path, conf=QRConfig.CONFIDENCE_THRESHOLD, verbose=False)

    qr_crops = []
    h, w = img.shape[:2]

    for r in results:
        if r.boxes is None:
            continue

        for box in r.boxes:
            cls_id = int(box.cls[0])
            class_name = MODEL2.names[cls_id].lower()

            # ✅ ONLY QR CLASS
            if class_name == "aadhaar_qr":
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                pad = QRConfig.QR_PADDING
                x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
                x2, y2 = min(w, x2 + pad), min(h, y2 + pad)

                crop = img[y1:y2, x1:x2]

                save_path = QRConfig.OUTPUT_DIR / f"qr_{len(qr_crops)+1}.png"
                cv2.imwrite(str(save_path), crop)

                qr_crops.append((crop, str(save_path)))

    return qr_crops


# ============================================================================
# PREPROCESSING
# ============================================================================

def apply_preprocessing(img):
    variations = []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    variations.append(gray)
    variations.append(cv2.GaussianBlur(gray, (5,5), 0))
    variations.append(cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2))

    return variations


def try_decode(img):
    for v in apply_preprocessing(img):
        result = zxingcpp.read_barcode(v)
        if result and result.text:
            return decode_qr_text(result)
    return None, "none"


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def qr_decoder(image_path: str):
    print(f"\n📸 Processing: {Path(image_path).name}")

    img = cv2.imread(image_path)
    if img is None:
        return {"success": False, "error": "Image not found"}

    # Step 1: Direct
    result = zxingcpp.read_barcode(img)
    if result and result.text:
        data, fmt = decode_qr_text(result)
        return {"success": True, "data": data, "method": "direct"}

    # Step 2: Preprocessing
    data, fmt = try_decode(img)
    if data:
        return {"success": True, "data": data, "method": "preprocessing"}

    # Step 3: YOLO QR extraction
    crops = extract_qr_regions(image_path)

    for crop, path in crops:
        result = zxingcpp.read_barcode(crop)
        if result and result.text:
            data, fmt = decode_qr_text(result)
            return {"success": True, "data": data, "method": "yolo_crop"}

        data, fmt = try_decode(crop)
        if data:
            return {"success": True, "data": data, "method": "yolo_preprocessed"}

    return {"success": False, "error": "QR not decoded"}


# ============================================================================
# FOLDER PROCESSING (DYNAMIC ✅)
# ============================================================================

def process_image_folder(folder_path: str):
    folder = Path(folder_path)

    images = [p for p in folder.iterdir() if p.suffix.lower() in [".jpg",".png",".jpeg"]]

    results = []

    for img in sorted(images):
        res = qr_decoder(str(img))
        results.append({"image": img.name, "result": res})

    return results