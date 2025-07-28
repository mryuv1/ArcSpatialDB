# main.py
from app import app

if __name__ == '__main__':
    try:
        from config import FLASK_HOST, FLASK_DEBUG
        app.run(host=FLASK_HOST, port=5002, debug=FLASK_DEBUG)
    except ImportError:
        # Fallback if config file doesn't exist
        app.run(host='0.0.0.0', port=5002, debug=False) 