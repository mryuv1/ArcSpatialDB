# ArcSpatialDB Requirements Files

This document explains the different requirements files in the ArcSpatialDB project and their purposes.

## Requirements Files Overview

### 1. **`requirements.txt`** - Main Requirements File
**Purpose**: Core dependencies for production deployment
**Usage**: `pip install -r requirements.txt`

**Contains**:
- Flask (Web framework)
- SQLAlchemy (Database ORM)
- requests (HTTP client)
- glob2 (File pattern matching)
- gunicorn (Production WSGI server)
- Flask-CORS (Cross-origin resource sharing)
- python-docx (Word document processing)
- waitress (Alternative WSGI server for Windows)

### 2. **`requirements_production.txt`** - Production Requirements
**Purpose**: Minimal requirements for production deployment
**Usage**: `pip install -r requirements_production.txt`

**Contains**: Same as main requirements.txt but with clear production focus

### 3. **`requirements_dev.txt`** - Development Requirements
**Purpose**: Additional tools for development and testing
**Usage**: `pip install -r requirements_dev.txt`

**Contains**:
- All core dependencies (from requirements.txt)
- pytest (Testing framework)
- flake8 (Code linting)
- black (Code formatting)
- python-dotenv (Environment management)
- Sphinx (Documentation)
- ipdb (Debugging)

### 4. **`requirements_complete.txt`** - Complete Requirements
**Purpose**: Comprehensive list of all dependencies with explanations
**Usage**: Reference only (not for direct installation)

**Contains**:
- All production dependencies
- Development dependencies
- Comments explaining each library's purpose
- List of built-in Python modules used

## Installation Instructions

### For Production Deployment:
```bash
pip install -r requirements.txt
```

### For Development:
```bash
pip install -r requirements_dev.txt
```

### For Minimal Production Setup:
```bash
pip install -r requirements_production.txt
```

## Library Usage in Project

### Core Libraries:
- **Flask**: Main web framework for the application
- **SQLAlchemy**: Database ORM for managing the SQLite database
- **requests**: HTTP client for API calls and testing
- **glob2**: File pattern matching for finding project files
- **python-docx**: Word document processing for code collection feature

### Production Servers:
- **gunicorn**: Primary WSGI server for Linux/Unix production
- **waitress**: Alternative WSGI server for Windows production

### Backend API:
- **Flask-CORS**: Enables cross-origin requests for the backend API

## Built-in Python Modules Used

The following Python standard library modules are used throughout the project:
- `os` - Operating system interface
- `sys` - System-specific parameters
- `json` - JSON data processing
- `uuid` - UUID generation
- `datetime` - Date and time handling
- `re` - Regular expressions
- `tempfile` - Temporary file creation
- `shutil` - High-level file operations
- `platform` - Platform identification
- `getpass` - Password input
- `socket` - Network interface
- `subprocess` - Subprocess management
- `urllib` - URL handling
- `sqlite3` - SQLite database interface

## Version Compatibility

All requirements files are tested with:
- **Python**: 3.10+ (recommended: 3.11)
- **Operating System**: Windows, Linux, macOS
- **Database**: SQLite (built-in)

## Docker Integration

The requirements are compatible with the Docker setup:
- `Dockerfile` uses `requirements.txt`
- `docker-compose.yml` mounts the requirements file
- All dependencies are installed in the container

## Node.js Dependencies

For the Node.js backend (in `backend_node/`):
```bash
cd backend_node
npm install
```

**Key Node.js dependencies**:
- express (Web framework)
- cors (Cross-origin resource sharing)
- sqlite3 (SQLite database)
- glob (File pattern matching)
- multer (File upload handling)

## Troubleshooting

### Common Issues:

1. **Version Conflicts**: Use virtual environments
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Missing Dependencies**: Ensure all files are installed
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_dev.txt  # For development
   ```

3. **Platform-Specific Issues**: Use appropriate WSGI server
   - Linux/Unix: Use `gunicorn`
   - Windows: Use `waitress`

### Verification:
```bash
# Test installation
python -c "import flask, sqlalchemy, requests, glob2; print('All core dependencies installed successfully!')"
```

## Updates and Maintenance

To update dependencies:
1. Update version numbers in requirements files
2. Test with `pip install -r requirements.txt`
3. Run tests to ensure compatibility
4. Update Docker images if needed

## Security Notes

- All dependencies are pinned to specific versions for security
- Regular updates recommended for security patches
- Production deployments should use the minimal requirements file
- Development tools should not be installed in production 