import xml.etree.ElementTree as ET

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           AADHAAR VERIFICATION PIPELINE — FINAL INTEGRATED VERSION         ║
║                                                                              ║
║  FLOW:                                                                       ║
║  QR Data + Image Folder (1 or 2 images)                                     ║
║       ↓                                                                      ║
║  OCR on each image → Concatenate all OCR text                               ║
║       ↓                                                                      ║
║  [APPROACH 1] Full-page OCR → Fuzzy Match                                   ║
║       ↓ Score >= 85%?                                                        ║
║       YES → AUTO-VERIFY ✅                                                   ║
║       NO  → [APPROACH 2] YOLO crops → Per-field OCR → Fuzzy Match           ║
║                  ↓ Score >= 85%?                                             ║
║                  YES → AUTO-VERIFY ✅ (OCR was just noisy in A1)            ║
║                  NO  → REJECT ❌  (Card content ≠ QR data)                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import cv2
import json
import os
import re
import glob
import numpy as np
from typing import List
from rapidfuzz import fuzz
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from ultralytics import YOLO

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

IMAGE_FOLDER = r"C:\Users\dhruv\OneDrive\Desktop\Aadhaar_Detection\Aadhaar_Trust\final_code\Image_Folder"
# ✅ CHANGED: now points to model2
MODEL_PATH   = r"C:\Users\dhruv\OneDrive\Desktop\Aadhaar_Detection\Aadhaar_Trust\aadhaar_full_pipeline\detect\train\weights\best.pt"
OUTPUT_JSON  = r"C:\Users\dhruv\OneDrive\Desktop\Aadhaar_Detection\final_output.json"

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")

# Thresholds
A1_PASS_THRESHOLD = 85
A2_PASS_THRESHOLD = 85
YOLO_CONF         = 0.25
OCR_PADDING_PX    = 5

# ✅ CHANGED: Model 2 class names mapped to what each field represents.
#    Used across the pipeline for display, filtering, and field routing.
MODEL2_CLASSES = {
    0:  "aadhaar_address",
    1:  "aadhaar_dob",
    2:  "aadhaar_gender",
    3:  "aadhaar_holder_name",
    4:  "aadhaar_logo",
    5:  "aadhaar_no",
    6:  "aadhaar_no_already_masked",
    7:  "aadhaar_photo",
    8:  "aadhaar_qr",
    9:  "aadhar_no_mask",
    10: "emblem",
    11: "gov_logo",
}

# ✅ CHANGED: Classes that carry no verifiable text — skip OCR on these crops
NON_TEXT_CLASSES = {"aadhaar_photo", "aadhaar_logo", "gov_logo", "emblem", "aadhaar_qr"}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 0 — FOLDER IMAGE LOADER
# ══════════════════════════════════════════════════════════════════════════════

def get_images_from_folder(folder_path: str) -> List[str]:
    if not os.path.isdir(folder_path):
        raise ValueError(f"Folder not found: {folder_path}")

    image_paths = []
    for ext in SUPPORTED_EXTENSIONS:
        image_paths.extend(glob.glob(os.path.join(folder_path, f"*{ext}")))
        image_paths.extend(glob.glob(os.path.join(folder_path, f"*{ext.upper()}")))

    image_paths = sorted(set(image_paths))

    if len(image_paths) == 0:
        raise ValueError(f"No supported images found in folder: {folder_path}")
    if len(image_paths) > 2:
        print(f"  ⚠  Warning: Found {len(image_paths)} images — using first 2 only.")
        image_paths = image_paths[:2]

    print(f"  📂 Found {len(image_paths)} image(s) in folder:")
    for p in image_paths:
        print(f"       • {os.path.basename(p)}")

    return image_paths


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — NORMALIZATION HELPERS  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def normalize(s) -> str:
    s = "" if s is None else str(s)
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_digits(s) -> str:
    return re.sub(r'\D', '', "" if s is None else str(s))

def normalize_ocr_digits(s: str) -> str:
    table = str.maketrans({'O': '0', 'o': '0', 'I': '1', 'l': '1', '|': '1', 'B': '8'})
    s = ("" if s is None else str(s)).translate(table)
    return re.sub(r'\D', '', s)

def is_numeric_heavy(s) -> bool:
    s = "" if s is None else str(s)
    if not s:
        return False
    return sum(c.isdigit() for c in s) >= max(4, len(s) * 0.5)

def is_masked(s: str) -> bool:
    return bool(re.search(r'X{4,}', ("" if s is None else str(s)).upper()))

