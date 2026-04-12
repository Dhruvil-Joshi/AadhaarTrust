from src.forgery_detection import detector
from src.noiseprint_creation.noise_creation import generate_noiseprint
from src.forgery_detection.detector import predict_image
from src.forgery_detection.localization import locate_forgery
from src.qr_decrpytion.qr_decoder import qr_decoder
from config import settings
import os
def aadhaar_trust():
    # Generate noiseprint
    filename_noiseprint, filename_original = generate_noiseprint(settings.INPUT_DIR)

    # Predict fake or not
    pred, results = predict_image(filename_noiseprint)

    r = results[0]

    print("\n================ FINAL PREDICTION ================\n")
    print("Document Title : ",str(filename_original).split('\\')[-1],"\n")
    if pred == 1:
        print("🚨 FORGERY DETECTED!")
        print(f"🧱 Number of suspicious regions: {len(r.boxes)}")

        for i, box in enumerate(r.boxes):
            print(f"\nRegion {i+1}:")
            print(f"  ➤ Class       : {int(box.cls)}")
            print(f"  ➤ Confidence  : {float(box.conf):.4f}")
            # print(f"  ➤ BBox (xyxy) : {box.xyxy.tolist()}")

        forgery_report = locate_forgery(filename_original,filename_noiseprint)
        print(forgery_report)

    else:
        print("✅ NO FORGERY DETECTED")
        print("The document appears authentic.")
        filename= os.listdir(settings.INPUT_DIR)[0]  # Returns 'file.txt'
        image_path = os.path.join(settings.INPUT_DIR,filename)

        result=qr_decoder(image_path)
        print(result)

    