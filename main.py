# main.py
from app import app

if __name__ == '__main__':
    try:
        from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
    except ImportError:
        # Fallback if config file doesn't exist
        app.run(host='0.0.0.0', port=5000, debug=True) 