def is_date(s: str) -> bool:
    return bool(re.match(r'^\d{1,4}[\-/\.]\d{1,2}[\-/\.]\d{2,4}$',
                         ("" if s is None else str(s)).strip()))

def normalize_date(s: str) -> str:
    return re.sub(r'\D', '', ("" if s is None else str(s)).strip())

def normalize_gender(s: str) -> str:
    s = ("" if s is None else str(s)).strip().lower()
    gender_map = {
        "m": "male", "ma": "male", "mal": "male", "male": "male",
        "men": "male", "man": "male",
        "f": "female", "fe": "female", "fem": "female", "fema": "female",
        "femal": "female", "female": "female", "women": "female", "woman": "female",
        "o": "other", "other": "other", "tg": "other", "transgender": "other",
        "trans": "other", "nb": "other", "non-binary": "other", "nonbinary": "other",
    }
    return gender_map.get(s, s)

GENDER_KEYWORDS = {
    "female": "female", "male": "male", "transgender": "other",
    "nonbinary": "other", "non binary": "other", "trans": "other", "other": "other",
}

def extract_gender_from_line(line: str) -> str:
    norm = normalize(line)
    for keyword in ["female", "male", "transgender", "nonbinary", "non binary", "trans", "other"]:
        if re.search(rf'\b{keyword}\b', norm):
            return GENDER_KEYWORDS[keyword]
    return ""

def best_fuzzy_match(value: str, ocr_lines: List[str]):
    best_score, best_line = 0, ""
    norm_val = normalize_gender(normalize(value))
    for line in ocr_lines:
        norm_line = normalize_gender(normalize(line))
        if len(norm_line) < len(norm_val) * 0.5:
            continue
        score = fuzz.token_set_ratio(norm_val, norm_line)
        if score > best_score:
            best_score, best_line = score, line.strip()
    return best_score, best_line


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — REGEX-BASED CLASS CORRECTION  ✅ UPDATED for Model 2 classes
# ══════════════════════════════════════════════════════════════════════════════

# ✅ CHANGED: Keys now use Model 2 class names exactly as returned by YOLO
FIELD_PATTERNS = {
    "aadhaar_no":             r'\b\d{4}\s?\d{4}\s?\d{4}\b',
    "aadhaar_no_already_masked": r'\bX{4}\s?\d{4}\s?\d{4}\b',
    "aadhar_no_mask":         r'\bX{4}\s?\d{4}\s?\d{4}\b',   # typo variant kept intentionally
    "aadhaar_dob":            r'\b\d{2}[\/\-]\d{2}[\/\-]\d{4}\b',
    "aadhaar_gender":         r'\b(male|female|MALE|FEMALE|पुरुष|महिला)\b',
    "aadhaar_address":        r'\b(s/o|d/o|w/o|c/o|village|dist|state|pin|near|at|po|ps)\b',
    "aadhaar_holder_name":    r'^[A-Z][a-z]+(?: [A-Z][a-z]+)+$',   # title-case name heuristic
}

