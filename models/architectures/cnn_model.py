import torch
from torch import nn
from torchvision import transforms

class RealFakeCNN(nn.Module):
    def __init__(self):
        super(RealFakeCNN, self).__init__()
        self.model = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),

            nn.Flatten(),
            nn.Linear(128 * 16 * 16, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)
    
def cnn_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.jit.load("C:\\Users\\dhruv\\OneDrive\\Desktop\\Aadhaar_Detection\\detection_model.pt", map_location=device)
    return model

def forgery_cnn_transforms():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    transform = transforms.Compose([
    transforms.Resize((572, 572)),   # or your training transform
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
    ])
    return transform
