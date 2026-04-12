from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import cv2
from collections import Counter

ocr_model = ocr_predictor(pretrained=True)

def run_crop_ocr(ocr_model, crop):
    success, buffer = cv2.imencode(".png", crop)
    if not success:
        return ""

    doc = DocumentFile.from_images(buffer.tobytes())
    result = ocr_model(doc)

    words = []
    for page in result.export()["pages"]:
        for block in page["blocks"]:
            for line in block["lines"]:
                for word in line["words"]:
                    words.append(word["value"])

    return " ".join(words)

def extract_aadhaar_numbers(result, front_path, back_path):

    extracted_numbers = []
    if not result or "results" not in result or len(result["results"]) < 2:
        print("[ERROR] Invalid detection_result format")
        return []
    try:
        if result["results"][0]["reason"] == 'Front Aadhaar detected':
            image_paths = [front_path, back_path]
        else:
            image_paths = [back_path, front_path]
    except Exception as e:
        print(f"[ERROR] Detection parsing failed: {e}")
        return []
    print(image_paths)
    # for img_idx in range(len(image_paths)):
    
    #     image_path = image_paths[img_idx]
    #     image = cv2.imread(image_path)
    for img_idx in range(len(image_paths)):

        image_path = image_paths[img_idx]

        # ✅ FIX 1: handle None path
        if not image_path:
            print(f"[WARNING] Skipping None image_path at index {img_idx}")
            continue

        image = cv2.imread(image_path)

        # ✅ FIX 2: handle failed read
        if image is None:
            print(f"[WARNING] Failed to read image: {image_path}")
            continue
    
        detections = result["results"][img_idx].get("detections", [])
        for det in detections:
        # for det in result["results"][img_idx]["detections"]:
            
            if det["class"] == "aadhaar_no":

                x1, y1, x2, y2 = det["bbox"]

                # 🔥 small padding improves OCR
                pad = 5
                x1 = max(0, x1 - pad)
                y1 = max(0, y1 - pad)
                x2 = min(image.shape[1], x2 + pad)
                y2 = min(image.shape[0], y2 + pad)

                crop = image[y1:y2, x1:x2]

                text = run_crop_ocr(ocr_model, crop)

                extracted_numbers.append({
                    "image": image_path,
                    "bbox": [x1, y1, x2, y2],
                    "raw_text": text
                })

    return extracted_numbers

import re

def clean_aadhaar(text):
    text = re.sub(r'\D', '', text)  # keep only digits

    # Aadhaar = 12 digits
    if len(text) >= 12:
        return text[:12]

    return text

def select_final_aadhaar(aadhaar_list):
    if not aadhaar_list:
        return None

    # choose most frequent
    most_common = Counter(aadhaar_list).most_common(1)[0][0]
    return most_common


def get_aadhaar_number(detection_result, front_path, back_path):
    aadhaar_data = extract_aadhaar_numbers(detection_result, front_path, back_path)
    aadhaar_list = []

    for item in aadhaar_data:
        clean_number = clean_aadhaar(item["raw_text"])

        print("\nImage:", item["image"])
        print("BBox :", item["bbox"])
        print("Raw  :", item["raw_text"])
        print("Clean:", clean_number)

        # ✅ collect valid candidates
        if len(clean_number) == 12:
            aadhaar_list.append(clean_number)

    final_aadhaar = select_final_aadhaar(aadhaar_list)
    return final_aadhaar
