#!/usr/bin/env python
"""
Simple test script to run the backend Flask application
"""
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    app = create_app()
    print("🚀 Starting ArcSpatialDB Backend API...")
    print("📡 Server will be available at: http://localhost:5000")
    print("📚 API endpoints available at: http://localhost:5000/api/")
    print("💊 Health check: http://localhost:5000/api/health")
    print("🛑 Press Ctrl+C to stop the server")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install Flask Flask-CORS SQLAlchemy glob2")
except Exception as e:
    print(f"❌ Error starting server: {e}")
    sys.exit(1)
