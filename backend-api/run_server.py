#!/usr/bin/env python3
"""
Simple script to run the FastAPI server
Usage: python run_server.py
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting AadhaarTrust Backend API Server")
    print("=" * 60)
    print("\nServer will be available at:")
    print("  • API: http://localhost:8000")
    print("  • API Docs: http://localhost:8000/docs")
    print("  • Alternative: http://127.0.0.1:8000")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Listen on all interfaces
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
