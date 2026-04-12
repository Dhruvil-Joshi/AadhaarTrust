from ultralytics import YOLO
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    AADHAAR_MODEL_PATH = Path(r"C:\Users\dhruv\OneDrive\Desktop\Aadhaar_Detection\Aadhaar_Trust\aadhaar_full_pipeline\detect\train\weights\best.pt")
    SPLICE_MODEL_PATH = Path(r"C:\Users\dhruv\Downloads\yolo_runsnew_2\detect\train\weights\best.pt")

    CONF_THRESHOLD = 0.25
    IOU_THRESHOLD = 0.15
    CONTAINMENT_THRESHOLD = 0.70

    CRITICAL_FIELDS = ["aadhaar_photo", "aadhaar_no"]

    CLASS_MAP = {
        "aadhaar_no": "aadhaar number",
        "aadhar_no_mask": "aadhaar number",
        "aadhaar_no_already_masked": "aadhaar number",
        "aadhaar_address": "address",
        "aadhaar_dob": "dob",
        "aadhaar_gender": "gender",
        "aadhaar_holder_name": "name",
        "aadhaar_photo": "photo",
        "aadhaar_logo": "logo",
        "emblem": "emblem",
        "gov_logo": "emblem",
        "aadhaar_qr": "qr"
    }


# ============================================================================
# LOAD MODELS ONCE
# ============================================================================

print("⏳ Loading models (only once)...")
AADHAAR_MODEL = YOLO(str(Config.AADHAAR_MODEL_PATH))
SPLICE_MODEL = YOLO(str(Config.SPLICE_MODEL_PATH))
print("✅ Models loaded\n")


# ============================================================================
# HELPERS
# ============================================================================

def calculate_iou(box_a, box_b):
    x_left = max(box_a[0], box_b[0])
    y_top = max(box_a[1], box_b[1])
    x_right = min(box_a[2], box_b[2])
    y_bottom = min(box_a[3], box_b[3])

    intersection = max(0, x_right - x_left) * max(0, y_bottom - y_top)
    if intersection == 0:
        return 0.0

    area_a = (box_a[2]-box_a[0])*(box_a[3]-box_a[1])
    area_b = (box_b[2]-box_b[0])*(box_b[3]-box_b[1])
    return intersection / float(area_a + area_b - intersection)


def calculate_containment(field_box, splice_box):
    x_left = max(field_box[0], splice_box[0])
    y_top = max(field_box[1], splice_box[1])
    x_right = min(field_box[2], splice_box[2])
    y_bottom = min(field_box[3], splice_box[3])

    intersection = max(0, x_right-x_left)*max(0, y_bottom-y_top)
    if intersection == 0:
        return 0.0

    field_area = (field_box[2]-field_box[0])*(field_box[3]-field_box[1])
    return intersection / field_area if field_area > 0 else 0.0


def extract_detections(results):
    detections = []

    if not results or results[0].boxes is None:
        return detections

    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])

        cls_id = int(box.cls[0])
        raw_label = results[0].names[cls_id]
        label = Config.CLASS_MAP.get(raw_label, raw_label)

        detections.append({
            "bbox": [x1, y1, x2, y2],
            "confidence": conf,
            "label": label
        })

    return detections


def check_critical_fields(all_boxes):
    labels = {b["label"].lower() for b in all_boxes}
    presence = {}

    for field in Config.CRITICAL_FIELDS:
        if field == "aadhaar_no":
            presence[field] = any("aadhaar number" in l for l in labels)
        elif field == "aadhaar_photo":
            presence[field] = any("photo" in l for l in labels)

    return presence


def map_tampering(all_boxes, splice_boxes):
    tampered = {}
    mapped_splices = set()

    for i, splice in enumerate(splice_boxes):
        for field in all_boxes:
            iou = calculate_iou(splice["bbox"], field["bbox"])
            cont = calculate_containment(field["bbox"], splice["bbox"])

            if iou > Config.IOU_THRESHOLD or cont > Config.IOU_THRESHOLD:
                mapped_splices.add(i)
                label = field["label"]

                pct = 100 if cont >= Config.CONTAINMENT_THRESHOLD else int(iou * 100)

                if label not in tampered:
                    tampered[label] = {"tampering_percentage": pct, "splice_count": 0}

                tampered[label]["splice_count"] += 1

    unmapped = [s for i, s in enumerate(splice_boxes) if i not in mapped_splices]
    return tampered, unmapped


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def aadhaar_pipeline(image_path, noiseprint_path):
    print("\n🔍 Aadhaar Full Pipeline\n")

    aadhaar_boxes = extract_detections(
        AADHAAR_MODEL(image_path, conf=Config.CONF_THRESHOLD, verbose=False)
    )

    splice_boxes = extract_detections(
        SPLICE_MODEL(noiseprint_path, conf=Config.CONF_THRESHOLD, verbose=False)
    )

    critical = check_critical_fields(aadhaar_boxes)
    tampered, unmapped = map_tampering(aadhaar_boxes, splice_boxes)

    is_tampered = (
        len(tampered) > 0 or
        len(unmapped) > 0 or
        not all(critical.values())
    )

    print("VERDICT:", "TAMPERED ❌" if is_tampered else "AUTHENTIC ✅")

    return {
        "status": "processed",
        "is_tampered": is_tampered,
        "tampered_fields": tampered,
        "missing_critical": [k for k, v in critical.items() if not v]
    }


# ============================================================================
# 🚀 GLOBAL EXECUTION WITH STRICT FAIL LOGIC
# ============================================================================

def process_all_images(image_pairs):
    final_result = True
    issues = []

    print(f"\n📂 Total Images: {len(image_pairs)}")

    for i, (image_path, noiseprint_path) in enumerate(image_pairs):
        print("\n" + "="*60)
        print(f"🔄 Processing Image {i+1}/{len(image_pairs)}")
        print("="*60)

        result = aadhaar_pipeline(image_path, noiseprint_path)

        print("\n📊 Detailed Report:")

        # ================= SHOW DETAILS =================
        if result.get("is_tampered", False):
            print("❌ Document is TAMPERED")

            # 🔴 Tampered fields
            if result.get("tampered_fields"):
                print("\n🔧 Tampered Fields:")
                for field, info in result["tampered_fields"].items():
                    print(f" - {field}")
                    print(f"   ➤ Tampering % : {info['tampering_percentage']}%")
                    print(f"   ➤ Splice Count: {info['splice_count']}")

            # 🔴 Missing critical fields
            if result.get("missing_critical"):
                print("\n⚠️ Missing Critical Fields:")
                for field in result["missing_critical"]:
                    print(f" - {field}")

            final_result = False
            issues.append(f"{image_path} → Failed validation")

        else:
            print("✅ Document is AUTHENTIC")

    # ================= FINAL OUTPUT =================
    print("\n" + "="*60)
    print("📊 FINAL RESULT")
    print("="*60)

    print("✅ ALL CLEAR" if final_result else "❌ DOCUMENT SET FAILED")

    if not final_result:
        print("\n⚠️ Issues found:")
        for issue in issues:
            print("-", issue)

    return {
        "final_result": final_result,
        "issues": issues
    }
# ============================================================================
# ▶️ USAGE EXAMPLE
# ============================================================================
