#!/usr/bin/env python3
"""
Production server for ArcSpatialDB using Waitress
This is the recommended way to run the application on a VM
"""

from waitress import serve
from app import app
import os
import sys

def main():
    """Run the production server"""
    
    # Get configuration
    try:
        from config import FLASK_HOST, FLASK_PORT
        host = FLASK_HOST
        port = FLASK_PORT
    except ImportError:
        # Fallback configuration
        host = "0.0.0.0"  # Allow external connections
        port = 5000
    
    print("🚀 Starting ArcSpatialDB Production Server")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🌐 URL: http://{host}:{port}")
    print("=" * 50)
    
    # Start the production server
    serve(app, host=host, port=port, threads=4)

if __name__ == '__main__':
    main() 