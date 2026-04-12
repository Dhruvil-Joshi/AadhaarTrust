# Installation Guide

## Complete Installation

### Option 1: Install All Dependencies (Recommended)

```bash
# Install all required dependencies
pip install -r requirements.txt
```

This includes:
- Backend API dependencies (FastAPI, etc.)
- Existing pipeline dependencies (OpenCV, PyTorch, etc.)
- All core libraries

### Option 2: Install Separately

#### Backend API Only
```bash
cd backend-api
pip install -r requirements.txt
```

**Note:** The backend also needs the existing pipeline dependencies. Install them from the root directory:
```bash
pip install opencv-python pillow torch torchvision ultralytics zxing-cpp numpy scipy matplotlib rawpy
```

#### Development Dependencies (Optional)
```bash
pip install -r requirements-dev.txt
```

#### Optional Features
```bash
# For OCR integration
pip install -r requirements-optional.txt

# Or install specific packages:
pip install python-doctr[torch]  # For OCR
pip install reportlab weasyprint  # For PDF reports
```

## System Requirements

### Python Version
- **Python 3.8+** (Python 3.10+ recommended)

### Operating System
- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS 10.15+

### Hardware Recommendations
- **CPU:** Multi-core processor (4+ cores recommended)
- **RAM:** 8GB minimum, 16GB+ recommended
- **GPU:** Optional but recommended for faster inference (CUDA-compatible)
- **Storage:** 10GB+ free space for models and dependencies

## Installation Steps

### 1. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
# Test FastAPI
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"

# Test PyTorch
python -c "import torch; print('PyTorch:', torch.__version__)"

# Test OpenCV
python -c "import cv2; print('OpenCV:', cv2.__version__)"

# Test Ultralytics
python -c "import ultralytics; print('Ultralytics:', ultralytics.__version__)"
```

## Troubleshooting

### Common Issues

#### 1. PyTorch Installation Issues
```bash
# For CPU-only (if GPU not available)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

#### 2. OpenCV Installation Issues
```bash
# If opencv-python fails, try:
pip install opencv-contrib-python
```

#### 3. zxing-cpp Installation Issues
```bash
# On Windows, you may need Visual C++ Build Tools
# On Linux:
sudo apt-get install build-essential
sudo apt-get install cmake

# On macOS:
brew install cmake
```

#### 4. Ultralytics Installation Issues
```bash
# Make sure you have the latest pip
pip install --upgrade pip setuptools wheel
pip install ultralytics
```

### Version Conflicts

If you encounter version conflicts:

1. **Create a fresh virtual environment:**
   ```bash
   python -m venv venv_new
   venv_new\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Install specific versions:**
   Check the error message and install compatible versions manually.

## GPU Setup (Optional)

### CUDA Installation

1. **Check CUDA version:**
   ```bash
   nvidia-smi
   ```

2. **Install PyTorch with CUDA:**
   ```bash
   # Visit https://pytorch.org/get-started/locally/
   # Select your CUDA version and install accordingly
   ```

3. **Verify GPU:**
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.cuda.get_device_name(0))
   ```

## Next Steps

After installation:

1. **Verify model paths** in `config/settings.py`
2. **Test the backend:**
   ```bash
   cd backend-api
   uvicorn app.main:app --reload
   ```
3. **Test the frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Getting Help

- Check `QUICK_START.md` for quick setup
- Review `PROJECT_SUMMARY.md` for project overview
- Check individual README files in `backend-api/` and `frontend/`
