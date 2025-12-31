#!/usr/bin/env python3
"""
Startup script for Render deployment
Handles port binding and error checking
"""
import os
import sys

def main():
    """Start the FastAPI application"""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting Strategic Intelligence Assistant API...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    
    try:
        import uvicorn
        from main import app
        
        print("Application loaded successfully")
        print("Starting server...")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

