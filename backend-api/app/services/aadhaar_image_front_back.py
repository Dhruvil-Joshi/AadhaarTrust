from ultralytics import YOLO
import json
import os
from config import settings
# -------------------------------
# Load YOLO model once (GLOBAL)
# -------------------------------
MODEL_PATH = settings.AADHAAR_MAIN_PIPELINE_PATH
model = YOLO(MODEL_PATH)

# -------------------------------
# Aadhaar Detection Class
# -------------------------------
class AadhaarDetector:

    def __init__(self):

        self.identity_fields = {
            "aadhaar_holder_name",
            "aadhaar_dob",
            "aadhaar_gender",
            "aadhaar_photo",
            "aadhaar_no",
            "aadhaar_no_mask",
            "aadhaar_no_already_masked"
        }

    # -------------------------------
    # YOLO Detection (STRUCTURED)
    # -------------------------------
    def run_yolo(self, image_path):

        results = model(image_path, conf=0.25)

        detections = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])

                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])

                detections.append({
                    "class": model.names[cls_id],
                    "confidence": round(conf, 3),
                    "bbox": [x1, y1, x2, y2]
                })

        return detections

    # -------------------------------
    # Single Image Check
    # -------------------------------
    def detect_single(self, image_path):

        detections = self.run_yolo(image_path)
        classes = set(d["class"] for d in detections)

        # Front Aadhaar
        if "emblem" in classes and "gov_logo" in classes:

            identity_count = len(classes.intersection(self.identity_fields))

            if identity_count >= 2:
                return True, "Front Aadhaar detected", classes, detections

            if "aadhaar_address" in classes:
                return True, "Back Aadhaar detected", classes, detections

        # PDF Aadhaar
        if "aadhaar_logo" in classes:
            if "aadhaar_holder_name" in classes or "aadhaar_photo" in classes:
                return True, "PDF Aadhaar detected", classes, detections

        return False, "Not Aadhaar", classes, detections

    # -------------------------------
    # Main Detection Function
    # -------------------------------
    def detect(self, image1_path, image2_path=None):
        front_detected = False
        front_image_path = None

        back_detected = False
        back_image_path = None

        valid1, reason1, classes1, detections1 = self.detect_single(image1_path)
        image1_json = {
            "image": image1_path,
            "aadhaar_valid": valid1,
            "reason": reason1,
            "classes": list(classes1),
            "detections": detections1
        }
        if reason1 == "Front Aadhaar detected":
            front_detected = True
            front_image_path = image1_path
        
        elif not back_detected and reason1 == "Back Aadhaar detected":
            back_detected = True
            back_image_path = image1_path
        
        # -------- Single Image --------
        if image2_path is None:
            return {
                "aadhaar_detected": valid1,
                "results": [image1_json],
                "front_detected": front_detected,
                "back_detected": back_detected,
                "front_image_path": front_image_path,
                "back_image_path": back_image_path
            }  

        # -------- Two Images --------
        valid2, reason2, classes2, detections2 = self.detect_single(image2_path)

        image2_json = {
            "image": image2_path,
            "aadhaar_valid": valid2,
            "reason": reason2,
            "classes": list(classes2),
            "detections": detections2
        }

        if not front_detected and reason2 == "Front Aadhaar detected":
            front_detected = True
            front_image_path = image2_path

        elif not back_detected and reason2 == "Back Aadhaar detected":
            back_detected = True
            back_image_path = image2_path

        return {
            "aadhaar_detected": valid1 or valid2,
            "results": [image1_json, image2_json],
            "front_detected": front_detected,
            "back_detected": back_detected,
            "front_image_path": front_image_path,
            "back_image_path": back_image_path
        }  



# -------------------------------
# Display Function (Optional)
# -------------------------------
def display_result(result):

    print("\n================ Aadhaar Verification Report ================\n")

    print(f"Aadhaar Detected : {result['aadhaar_detected']}")
    for idx, res in enumerate(result["results"], start=1):

        print(f"\nImage {idx}")
        print("---------------------------")
        print(f"Path           : {res['image']}")
        print(f"Valid Aadhaar  : {res['aadhaar_valid']}")
        print(f"Reason         : {res['reason']}")

        print("\nDetected Classes:")
        for cls in res["classes"]:
            print(f"  - {cls}")

        print("\nDetections (with bbox):")
        for d in res["detections"]:
            print(f"  - {d['class']} | Conf: {d['confidence']} | Box: {d['bbox']}")

    print("\n==============================================================\n")


# -------------------------------
# SAVE JSON (IMPORTANT)
# -------------------------------
def save_result(result, output_path="aadhaar_detection.json"):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    print(f"✅ JSON saved at: {output_path}")


