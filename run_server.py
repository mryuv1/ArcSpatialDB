#!/usr/bin/env python3
"""
Smart server runner for ArcSpatialDB
Automatically chooses the best available server
"""

import sys
import os

def check_waitress():
    """Check if Waitress is available"""
    try:
        import waitress
        return True
    except ImportError:
        return False

def check_gunicorn():
    """Check if Gunicorn is available"""
    try:
        import gunicorn
        return True
    except ImportError:
        return False

def run_waitress():
    """Run with Waitress"""
    from waitress import serve
    from app import app
    
    try:
        from config import FLASK_HOST, FLASK_PORT
        host = FLASK_HOST
        port = FLASK_PORT
    except ImportError:
        host = "0.0.0.0"
        port = 5000
    
    print("🚀 Starting ArcSpatialDB with Waitress (Production)")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🌐 URL: http://{host}:{port}")
    print("=" * 50)
    
    serve(app, host=host, port=port, threads=4)

def run_gunicorn():
    """Run with Gunicorn"""
    import subprocess
    
    print("🚀 Starting ArcSpatialDB with Gunicorn (Production)")
    print("📍 Host: 0.0.0.0")
    print("🔌 Port: 5000")
    print("🌐 URL: http://0.0.0.0:5000")
    print("=" * 50)
    
    subprocess.run([
        sys.executable, "-m", "gunicorn", 
        "-w", "4", 
        "-b", "0.0.0.0:5000", 
        "app:app"
    ])

def run_development():
    """Run with Flask development server"""
    from app import app
    
    try:
        from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
        host = FLASK_HOST
        port = FLASK_PORT
        debug = FLASK_DEBUG
    except ImportError:
        host = "0.0.0.0"
        port = 5000
        debug = False
    
    print("🚀 Starting ArcSpatialDB with Flask (Development)")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🌐 URL: http://{host}:{port}")
    print("⚠️  WARNING: This is a development server, not suitable for production!")
    print("=" * 50)
    
    app.run(host=host, port=port, debug=debug)

def main():
    """Choose and run the best available server"""
    
    print("🔍 Checking available servers...")
    
    if check_waitress():
        print("✅ Waitress found - using production server")
        run_waitress()
    elif check_gunicorn():
        print("✅ Gunicorn found - using production server")
        run_gunicorn()
    else:
        print("⚠️  No production server found - using development server")
        print("💡 Install Waitress: pip install waitress")
        print("💡 Or install Gunicorn: pip install gunicorn")
        run_development()

if __name__ == '__main__':
    main() 