def correct_class(predicted_class: str, text: str) -> str:
    """
    Override wrong YOLO labels using regex on the crop's OCR text.
    Only attempts correction for text-bearing classes.
    Non-text classes (photo, logo, qr, emblem) are returned unchanged.
    """
    # ✅ CHANGED: skip correction for visual-only crops
    if predicted_class in NON_TEXT_CLASSES:
        return predicted_class

    for true_class, pattern in FIELD_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            if true_class != predicted_class:
                print(f"    ⚠  Class corrected: '{predicted_class}' → '{true_class}'")
            return true_class

    return predicted_class


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — CORE FUZZY MATCH ENGINE  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def check_list_vs_ocr(ocr_text: str, ref_list: List) -> dict:
    ocr_lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
    results = []
    matched = 0
    ocr_digits_norm = normalize_ocr_digits(ocr_text)
    LONG_UID_THRESHOLD = 15

    for item in ref_list:
        item = "" if item is None else str(item).strip()

        item_gender_norm = normalize_gender(normalize(item))
        if item_gender_norm in ["male", "female", "other"]:
            gender_match, matched_gender_line = False, ""
            for line in ocr_lines:
                if extract_gender_from_line(line) == item_gender_norm:
                    gender_match, matched_gender_line = True, line
                    break
            results.append({"item": item, "digit_match": False, "gender_match": gender_match,
                             "fuzzy_score": 0, "matched_line": matched_gender_line,
                             "ok": gender_match, "note": "gender check"})
            if gender_match:
                matched += 1
            continue

        if is_date(item):
            norm_item_date = normalize_date(item)
            date_match, matched_date_line = False, ""
            for line in ocr_lines:
                for ld in re.findall(r'\d{1,4}[\-/\.]\d{1,2}[\-/\.]\d{2,4}', line):
                    if normalize_date(ld) == norm_item_date:
                        date_match, matched_date_line = True, line
                        break
                if date_match:
                    break
            if not date_match and norm_item_date in ocr_digits_norm:
                date_match, matched_date_line = True, "(found in digit stream)"
            results.append({"item": item, "digit_match": date_match, "gender_match": False,
                             "fuzzy_score": 0, "matched_line": matched_date_line,
                             "ok": date_match, "note": "date check"})
            if date_match:
                matched += 1
            continue

        if len(item) <= 1:
            results.append({"item": item, "digit_match": False, "gender_match": False,
                             "fuzzy_score": 0, "matched_line": "", "ok": True,
                             "note": "skipped (too short)"})
            matched += 1
            continue
        if is_masked(item):
            results.append({"item": item, "digit_match": False, "gender_match": False,
                             "fuzzy_score": 0, "matched_line": "", "ok": True,
                             "note": "skipped (masked value)"})
            matched += 1
            continue
        if len(extract_digits(item)) > LONG_UID_THRESHOLD and is_numeric_heavy(item):
            results.append({"item": item, "digit_match": False, "gender_match": False,
                             "fuzzy_score": 0, "matched_line": "", "ok": True,
                             "note": "skipped (long internal UID)"})
            matched += 1
            continue

        item_norm   = normalize(item)
        item_digits = extract_digits(item)

        digit_match = bool(item_digits and len(item_digits) >= 4
                           and item_digits in ocr_digits_norm)

        fuzzy_score, best_line, fuzzy_ok = 0, "", False
        if not is_numeric_heavy(item) and len(item_norm) >= 3:
            fuzzy_score, best_line = best_fuzzy_match(item_norm, ocr_lines)
            fuzzy_ok = fuzzy_score >= 75

        ok = digit_match or fuzzy_ok
        results.append({"item": item, "digit_match": digit_match, "gender_match": False,
                         "fuzzy_score": round(fuzzy_score, 2), "matched_line": best_line,
                         "ok": ok, "note": ""})
        if ok:
            matched += 1

    total_confidence = 0
    for r in results:
        if not r["ok"]:
            total_confidence += 0
        elif r["note"] in ["skipped (too short)", "skipped (masked value)",
                            "skipped (long internal UID)"]:
            total_confidence += 100
        elif r["note"] in ["gender check", "date check"]:
            total_confidence += 100
        elif r["digit_match"]:
            total_confidence += 100
        else:
            total_confidence += r["fuzzy_score"]

    final_score = (total_confidence / (len(ref_list) * 100)) * 100 if ref_list else 0
    # print(results)
    return {"final_score": round(final_score, 2), "results": results}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — OCR HELPERS  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def build_ocr_model():
    return ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)

def run_ocr_on_single_image(ocr_model, image_path: str) -> str:
    doc         = DocumentFile.from_images(image_path)
    result      = ocr_model(doc)
    json_output = result.export()

    lines_out = []
    for page in json_output["pages"]:
        prev_y_min, prev_y_max = None, None
        current_line = ""
        for block in page["blocks"]:
            for line in block["lines"]:
                for word in line["words"]:
                    geo   = word["geometry"]
                    y_min = float(geo[0][1])
                    y_max = float(geo[1][1])
                    text  = word["value"]
                    if prev_y_min is not None:
                        if (y_min - prev_y_min) <= 0.01 and (y_max - prev_y_max) <= 0.01:
                            current_line += " " + text
                        else:
                            lines_out.append(current_line.strip())
                            current_line = text
                    else:
                        current_line = text
                    prev_y_min, prev_y_max = y_min, y_max
        if current_line:
            lines_out.append(current_line.strip())

    return "\n".join(lines_out)

def run_full_page_ocr(ocr_model, image_paths: List[str]) -> str:
    all_ocr_parts = []
    for idx, image_path in enumerate(image_paths, start=1):
        print(f"\n  🔍 OCR on image {idx}/{len(image_paths)}: {os.path.basename(image_path)}")
        ocr_text = run_ocr_on_single_image(ocr_model, image_path)
        print(f"     → {len(ocr_text.splitlines())} lines extracted")
        all_ocr_parts.append(ocr_text)
    return "\n\n".join(all_ocr_parts)

