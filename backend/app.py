from flask import Flask, jsonify
from flask_cors import CORS
from api.projects import projects_bp
from api.areas import areas_bp
from api.files import files_bp
from sqlalchemy import Table, MetaData, create_engine
import os

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'elements.db')
DATABASE_URL = f'sqlite:///{DB_PATH}'
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# OLD VERSION (with autoload=True) - keeping for reference
# projects_table = Table('projects', metadata, autoload=True, autoload_with=engine)
# areas_table = Table('areas', metadata, autoload=True, autoload_with=engine)

# Current version (without autoload=True)
projects_table = Table('projects', metadata, autoload_with=engine)
areas_table = Table('areas', metadata, autoload_with=engine)

def create_app():
    app = Flask(__name__)
    
    # Enable CORS for all domains on all routes
    CORS(app, origins=["*"])
    
    # Register blueprints
    app.register_blueprint(projects_bp, url_prefix='/api')
    app.register_blueprint(areas_bp, url_prefix='/api')
    app.register_blueprint(files_bp)
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Backend API is running'})
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    try:
        # Try to import config values
        import sys
        sys.path.append('..')
        from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
    except ImportError:
        # Fallback if config file doesn't exist
        app.run(host='0.0.0.0', port=5000, debug=True)
