from flask import Blueprint, send_file
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

files_bp = Blueprint('files', __name__)

@files_bp.route('/view_file/<path:rel_path>')
def view_file(rel_path):
    """Serve project files for viewing"""
    try:
        abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, rel_path))
        
        # Security: Only allow files inside project directory
        if not abs_path.startswith(PROJECT_ROOT):
            return {'error': 'Access denied'}, 403
        
        if not os.path.exists(abs_path):
            return {'error': 'File not found'}, 404
            
        return send_file(abs_path)
    except Exception as e:
        return {'error': str(e)}, 500
