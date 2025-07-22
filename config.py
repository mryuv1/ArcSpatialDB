# Configuration file for ArcSpatialDB
# Update these values according to your deployment environment

# API Configuration
API_BASE_URL = "http://localhost:5000"  # Local Flask app
API_TIMEOUT = 30  # Timeout in seconds for API requests

# Database Configuration (for local fallback)
LOCAL_DATABASE_PATH = "elements.db"

# Flask App Configuration
FLASK_HOST = "0.0.0.0"  # Allow external connections
FLASK_PORT = 5000
FLASK_DEBUG = False  # Set to False in production

# File Upload Configuration
UPLOAD_FOLDER = "sampleDataset"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size 