def run_crop_ocr(ocr_model, crop_bgr: np.ndarray) -> str:
    success, buffer = cv2.imencode(".png", crop_bgr)
    if not success:
        return ""
    img_bytes = buffer.tobytes()
    doc      = DocumentFile.from_images(img_bytes)
    result   = ocr_model(doc)
    words    = []
    for page in result.export()["pages"]:
        for block in page["blocks"]:
            for line in block["lines"]:
                for word in line["words"]:
                    words.append(word["value"])
    return " ".join(words).strip()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — APPROACH 1  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def approach_1(ocr_model, image_paths: List[str], qr_values: List) -> dict:
    print("\n" + "─"*60)
    print("  APPROACH 1 — Full-page OCR (all images) + Fuzzy Match")
    print("─"*60)

    ocr_text = run_full_page_ocr(ocr_model, image_paths)

    print(f"\n  Combined OCR text ({len(ocr_text.splitlines())} lines total):")
    for line in ocr_text.splitlines():
        print(f"    {line}")

    report = check_list_vs_ocr(ocr_text, qr_values)

    print(f"\n  Score : {report['final_score']}%")
    _print_match_table(report["results"])
    # return {"final_score": round(final_score, 2), "results": results}

    return {"approach": 1, "ocr_text": ocr_text, **report}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — APPROACH 2  ✅ UPDATED for Model 2 classes
# ══════════════════════════════════════════════════════════════════════════════

def approach_2(ocr_model, yolo_model, image_paths: List[str], qr_values: List) -> dict:
    print("\n" + "─"*60)
    print("  APPROACH 2 — YOLO Crop OCR (all images) + Per-field Fuzzy Match")
    print("─"*60)

    all_yolo_regions = []

    for idx, image_path in enumerate(image_paths, start=1):
        print(f"\n  🔍 YOLO on image {idx}/{len(image_paths)}: {os.path.basename(image_path)}")

        image        = cv2.imread(image_path)
        H, W         = image.shape[:2]
        results_yolo = yolo_model(image_path, conf=YOLO_CONF)

        for result in results_yolo:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cls_id   = int(box.cls[0])
                cls_name = result.names[cls_id]   # ✅ model2 class name directly
                conf     = float(box.conf[0])

                # ✅ CHANGED: skip OCR entirely for visual-only classes
                if cls_name in NON_TEXT_CLASSES:
                    all_yolo_regions.append({
                        "source_image":   os.path.basename(image_path),
                        "class":          cls_name,
                        "original_class": cls_name,
                        "confidence":     round(conf, 3),
                        "bbox_px":        [x1, y1, x2, y2],
                        "ocr_text":       "",    # no OCR for photos/logos
                    })
                    continue

                # Pad crop slightly
                x1c = max(0, x1 - OCR_PADDING_PX)
                y1c = max(0, y1 - OCR_PADDING_PX)
                x2c = min(W, x2 + OCR_PADDING_PX)
                y2c = min(H, y2 + OCR_PADDING_PX)
                crop = image[y1c:y2c, x1c:x2c]

                crop_text       = run_crop_ocr(ocr_model, crop) if crop.size > 0 else ""
                # ✅ correct_class now works with model2 class names
                corrected_class = correct_class(cls_name, crop_text)

                all_yolo_regions.append({
                    "source_image":   os.path.basename(image_path),
                    "class":          corrected_class,
                    "original_class": cls_name,
                    "confidence":     round(conf, 3),
                    "bbox_px":        [x1, y1, x2, y2],
                    "ocr_text":       crop_text,
                })

    print(f"\n  YOLO detected {len(all_yolo_regions)} region(s) across all images:")
    print(f"  {'IMAGE':<20} {'CLASS':<30} {'CONF':>6}  {'OCR TEXT'}")
    print(f"  {'─'*20} {'─'*30} {'─'*6}  {'─'*30}")
    for r in sorted(all_yolo_regions, key=lambda x: (x["source_image"], x["bbox_px"][1])):
        corrected = f" → {r['class']}" if r['class'] != r['original_class'] else ""
        print(f"  {r['source_image']:<20} {r['original_class']:<30}{corrected} "
              f"{r['confidence']:>6.2f}  {r['ocr_text']}")

    # ✅ CHANGED: only include text-bearing crops in the match string
    combined_ocr = "\n".join(
        f"{r['class']}: {r['ocr_text']}"
        for r in all_yolo_regions
        if r["ocr_text"] and r["class"] not in NON_TEXT_CLASSES
    )

    print(f"\n  Combined field text for matching:\n")
    for line in combined_ocr.splitlines():
        print(f"    {line}")

    report = check_list_vs_ocr(combined_ocr, qr_values)

    print(f"\n  Score : {report['final_score']}%")
    _print_match_table(report["results"])

    return {"approach": 2, "regions": all_yolo_regions, "combined_ocr": combined_ocr, **report}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — DISPLAY HELPERS  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def _print_match_table(results: list):
    print(f"\n  {'ITEM':<30} {'OK':>4}  {'NOTE / MATCHED LINE'}")
    print(f"  {'─'*30} {'─'*4}  {'─'*35}")
    for r in results:
        ok_icon = "✅" if r["ok"] else "❌"
        note    = r["note"] if r["note"] else r.get("matched_line", "")[:40]
        print(f"  {str(r['item']):<30} {ok_icon}    {note}")

