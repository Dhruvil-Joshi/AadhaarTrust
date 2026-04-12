from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Central configuration"""
    
    # Import settings from config module
    from config import settings as app_settings
    
    # Model paths - use settings from config.py, fallback to relative paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
    # Try to use settings from config, otherwise use relative paths
    try:
        AADHAAR_MODEL_PATH = getattr(app_settings, 'AADHAAR_REGION_DETECTION_PATH', None) or (BASE_DIR / "models" / "paths" / "aadhaar_region_detection" / "best.pt")
        SPLICE_MODEL_PATH = getattr(app_settings, 'SPLICING_REGION_DETECTION_PATH', None) or (BASE_DIR / "models" / "paths" / "forgery" / "aadhaar_splicing_detection.pt")
        QR_MODEL_PATH = getattr(app_settings, 'QR_DETECTION_MODEL_PATH', None) or (BASE_DIR / "models" / "paths" / "qr" / "best.pt")
    except Exception as e:
        # Fallback to relative paths from project root
        AADHAAR_MODEL_PATH = BASE_DIR / "models" / "paths" / "aadhaar_region_detection" / "best.pt"
        SPLICE_MODEL_PATH = BASE_DIR / "models" / "paths" / "forgery" / "aadhaar_splicing_detection.pt"
        QR_MODEL_PATH = BASE_DIR / "models" / "paths" / "qr" / "best.pt"
    
    # Validate that model files exist
    def _check_model_path(path, name):
        """Check if model path exists, try alternatives if not"""
        if path.exists():
            return path
        
        # Try alternative extensions
        alternatives = [
            path.with_suffix('.pt'),
            path.with_suffix('.pth'),
            path.parent / "best.pt",
            path.parent / "best.pth",
        ]
        
        for alt in alternatives:
            if alt.exists():
                return alt
        
        # If still not found, raise helpful error
        raise FileNotFoundError(
            f"{name} model not found at: {path}\n"
            f"Tried alternatives: {alternatives}\n"
            f"Please ensure the model file exists in: {path.parent}"
        )
    
    # Validate all model paths
    AADHAAR_MODEL_PATH = _check_model_path(Path(AADHAAR_MODEL_PATH), "Aadhaar Region Detection")
    SPLICE_MODEL_PATH = _check_model_path(Path(SPLICE_MODEL_PATH), "Splice Detection")
    QR_MODEL_PATH = _check_model_path(Path(QR_MODEL_PATH), "QR Detection")
    
    # Input paths
    IMAGE_PATH =""
    NOISE_IMAGE_PATH = ""

    # Output - use settings from config if available
    try:
        OUTPUT_DIR = getattr(app_settings, 'SPLICING_MAPS_DIR', None) or (BASE_DIR / "data" / "output" / "splicing_maps")
    except:
        OUTPUT_DIR = BASE_DIR / "data" / "output" / "splicing_maps"
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_IMAGE_NAME = "tampering_result.jpg"
    
    # Detection settings
    CONF_THRESHOLD = 0.25
    IOU_THRESHOLD = 0.15
    CONTAINMENT_THRESHOLD = 0.70
    
    # Critical fields that must be present
    CRITICAL_FIELDS = ["photo", "aadhaar number"]
    
    # Visualization
    COLOR_TAMPERED = (0, 0, 255)      # Red
    COLOR_SAFE = (0, 255, 0)          # Green
    COLOR_SPLICE = (255, 0, 255)      # Magenta
    COLOR_QR = (255, 255, 0)          # Cyan for QR
    BOX_THICKNESS = 3

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_iou(box_a: List[int], box_b: List[int]) -> float:
    """Calculate Intersection over Union"""
    x_left = max(box_a[0], box_b[0])
    y_top = max(box_a[1], box_b[1])
    x_right = min(box_a[2], box_b[2])
    y_bottom = min(box_a[3], box_b[3])
    
    intersection = max(0, x_right - x_left) * max(0, y_bottom - y_top)
    if intersection == 0:
        return 0.0
    
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - intersection
    
    return intersection / float(union)


def calculate_containment(field_box: List[int], splice_box: List[int]) -> float:
    """Calculate what % of field is inside splice region"""
    x_left = max(field_box[0], splice_box[0])
    y_top = max(field_box[1], splice_box[1])
    x_right = min(field_box[2], splice_box[2])
    y_bottom = min(field_box[3], splice_box[3])
    
    intersection = max(0, x_right - x_left) * max(0, y_bottom - y_top)
    if intersection == 0:
        return 0.0
    
    field_area = (field_box[2] - field_box[0]) * (field_box[3] - field_box[1])
    return intersection / float(field_area) if field_area > 0 else 0.0


def extract_detections(results, label_override=None) -> List[Dict]:
    """Extract bounding boxes from YOLO results"""
    detections = []
    
    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        confidence = float(box.conf[0])
        
        detection = {
            "bbox": [x1, y1, x2, y2],
            "confidence": confidence
        }
        
        # Use override label if provided (for QR model)
        if label_override:
            detection["label"] = label_override
        elif hasattr(box, 'cls'):
            cls_id = int(box.cls[0])
            label = results[0].names[cls_id]
            detection["label"] = label
        
        detections.append(detection)
    
    return detections


def merge_detections(aadhaar_boxes: List[Dict], qr_boxes: List[Dict]) -> List[Dict]:
    """Merge Aadhaar and QR detections, avoiding duplicates"""
    merged = aadhaar_boxes.copy()
    
    for qr_box in qr_boxes:
        # Check if QR already detected by aadhaar model
        is_duplicate = False
        for aadhaar_box in aadhaar_boxes:
            if aadhaar_box.get("label", "").lower() in ["qr", "qr code", "qrcode"]:
                iou = calculate_iou(qr_box["bbox"], aadhaar_box["bbox"])
                if iou > 0.5:  # If IoU > 50%, consider it same QR code
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            merged.append(qr_box)
    
    return merged


def check_critical_fields(all_boxes: List[Dict]) -> Dict[str, bool]:
    """Check which critical fields are present"""
    detected_labels = {box.get("label", "").lower().replace(" ", "") for box in all_boxes}
    
    presence = {}
    for critical_field in Config.CRITICAL_FIELDS:
        # Normalize field name
        field_normalized = critical_field.lower().replace(" ", "")
        
        # Check various representations
        is_present = any(
            field_normalized in label or label in field_normalized
            for label in detected_labels
        )
        
        # Special handling for QR
        if critical_field == "qr":
            is_present = any(
                "qr" in label.lower() 
                for label in detected_labels
            )
        
        presence[critical_field] = is_present
    
    return presence


def map_tampering(all_boxes: List[Dict], 
                  splice_boxes: List[Dict]) -> Tuple[Dict, List[Dict]]:
    """Map splice regions to all detected fields"""
    tampered_fields = {}
    mapped_splices = set()
    
    for splice_idx, splice in enumerate(splice_boxes):
        splice_id = f"Splice #{splice_idx + 1}"
        
        for field in all_boxes:
            iou = calculate_iou(splice["bbox"], field["bbox"])
            containment = calculate_containment(field["bbox"], splice["bbox"])
            
            if iou > Config.IOU_THRESHOLD or containment > Config.IOU_THRESHOLD:
                mapped_splices.add(splice_idx)
                field_label = field.get("label", "unknown")
                
                # Determine tampering level
                if containment >= Config.CONTAINMENT_THRESHOLD:
                    tampering_pct = 100
                    tampering_type = "FULLY CONTAINED"
                else:
                    tampering_pct = int(iou * 100)
                    tampering_type = "PARTIAL OVERLAP"
                
                if field_label not in tampered_fields:
                    tampered_fields[field_label] = {
                        "tampering_percentage": tampering_pct,
                        "tampering_type": tampering_type,
                        "containment": containment,
                        "bbox": field["bbox"],
                        "splice_count": 0
                    }
                
                tampered_fields[field_label]["splice_count"] += 1
                
                if tampering_pct > tampered_fields[field_label]["tampering_percentage"]:
                    tampered_fields[field_label]["tampering_percentage"] = tampering_pct
                    tampered_fields[field_label]["tampering_type"] = tampering_type
    
    # Unmapped splices
    unmapped = []
    for idx, splice in enumerate(splice_boxes):
        if idx not in mapped_splices:
            unmapped.append({
                "splice_id": f"Splice #{idx + 1}",
                "bbox": splice["bbox"]
            })
    
    return tampered_fields, unmapped


def visualize_result(image_path: Path, 
                    all_boxes: List[Dict],
                    splice_boxes: List[Dict],
                    tampered_fields: Dict,
                    unmapped_splices: List[Dict],
                    critical_field_status: Dict[str, bool],
                    output_path: Path):
    """Create comprehensive visualization"""
    image = cv2.imread(str(image_path))
    
    # Check if document is tampered
    missing_critical = [f for f, present in critical_field_status.items() if not present]
    is_tampered = len(tampered_fields) > 0 or len(unmapped_splices) > 0 or len(missing_critical) > 0
    
    if not is_tampered:
        # If authentic, just save the original image cleaned
        # We can add a subtle water mark or just leave it clean as requested
        # User asked: "if there is no issue then display the original image there"
        cv2.imwrite(str(output_path), image)
        return

    # If tampered, visualize ONLY the issues
    overlay = image.copy()
    
    # Draw splice regions (transparent) - ONLY if they match a field or are unmapped
    # actually user said "only show the red area in forgery detection"
    # so we focus on unmapped splices and tampered fields
    
    # Draw all detected fields - FILTERED for issues
    for field in all_boxes:
        label = field.get("label", "field")
        
        # Only draw if tampered
        if label in tampered_fields:
            x1, y1, x2, y2 = field["bbox"]
            color = Config.COLOR_TAMPERED
            pct = tampered_fields[label]["tampering_percentage"]
            text = f"{label} - {pct}% TAMPERED"
            
            cv2.rectangle(image, (x1, y1), (x2, y2), color, Config.BOX_THICKNESS)
            
            # Label background
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(image, (x1, y1-th-8), (x1+tw, y1), color, -1)
            cv2.putText(image, text, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    # Draw unmapped splices
    for unmapped in unmapped_splices:
        x1, y1, x2, y2 = unmapped["bbox"]
        
        # Dashed red border
        for x in range(x1, x2, 20):
            cv2.line(image, (x, y1), (min(x+10, x2), y1), (0,0,255), 4)
            cv2.line(image, (x, y2), (min(x+10, x2), y2), (0,0,255), 4)
        for y in range(y1, y2, 20):
            cv2.line(image, (x1, y), (x1, min(y+10, y2)), (0,0,255), 4)
            cv2.line(image, (x2, y), (x2, min(y+10, y2)), (0,0,255), 4)
        
        cv2.putText(image, "REMOVED FIELD", (x1, y1-5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
    
    # Summary header - Only if tampered
    verdict = "TAMPERED/INVALID"
    color = Config.COLOR_TAMPERED
    
    cv2.putText(image, f"VERDICT: {verdict}", (10, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 4)
    cv2.putText(image, f"VERDICT: {verdict}", (10, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
    
    # Critical field warnings
    if missing_critical:
        y_offset = 80
        for field in missing_critical:
            warning = f"MISSING: {field.upper()}"
            cv2.putText(image, warning, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 3)
            cv2.putText(image, warning, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,139), 2)
            y_offset += 35
    
    cv2.imwrite(str(output_path), image)

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def locate_forgery(filename_original, filename_noiseprint, output_path: Path = None):
    """Main detection pipeline with QR detection"""
    
    # Ensure output directory exists (already created in Config, but double-check)
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Header
    print("\n" + "="*70)
    print("           🔍 AADHAAR FORGERY DETECTION SYSTEM")
    print("="*70 + "\n")
    
    # Load models
    print("⏳ Loading AI models...")
    aadhaar_model = YOLO(str(Config.AADHAAR_MODEL_PATH))
    splice_model = YOLO(str(Config.SPLICE_MODEL_PATH))
    qr_model = YOLO(str(Config.QR_MODEL_PATH))
    Config.IMAGE_PATH = filename_original
    Config.NOISE_IMAGE_PATH = filename_noiseprint
    print("✓ All models loaded successfully\n")
    
    # Run detections
    print("📄 Analyzing document...")
    print("   ├─ Detecting Aadhaar fields...")
    aadhaar_results = aadhaar_model(str(Config.IMAGE_PATH), conf=Config.CONF_THRESHOLD, verbose=False)
    aadhaar_boxes = extract_detections(aadhaar_results)
    
    print("   ├─ Detecting QR codes...")
    qr_results = qr_model(str(Config.IMAGE_PATH), conf=Config.CONF_THRESHOLD, verbose=False)
    qr_boxes = extract_detections(qr_results, label_override="qr")
    
    print("   └─ Detecting splice regions...")
    splice_results = splice_model(str(Config.NOISE_IMAGE_PATH), conf=Config.CONF_THRESHOLD, verbose=False)
    splice_boxes = extract_detections(splice_results)
    
    # Merge all detections
    all_boxes = merge_detections(aadhaar_boxes, qr_boxes)
    
    print(f"✓ Detection complete:")
    print(f"   • Aadhaar fields: {len(aadhaar_boxes)}")
    print(f"   • QR codes: {len(qr_boxes)}")
    print(f"   • Splice regions: {len(splice_boxes)}")
    print(f"   • Total fields: {len(all_boxes)}\n")
    
    # Check critical fields
    print("🔍 Checking critical fields...")
    critical_field_status = check_critical_fields(all_boxes)
    missing_critical = [f for f, present in critical_field_status.items() if not present]
    
    if missing_critical:
        print(f"⚠️  Missing critical fields: {', '.join([f.upper() for f in missing_critical])}\n")
    else:
        print("✓ All critical fields detected\n")
    
    # Analyze tampering
    print("🔬 Analyzing tampering patterns...")
    tampered_fields, unmapped_splices = map_tampering(all_boxes, splice_boxes)
    
    # Create visualization
    if output_path is None:
        output_path = Config.OUTPUT_DIR / Config.OUTPUT_IMAGE_NAME
        
    visualize_result(Config.IMAGE_PATH, all_boxes, splice_boxes, 
                    tampered_fields, unmapped_splices, critical_field_status, output_path)
    
    # Results
    print("\n" + "="*70)
    print("                        📊 ANALYSIS RESULTS")
    print("="*70 + "\n")
    
    # Verdict
    is_tampered = len(tampered_fields) > 0 or len(unmapped_splices) > 0 or len(missing_critical) > 0
    
    if is_tampered:
        print("🚨 VERDICT: DOCUMENT IS TAMPERED/INVALID\n")
    else:
        print("✅ VERDICT: DOCUMENT IS AUTHENTIC\n")
    
    # Critical fields status
    print("🔐 Critical Fields Status:")
    for field, present in critical_field_status.items():
        status_icon = "✓" if present else "✗"
        status_text = "DETECTED" if present else "MISSING"
        print(f"   {status_icon} {field.upper()}: {status_text}")
    print()
    
    # Statistics
    print("📈 Detection Statistics:")
    print(f"   • Total Fields Detected: {len(all_boxes)}")
    print(f"   • Splice Regions Found: {len(splice_boxes)}")
    print(f"   • Tampered Fields: {len(tampered_fields)}")
    print(f"   • Removed/Missing Fields: {len(unmapped_splices)}\n")
    
    # Tampered fields detail
    if tampered_fields:
        print("⚠️  TAMPERED FIELDS DETECTED:\n")
        for field_name, data in tampered_fields.items():
            print(f"   📍 {field_name.upper()}")
            print(f"      ├─ Tampering Level: {data['tampering_percentage']}%")
            print(f"      ├─ Type: {data['tampering_type']}")
            print(f"      └─ Affected by {data['splice_count']} splice region(s)\n")
    
    # Unmapped splices
    if unmapped_splices:
        print("🚨 CRITICAL ALERT: FIELD REMOVAL DETECTED\n")
        for unmapped in unmapped_splices:
            print(f"   ⚠️  {unmapped['splice_id']}")
            print(f"      └─ No corresponding field found (possible deletion)\n")
    
    # Safe fields
    safe_fields = [f for f in all_boxes if f.get("label") not in tampered_fields]
    if safe_fields:
        print("✅ AUTHENTIC FIELDS:\n")
        for field in safe_fields:
            label = field.get('label', 'unknown').upper()
            if "qr" in label.lower():
                print(f"   ✓ {label} (QR Code Verified)")
            else:
                print(f"   ✓ {label}")
        print()
    
    # Missing critical fields warning
    if missing_critical:
        print("🚨 CRITICAL FIELDS MISSING:\n")
        for field in missing_critical:
            print(f"   ✗ {field.upper()} - NOT DETECTED")
            print(f"      └─ Required for valid Aadhaar verification\n")
    
    # Output files
    print("="*70)
    print("📁 Output saved to:")
    print(f"   {output_path}")
    print("="*70 + "\n")
    
    # Final verdict with recommendation
    if missing_critical:
        print("⛔ RECOMMENDATION: REJECT THIS DOCUMENT")
        print("   Critical fields are missing. Document is invalid.\n")
    elif is_tampered:
        print("⛔ RECOMMENDATION: REJECT THIS DOCUMENT")
        print("   This Aadhaar card shows signs of digital manipulation.\n")
    else:
        print("✓ RECOMMENDATION: DOCUMENT APPEARS VALID")
        print("   No tampering detected. Proceed with verification.\n")
    
    return {
        "is_tampered": is_tampered,
        "missing_critical": missing_critical,
        "tampered_count": len(tampered_fields),
        "removed_count": len(unmapped_splices),
        "qr_detected": any("qr" in f.get("label", "").lower() for f in all_boxes),
        "tampered_fields": tampered_fields
    }

