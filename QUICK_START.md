# 🚀 Quick Start Guide

## Prerequisites

- Python 3.8+ installed
- Node.js 18+ and npm installed
- Your existing Aadhaar validation models in place

## Step 1: Backend Setup (5 minutes)

```bash
# Navigate to backend
cd backend-api

# Install Python dependencies
pip install -r requirements.txt

# Make sure your existing Python modules are accessible
# The backend imports from your existing src/ directory

# Option 1: Use the run script (Easiest)
python run_server.py
# OR on Windows: run_server.bat
# OR on Linux/macOS: ./run_server.sh

# Option 2: Run directly with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**IMPORTANT:** After starting the server, access it at:
- ✅ **API:** `http://localhost:8000` or `http://127.0.0.1:8000`
- ✅ **API docs (Swagger):** `http://localhost:8000/docs`
- ❌ **DO NOT** use `http://0.0.0.0:8000` - that's only for server binding, not browser access!

## Step 2: Frontend Setup (3 minutes)

```bash
# Open a new terminal
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at: `http://localhost:5173`

## Step 3: Test the Application

1. Open `http://localhost:5173` in your browser
2. Click "Start Verification"
3. Upload an Aadhaar image (JPEG, PNG, TIFF, or BMP)
4. Watch the real-time progress
5. View the results

## Troubleshooting

### Backend Issues

**"This site can't be reached" or ERR_ADDRESS_INVALID:**
- ❌ **Wrong:** `http://0.0.0.0:8000` (this won't work!)
- ✅ **Correct:** `http://localhost:8000` or `http://127.0.0.1:8000`
- The `0.0.0.0` address is only for the server to listen on all interfaces
- You must use `localhost` or `127.0.0.1` in your browser

**Import errors:**
- Make sure you're running from the project root
- Check that `src/`, `config/`, and `pipeline/` directories are accessible
- Verify model paths in `config/settings.py`

**Port already in use:**
- Change port: `uvicorn app.main:app --port 8001`
- Then access at: `http://localhost:8001`

### Frontend Issues

**API connection errors:**
- Check that backend is running on port 8000
- Verify CORS settings in `backend-api/app/core/config.py`
- Check browser console for errors

**Build errors:**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again

## Next Steps

1. **Test with real images** - Upload genuine and forged Aadhaar cards
2. **Integrate OCR** - Update `extract_ocr_data()` in `pipeline_service.py`
3. **Add report generation** - Implement PDF/HTML report creation
4. **Customize UI** - Adjust colors, fonts, layouts in Tailwind config

## Need Help?

- Check `PROJECT_SUMMARY.md` for detailed documentation
- Review `backend-api/README.md` and `frontend/README.md`
- Check API docs at `http://localhost:8000/docs`

Happy coding! 🎉
