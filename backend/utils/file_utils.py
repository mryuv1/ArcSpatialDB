import os
import glob2
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def get_project_files(file_location):
    """Get all files (PDF, JPEG, PNG) for a project and return file information"""
    abs_path = os.path.abspath(file_location)
    file_types = [('pdf', 'pdf'), ('jpeg', 'img'), ('jpg', 'img'), ('png', 'img')]
    all_files = []
    most_recent = None

    for ext, ftype in file_types:
        pattern = os.path.join(abs_path, f"*.{ext}")
        files = glob2.glob(pattern)
        for f in files:
            ctime = os.path.getctime(f)
            file_info = {
                'path': f,
                'type': ftype,
                'ctime': ctime,
                'filename': os.path.basename(f),
                'rel_path': os.path.relpath(f, PROJECT_ROOT)
            }
            all_files.append(file_info)

            if (most_recent is None) or (ctime > most_recent['ctime']):
                most_recent = file_info

    # Sort files by creation time (newest first)
    all_files.sort(key=lambda x: x['ctime'], reverse=True)
    
    return {
        'all_files': all_files,
        'file_count': len(all_files),
        'most_recent': most_recent
    }
