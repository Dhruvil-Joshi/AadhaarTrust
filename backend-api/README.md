# AadhaarTrust Backend API

FastAPI backend for Aadhaar card authentication and forgery detection.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment variables:**
   Create a `.env` file (optional, defaults are used):
   ```env
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

3. **Run the server:**
   
   **Option 1: Use the run script (Recommended)**
   ```bash
   python run_server.py
   # OR on Windows: run_server.bat
   # OR on Linux/macOS: chmod +x run_server.sh && ./run_server.sh
   ```
   
   **Option 2: Run directly**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   **Access the API:**
   - ✅ API: `http://localhost:8000` or `http://127.0.0.1:8000`
   - ✅ API Docs: `http://localhost:8000/docs`
   - ❌ **DO NOT** use `http://0.0.0.0:8000` - that's only for server binding!

## API Endpoints

### Upload
- **POST** `/api/v1/upload` - Upload Aadhaar image for validation

### Status
- **GET** `/api/v1/status/{job_id}` - Get validation job status

### Results
- **GET** `/api/v1/results/{job_id}` - Get validation results

### Download
- **GET** `/api/v1/download/{job_id}/{file_type}` - Download reports and files
  - `report.pdf` - PDF validation report
  - `report.html` - HTML validation report
  - `data.json` - JSON data export
  - `splicing_map.png` - Forgery localization map (if forged)

### Manual Review
- **GET** `/api/v1/manual-review` - Get pending manual reviews
- **POST** `/api/v1/manual-review/{job_id}` - Submit manual review decision

### Health
- **GET** `/api/v1/health` - Health check

## Project Structure

```
backend-api/
├── app/
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── services/            # Business logic
│   ├── models/              # Pydantic models
│   └── core/                # Configuration
├── requirements.txt
└── README.md
```

## Integration

This backend integrates with the existing Python pipeline:
- `pipeline/pipeline.py` - Main validation pipeline
- `src/forgery_detection/` - Forgery detection modules
- `src/qr_decrpytion/` - QR code decoding
- `src/noiseprint_creation/` - Noiseprint generation

## Notes

- Temporary files are stored in `data/temp/` and auto-cleaned after 1 hour
- Job status is stored in-memory (use Redis for production)
- OCR extraction is currently a placeholder (integrate DocTR/Tesseract)
