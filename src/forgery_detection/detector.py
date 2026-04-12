import cv2
import torch
import numpy as np
import torch.nn.functional as F
from pipeline import load_forgery_model
from config import settings
from ultralytics import YOLO

# # -------------------------------
# # PREDICT IMAGE (STABLE VERSION)
# # -------------------------------
# def predict_image(
#     image_path,
#     patch_size=128,
#     stride=64
# ):
    
#     model,device = load_forgery_model.load_model()

#     # Load noiseprint (grayscale)
#     noiseprint = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
#     noiseprint = noiseprint.astype(np.float32) / 127.5 - 1.0

#     # Pad if image is smaller than patch
#     H, W = noiseprint.shape
#     if H < patch_size or W < patch_size:
#         noiseprint = np.pad(
#             noiseprint,
#             ((0, max(0, patch_size - H)),
#              (0, max(0, patch_size - W))),
#             mode="reflect"
#         )

#     fake_probs = []

#     with torch.no_grad():
#         for i in range(0, noiseprint.shape[0] - patch_size + 1, stride):
#             for j in range(0, noiseprint.shape[1] - patch_size + 1, stride):

#                 patch = noiseprint[i:i+patch_size, j:j+patch_size]
#                 patch = torch.from_numpy(patch)\
#                              .unsqueeze(0)\
#                              .unsqueeze(0)\
#                              .to(device)

#                 logits = model(patch)
#                 prob = F.softmax(logits, dim=1)
#                 fake_probs.append(prob[:, 1].item())

#     # Aggregate
#     final_fake_prob = float(np.mean(fake_probs))
#     prediction = "fake" if final_fake_prob >= 0.5 else "real"

#     return {
#         "prediction": prediction,
#         "fake_probability": round(final_fake_prob, 4),
#         "num_patches": len(fake_probs)
#     }


def predict_image(img_path):
    model = YOLO(settings.SPLICING_REGION_DETECTION_PATH)
    results = model(img_path, conf=0.25, verbose=False)

    r = results[0]
    
    if r.boxes is not None and len(r.boxes) > 0:
        return 1,results   # forged
    else:
        return 0,results   # real