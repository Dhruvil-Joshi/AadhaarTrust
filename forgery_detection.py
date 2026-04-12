from PIL import Image
import torch

def predict_image(image_path, model, transform):
    model.eval()
    class_names = ['fake','real']
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0)  # Add batch dimension
    image = image.to(next(model.parameters()).device)  # Send to same device

    with torch.no_grad():
        output = model(image)  # shape: [1,1]
        prob = output.item()   # probability from sigmoid

    # Decide class
    predicted_class = 1 if prob >= 0.5 else 0  # threshold at 0.5
    return class_names[predicted_class], prob
