#!/bin/bash
# Linux/macOS script to run the FastAPI server

echo "============================================================"
echo "Starting AadhaarTrust Backend API Server"
echo "============================================================"
echo ""
echo "Server will be available at:"
echo "  • API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Alternative: http://127.0.0.1:8000"
echo ""
echo "Press CTRL+C to stop the server"
echo "============================================================"
echo ""

python3 run_server.py