def draw_annotated_images(image_paths: List[str], regions: list) -> List[str]:
    annotated_paths = []
    for image_path in image_paths:
        image    = cv2.imread(image_path)
        basename = os.path.basename(image_path)
        img_regions = [r for r in regions if r["source_image"] == basename]

        for r in img_regions:
            x1, y1, x2, y2 = r["bbox_px"]
            # ✅ CHANGED: different colour for visual-only vs text crops
            color = (180, 180, 180) if r["class"] in NON_TEXT_CLASSES else (0, 255, 0)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            label = f"{r['class']} | {r['ocr_text'][:25]}" if r["ocr_text"] else r["class"]
            cv2.putText(image, label, (x1, max(y1 - 8, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 200, 255), 1)

        # name, ext = os.path.splitext(image_path)
        # out_path  = f"{name}_annotated{ext}"
        # cv2.imwrite(out_path, image)
        # annotated_paths.append(out_path)
        # print(f"  🖼  Annotated → {out_path}")

    return annotated_paths


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — MAIN PIPELINE  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline(image_folder: str, qr_values: List, save_json: bool = True):

    print("\n" + "═"*60)
    print("  AADHAAR VERIFICATION PIPELINE")
    print("═"*60)

    image_paths = get_images_from_folder(image_folder)
    print(f"\n  QR fields ({len(qr_values)}) : {qr_values}")

    print("\n  Loading models...")
    ocr_model  = build_ocr_model()
    yolo_model = YOLO(MODEL_PATH)
    print("  Models loaded ✓")

    final_result = {}

    a1 = approach_1(ocr_model, image_paths, qr_values)
    ocr_texts = a1["ocr_text"]
    if a1["final_score"] >= A1_PASS_THRESHOLD:
        decision = "AUTO-VERIFY ✅"
        final_result = {**a1, "decision": decision, "approach_used": 1,
                        "images_processed": image_paths}
        print("RESULT: ",final_result)
        
    else:
        print(f"\n  Approach 1 score {a1['final_score']}% < {A1_PASS_THRESHOLD}%")
        print("  → OCR may be noisy. Escalating to Approach 2...")

        a2 = approach_2(ocr_model, yolo_model, image_paths, qr_values)

        if a2["final_score"] >= A2_PASS_THRESHOLD:
            decision = "AUTO-VERIFY ✅  (passed via YOLO crop OCR)"
        else:
            decision = "REJECT ❌  (card content does not match QR data)"
            final_result = {**a1, "decision": decision, "approach_used": 2,
                        "images_processed": image_paths}
            return final_result        
            
        final_result = {
            "approach_used":    2,
            "images_processed": image_paths,
            "approach_1_score": a1["final_score"],
            "approach_1_ocr":   a1["ocr_text"],
            "approach_2_score": a2["final_score"],
            "regions":          a2.get("regions", []),
            "decision":         decision,
            "final_score":      a2["final_score"],
            "results":          a2["results"],
            "ocr_text":         ocr_texts
        }

        if a2.get("regions"):
            ann_paths = draw_annotated_images(image_paths, a2["regions"])
            final_result["annotated_images"] = ann_paths

    print("\n" + "═"*60)
    print(f"  DECISION : {final_result['decision']}")
    print(f"  SCORE    : {final_result['final_score']}%")
    print(f"  APPROACH : {final_result['approach_used']}")
    print(f"  IMAGES   : {[os.path.basename(p) for p in image_paths]}")
    print("═"*60)

    if save_json:
        serializable = {k: v for k, v in final_result.items() if k != "results"}
        serializable["match_details"] = final_result.get("results", [])
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=4, ensure_ascii=False)
        print(f"\n  ✅ Full report saved → {OUTPUT_JSON}")

    return final_result


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

# if __name__ == "__main__":
#     run_pipeline(IMAGE_FOLDER, best_qr_list)