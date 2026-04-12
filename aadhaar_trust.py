import os
from models.architectures.cnn_model import forgery_cnn_transforms
from forgery_detection import predict_image
from noiseprint_creation import noise_creation
from models.architectures.cnn_model import cnn_model

img_path="C:\\Users\\dhruv\\OneDrive\\Desktop\\Aadhaar_Detection\\Aadhaar_Trust\\Image_Folder"
output_dir = noise_creation(img_path)
transform = forgery_cnn_transforms()
model = cnn_model()
results = []

for filename in os.listdir(output_dir):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        img_path = os.path.join(output_dir, filename)
        label, score = predict_image(image_path=img_path, model=model, transform=transform)
        results.append((filename, label, round(score, 4)))

# Display
for fname, label, prob in results:
    print(f"{fname}: Predicted as {label} (Confidence: {prob})")
