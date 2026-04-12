import torch
from models.architectures.ForgeryDetectionCNN import ForgeryDetectionCNN
from config import settings

# -------------------------------
# LOAD MODEL
# -------------------------------
def load_model():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = ForgeryDetectionCNN(dropout=0.5).to(device)
    checkpoint = torch.load(settings.FORGERY_MODEL_PATH, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model,device