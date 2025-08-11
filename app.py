from flask import Flask, render_template, request, url_for, send_file, redirect, jsonify
from sqlalchemy import create_engine, MetaData, Table, and_, select, distinct, func, or_, Column, String, Float, Integer, ForeignKey
import os
import glob2
from datetime import datetime
import shutil
import uuid
import math

# Add pyproj for coordinate transformations
try:
    from pyproj import Transformer, CRS
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    print("⚠️  pyproj not available. Coordinate transformation will be disabled.")
    print("   Install with: pip install pyproj")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def safe_relpath(path, start=None):
    """
    Safely calculate relative path, handling cross-drive issues on Windows.
    If paths are on different drives, return a special marker for absolute paths.
    """
    try:
        if start is None:
            start = os.path.abspath('.')
        return os.path.relpath(path, start)
    except ValueError:
        # Cross-drive issue, return the absolute path with a special prefix
        # This will be handled specially in the view_file route
        return f"ABS:{os.path.abspath(path)}"

def file_exists_check(file_path):
    """
    Check if a file exists and is accessible.
    Returns True if file exists and is readable, False otherwise.
    """
    try:
        return os.path.exists(file_path) and os.path.isfile(file_path) and os.access(file_path, os.R_OK)
    except Exception as e:
        print(f"Error checking file existence for {file_path}: {e}")
        return False

def parse_point(s):
    """
    Parse coordinate string and return UTM coordinates.
    Supports various formats and converts geographic coordinates to UTM Zone 36N.
    
    Supported formats:
    - WGS84 UTM 36N 723478 E / 3537402 N -> (723478, 3537402)
    - 723478/3537402 -> (723478, 3537402)  
    - 723478 E 3537402 N -> (723478, 3537402)
    - WGS84 Geo 35.342893 E / 31.926979 N -> converted to UTM
    - 35.342893 E / 31.926979 N -> converted to UTM
    - 35.342893 / 31.926979 -> converted to UTM
    
    Returns: (x_utm, y_utm) if successful, or (None, error_message) if failed
    """
    import re
    
    try:
        s = str(s).strip()
        if not s:
            return None, "Empty coordinate string provided"
        
        # Pattern 1: WGS84 UTM format - extract numbers directly
        utm_match = re.search(r'WGS84\s+UTM\s+\d+[NS]\s+(\d+(?:\.\d+)?)\s*[EW]\s*/\s*(\d+(?:\.\d+)?)\s*[NS]', s, re.IGNORECASE)
        if utm_match:
            x = float(utm_match.group(1))
            y = float(utm_match.group(2))
            return (int(round(x)), int(round(y))), None
        
        # Pattern 2: WGS84 Geo format - extract and convert
        geo_match = re.search(r'WGS84\s+GEO\s+([\d.]+)\s*([EW])\s*/\s*([\d.]+)\s*([NS])', s, re.IGNORECASE)
        if geo_match:
            lon = float(geo_match.group(1))
            lon_dir = geo_match.group(2).upper()
            lat = float(geo_match.group(3))
            lat_dir = geo_match.group(4).upper()
            
            # Apply direction
            if lon_dir == 'W':
                lon = -lon
            if lat_dir == 'S':
                lat = -lat
            
            # Convert to UTM
            x_utm, y_utm, _ = transform_to_utm(lon, lat, "EPSG:4326")
            return (int(round(x_utm)), int(round(y_utm))), None
        
        # Pattern 3: Simple coordinate with E/N directions (no slash)
        en_match = re.search(r'(\d+(?:\.\d+)?)\s*E\s+(\d+(?:\.\d+)?)\s*N', s, re.IGNORECASE)
        if en_match:
            x = float(en_match.group(1))
            y = float(en_match.group(2))
            
            # Check if these are UTM coordinates (large numbers)
            if x > 100000 and y > 100000:
                # Already UTM coordinates
                return (int(round(x)), int(round(y))), None
            else:
                # Geographic coordinates, convert to UTM
                x_utm, y_utm, _ = transform_to_utm(x, y, "EPSG:4326")
                return (int(round(x_utm)), int(round(y_utm))), None
        
        # Pattern 4: Geographic with E/W and N/S directions  
        geo_dir_match = re.search(r'([\d.]+)\s*([EW])\s*/\s*([\d.]+)\s*([NS])', s, re.IGNORECASE)
        if geo_dir_match:
            lon = float(geo_dir_match.group(1))
            lon_dir = geo_dir_match.group(2).upper()
            lat = float(geo_dir_match.group(3))
            lat_dir = geo_dir_match.group(4).upper()
            
            # Apply direction
            if lon_dir == 'W':
                lon = -lon
            if lat_dir == 'S':
                lat = -lat
            
            # Convert to UTM
            x_utm, y_utm, _ = transform_to_utm(lon, lat, "EPSG:4326")
            return (int(round(x_utm)), int(round(y_utm))), None
        
        # Pattern 5: Simple numeric coordinates with various separators
        # Try separators: /, ,, :, ;, |, \, tab, space
        coord_match = re.search(r'([\d.-]+)\s*[/,:;|\\\t\s]\s*([\d.-]+)', s)
        if coord_match:
            x = float(coord_match.group(1))
            y = float(coord_match.group(2))
            
            # Determine if coordinates are UTM or geographic based on magnitude
            if abs(x) > 180 or abs(y) > 90:
                # Likely UTM coordinates
                return (int(round(x)), int(round(y))), None
            else:
                # Likely geographic coordinates, convert to UTM
                x_utm, y_utm, _ = transform_to_utm(x, y, "EPSG:4326")
                return (int(round(x_utm)), int(round(y_utm))), None
        
        # If no pattern matched
        return None, f"Invalid coordinate format: '{s}'. Expected formats: '723478/3537402', '723478 E 3537402 N', 'WGS84 UTM 36N 723478 E / 3537402 N', '35.342893 E / 31.926979 N', '35.342893/31.926979'"
        
    except ValueError as e:
        return None, f"Invalid numeric values in '{s}': {str(e)}"
    except Exception as e:
        return None, f"Error parsing coordinates '{s}': {str(e)}"
    

def transform_to_utm(x, y, source_crs=None):
    """
    Transform coordinates to WGS84 UTM Zone 36N (EPSG:32636) format using pyproj.
    All coordinates are transformed to the same UTM zone for consistency.
    
    Args:
        x, y: Input coordinates
        source_crs: Source coordinate reference system (EPSG code or CRS string)
                   If None, assumes WGS84 Geographic (EPSG:4326)
    
    Returns:
        (x_utm, y_utm, utm_epsg) or (x, y, None) if transformation fails
    """
    if not PYPROJ_AVAILABLE:
        return x, y, None
    
    try:
        # Default to WGS84 Geographic if no source CRS provided
        if source_crs is None:
            source_crs = "EPSG:4326"
        
        # Create transformer from source to WGS84 Geographic
        transformer_to_wgs84 = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)
        
        # Transform to WGS84 Geographic
        lon, lat = transformer_to_wgs84.transform(x, y)
        
        # Always use WGS84 UTM Zone 36N (EPSG:32636) as the reference
        utm_epsg = 32636  # WGS84 UTM Zone 36N
        
        # Create transformer from WGS84 to UTM Zone 36N
        transformer_to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
        
        # Transform to UTM Zone 36N
        x_utm, y_utm = transformer_to_utm.transform(lon, lat)
        
        return x_utm, y_utm, utm_epsg
        
    except Exception as e:
        print(f"⚠️  Coordinate transformation failed: {e}")
        return x, y, None

def dms_to_decimal(degrees, minutes, seconds, direction):
    """
    Convert degrees, minutes, seconds to decimal degrees.
    
    Args:
        degrees, minutes, seconds: DMS values
        direction: 'N', 'S', 'E', 'W'
    
    Returns:
        Decimal degrees
    """
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    if direction in ['S', 'W']:
        decimal = -decimal
    
    return decimal

def row_to_dict(row):
    """
    Convert SQLAlchemy Row object to dictionary, handling different SQLAlchemy versions
    """
    try:
        if hasattr(row, '_mapping'):
            return dict(row._mapping)
        else:
            return dict(row)
    except (ValueError, TypeError):
        # Fallback for SQLAlchemy Row objects
        return {key: row[key] for key in row.keys()}

app = Flask(__name__)

# Custom filter for datetime formatting
@app.template_filter('datetime')
def datetime_filter(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

DATABASE_URL = 'sqlite:///elements.db'
engine = create_engine(DATABASE_URL)
metadata = MetaData()

def initialize_database():
    """
    Initialize the database with required tables if they don't exist.
    This function creates the tables if the database is empty or doesn't exist.
    """
    try:
        # Check if tables exist by trying to reflect them
        metadata.reflect(bind=engine)
        
        # If tables don't exist, create them
        if 'projects' not in metadata.tables or 'areas' not in metadata.tables:
            print("🔄 Database tables not found. Creating tables...")
            
            # Define the projects table
            projects_table = Table('projects', metadata,
                Column('uuid', String, primary_key=True),
                Column('project_name', String, nullable=False),
                Column('user_name', String, nullable=False),
                Column('date', String, nullable=False),
                Column('file_location', String, nullable=False),
                Column('paper_size', String, nullable=False),
                Column('description', String, nullable=True)
            )
            
            # Define the areas table
            areas_table = Table('areas', metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('project_id', String, ForeignKey('projects.uuid'), nullable=False),
                Column('xmin', Integer, nullable=False),
                Column('ymin', Integer, nullable=False),
                Column('xmax', Integer, nullable=False),
                Column('ymax', Integer, nullable=False),
                Column('scale', String, nullable=False)
            )
            
            # Create all tables
            metadata.create_all(engine)
            print("✅ Database tables created successfully!")
            
            return projects_table, areas_table
        else:
            print("✅ Database tables already exist.")
            # Return the existing tables
            return metadata.tables['projects'], metadata.tables['areas']
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        # Create tables from scratch if reflection fails
        print("🔄 Creating tables from scratch...")
        
        # Clear metadata and create tables
        metadata.clear()
        
        projects_table = Table('projects', metadata,
            Column('uuid', String, primary_key=True),
            Column('project_name', String, nullable=False),
            Column('user_name', String, nullable=False),
            Column('date', String, nullable=False),
            Column('file_location', String, nullable=False),
            Column('paper_size', String, nullable=False),
            Column('description', String, nullable=True)
        )
        
        areas_table = Table('areas', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('project_id', String, ForeignKey('projects.uuid'), nullable=False),
            Column('xmin', Float, nullable=False),
            Column('ymin', Float, nullable=False),
            Column('xmax', Float, nullable=False),
            Column('ymax', Float, nullable=False),
            Column('scale', String, nullable=False)
        )
        
        metadata.create_all(engine)
        print("✅ Database tables created successfully!")
        return projects_table, areas_table

# Initialize database and get table references
projects_table, areas_table = initialize_database()

def create_sample_data():
    """
    Create sample data if the database is empty.
    This function adds some example projects and areas for testing.
    """
    try:
        with engine.connect() as conn:
            # Check if there are any projects
            result = conn.execute(select(func.count()).select_from(projects_table)).scalar()
            
            if result == 0:
                print("📝 Database is empty. Creating sample data...")
                
                # Sample projects
                sample_projects = [
                    {
                        'uuid': 'sample001',
                        'project_name': 'Sample Project 1',
                        'user_name': 'Test User',
                        'date': '01-01-24',
                        'file_location': 'sampleDataset/sample1',
                        'paper_size': 'A1',
                        'description': 'Sample project for testing'
                    },
                    {
                        'uuid': 'sample002',
                        'project_name': 'Sample Project 2',
                        'user_name': 'Test User',
                        'date': '02-01-24',
                        'file_location': 'sampleDataset/sample2',
                        'paper_size': 'A2',
                        'description': 'Another sample project'
                    }
                ]
                
                # Sample areas
                sample_areas = [
                    {
                        'project_id': 'sample001',
                        'xmin': 732387,
                        'ymin': 3595538,
                        'xmax': 740294,
                        'ymax': 3601127,
                        'scale': '1:1000'
                    },
                    {
                        'project_id': 'sample002',
                        'xmin': 741000,
                        'ymin': 3600000,
                        'xmax': 742000,
                        'ymax': 3602000,
                        'scale': '1:2000'
                    }
                ]
                
                # Insert sample projects
                for project in sample_projects:
                    conn.execute(projects_table.insert().values(**project))
                
                # Insert sample areas
                for area in sample_areas:
                    conn.execute(areas_table.insert().values(**area))
                
                conn.commit()
                print("✅ Sample data created successfully!")
            else:
                print(f"📊 Database contains {result} projects. Skipping sample data creation.")
                
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

# Create sample data if database is empty
create_sample_data()


def calculate_area_size(xmin, ymin, xmax, ymax):
    """Calculate the area size in square meters using UTM coordinates"""
    width = abs(xmax - xmin)
    height = abs(ymax - ymin)
    return width * height

def calculate_overlap_percentage(area_xmin, area_ymin, area_xmax, area_ymax, query_xmin, query_ymin, query_xmax, query_ymax):
    """Calculate the percentage of area that overlaps with the query rectangle"""
    # Calculate intersection
    intersect_xmin = max(area_xmin, query_xmin)
    intersect_ymin = max(area_ymin, query_ymin)
    intersect_xmax = min(area_xmax, query_xmax)
    intersect_ymax = min(area_ymax, query_ymax)

    # Check if there's an intersection
    if intersect_xmin >= intersect_xmax or intersect_ymin >= intersect_ymax:
        return 0.0

    # Calculate areas
    area_size = (area_xmax - area_xmin) * (area_ymax - area_ymin)
    intersect_size = (intersect_xmax - intersect_xmin) * (intersect_ymax - intersect_ymin)

    if area_size == 0:
        return 0.0

    return (intersect_size / area_size) * 100.0

def generate_unique_uuid():
    """
    Generate a unique UUID that doesn't exist in the database.
    
    Returns:
        str: A unique UUID string
    """
    with engine.connect() as conn:
        while True:
            generated_uuid = str(uuid.uuid4())[:8]
            # Check if UUID already exists
            existing = conn.execute(
                select(projects_table.c.uuid).where(projects_table.c.uuid == generated_uuid)
            ).first()
            if not existing:
                return generated_uuid

@app.route('/api/add_project', methods=['POST'])
def api_add_project():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    required_fields = ['project_name', 'user_name', 'date', 'file_location', 'paper_size', 'description']
    missing_fields = [f for f in required_fields if f not in data]
    
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400
    
    try:
        # Generate a unique UUID using the reusable function
        generated_uuid = generate_unique_uuid()
        
        with engine.begin() as conn:
            # Insert project with generated UUID
            conn.execute(projects_table.insert().values(
                uuid=generated_uuid,
                project_name=data['project_name'],
                user_name=data['user_name'],
                date=data['date'],
                file_location=data['file_location'],
                paper_size=data['paper_size'],
                description=data['description']
            ))
            
            # Insert areas if provided
            if 'areas' in data and isinstance(data['areas'], list):
                for area_data in data['areas']:
                    area_required_fields = ['xmin', 'ymin', 'xmax', 'ymax', 'scale']
                    area_missing_fields = [f for f in area_required_fields if f not in area_data]
                    
                    if area_missing_fields:
                        return jsonify({"error": f"Missing area fields: {', '.join(area_missing_fields)}"}), 400
                    
                    # Convert scale to string format if it's a number
                    scale_value = area_data['scale']
                    if isinstance(scale_value, (int, float)):
                        scale_value = f"1:{int(scale_value)}"
                    
                    # Transform coordinates to UTM if they're not already
                    xmin, ymin, xmax, ymax = area_data['xmin'], area_data['ymin'], area_data['xmax'], area_data['ymax']
                    
                    # Check if coordinates are already in UTM format (large numbers)
                    # If they look like geographic coordinates (small numbers), transform them
                    if abs(xmin) < 180 and abs(ymin) < 90 and abs(xmax) < 180 and abs(ymax) < 90:
                        # Likely geographic coordinates, transform to UTM
                        xmin_utm, ymin_utm, utm_epsg = transform_to_utm(xmin, ymin)
                        xmax_utm, ymax_utm, _ = transform_to_utm(xmax, ymax)
                        xmin, ymin, xmax, ymax = xmin_utm, ymin_utm, xmax_utm, ymax_utm
                    
                    conn.execute(areas_table.insert().values(
                        project_id=generated_uuid,
                        xmin=xmin,
                        ymin=ymin,
                        xmax=xmax,
                        ymax=ymax,
                        scale=scale_value
                    ))
        
        return jsonify({"message": "Project added successfully", "uuid": generated_uuid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_new_uuid', methods=['POST'])
def api_get_new_uuid():
    """Generate a new unique UUID"""
    try:
        # Use the reusable UUID generation function
        generated_uuid = generate_unique_uuid()
        return jsonify({"uuid": generated_uuid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/db_manager.pyt')
def download_db_manager():
    """Download the db_manager.pyt file"""
    try:
        db_manager_path = os.path.join(PROJECT_ROOT, 'db_manager.pyt')
        if os.path.exists(db_manager_path):
            return send_file(
                db_manager_path,
                as_attachment=True,
                download_name='db_manager.pyt',
                mimetype='text/plain'
            )
        else:
            return jsonify({"error": "db_manager.pyt file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/project_gui.py')
def download_project_gui():
    """Download the project_gui.py file"""
    try:
        project_gui_path = os.path.join(PROJECT_ROOT, 'project_gui.py')
        if os.path.exists(project_gui_path):
            return send_file(
                project_gui_path,
                as_attachment=True,
                download_name='project_gui.py',
                mimetype='text/plain'
            )
        else:
            return jsonify({"error": "project_gui.py file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_project/<uuid>', methods=['GET'])
def api_get_project(uuid):
    try:
        with engine.connect() as conn:
            # Get project details
            project_result = conn.execute(
                select(projects_table).where(projects_table.c.uuid == uuid)
            ).first()
            
            if not project_result:
                return jsonify({"error": "Project not found"}), 404
            
            project_dict = row_to_dict(project_result)
            
            # Get associated areas
            areas_result = conn.execute(
                select(areas_table).where(areas_table.c.project_id == uuid)
            ).fetchall()
            
            areas_list = [row_to_dict(area) for area in areas_result]
            project_dict['areas'] = areas_list
            
            return jsonify(project_dict), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None
    # Query unique user names for the dropdown
    with engine.connect() as conn:
        user_names = [row[0] for row in conn.execute(select(projects_table.c.user_name).distinct())]
    selected_user_names = []

    if request.method == 'POST':
        # This block handles the main search form submission
        filters = []
        # Parse spatial box
        bottom_left = request.form.get('bottom_left', '').strip()
        top_right = request.form.get('top_right', '').strip()
        # Removed: relative_size_enabled, size_percentage, inside_enabled, outside_enabled, percentage_overlap_enabled, overlap_percentage

        if bottom_left and top_right:
            bl_result = parse_point(bottom_left)
            tr_result = parse_point(top_right)
            
            # Check for parsing errors
            if bl_result[1] is not None:  # Error in bottom_left
                error = f'Bottom Left: {bl_result[1]}'
            elif tr_result[1] is not None:  # Error in top_right
                error = f'Top Right: {tr_result[1]}'
            elif not bl_result[0] or not tr_result[0]:  # No coordinates returned
                error = 'Invalid input format. Please use X/Y or X,Y for both points.'
            else:
                xmin, ymin = bl_result[0]
                xmax, ymax = tr_result[0]
                if xmin >= xmax or ymin >= ymax:
                    error = 'Bottom Left must be southwest (smaller X and Y) of Top Right. Please check your input.'
                else:
                    # Only use the default INSIDE spatial filter
                    inside_filters = [
                        areas_table.c.xmin >= xmin,
                        areas_table.c.xmax <= xmax,
                        areas_table.c.ymin >= ymin,
                        areas_table.c.ymax <= ymax
                    ]
                    filters.append(and_(*inside_filters))
        # Parse other filters
        uuid = request.form.get('uuid', '').strip()
        if uuid:
            filters.append(projects_table.c.uuid.ilike(f"{uuid}%"))
        # Handle user name searches (both partial and exact matches)
        user_name_partial = request.form.get('user_name_partial', '').strip()
        user_name_list = request.form.getlist('user_name')
        selected_user_names = [n for n in user_name_list if n]
        
        # Combine all user name filters with OR logic
        user_name_filters = []
        if user_name_partial:
            user_name_filters.append(projects_table.c.user_name.ilike(f"{user_name_partial}%"))
        if selected_user_names:
            user_name_filters.extend([projects_table.c.user_name.ilike(f"{n}%") for n in selected_user_names])
        
        if user_name_filters:
            filters.append(or_(*user_name_filters))
        paper_size = request.form.get('paper_size', '').strip()
        custom_height = request.form.get('custom_height', '').strip()
        custom_width = request.form.get('custom_width', '').strip()

        if paper_size:
            if paper_size == 'custom' and custom_height and custom_width:
                try:
                    height_cm = float(custom_height)
                    width_cm = float(custom_width)
                    custom_size_format = f"Custom Size: Height: {height_cm} cm, Width: {width_cm} cm"
                    filters.append(projects_table.c.paper_size.ilike(f"{custom_size_format}%"))
                except ValueError:
                    error = 'Custom height and width must be valid numbers.'
            elif paper_size != 'custom':
                filters.append(projects_table.c.paper_size.ilike(f"{paper_size}%"))
            elif paper_size == 'custom' and (not custom_height or not custom_width):
                error = 'Please enter both height and width for custom size.'
        scale = request.form.get('scale', '').strip()
        if scale:
            # Filter projects by checking if *any* associated area has this scale
            # Support both old numeric format and new string format
            try:
                # Try to parse as float for backward compatibility
                scale_val = float(scale)
                filters.append(areas_table.c.scale == str(scale_val))
            except ValueError:
                # If not a number, treat as string scale format
                filters.append(areas_table.c.scale.ilike(f"%{scale}%"))

        # Parse date range
        date_from = request.form.get('date_from', '').strip()
        date_to = request.form.get('date_to', '').strip()

        if date_from or date_to:
            # Convert DD/MM/YYYY format to database format (DD-MM-YY) for comparison
            def convert_date_to_db_format(date_str):
                try:
                    if date_str and '/' in date_str:  # DD/MM/YYYY format
                        day, month, year = date_str.split('/')
                        # Convert to DD-MM-YY format for database comparison
                        return f"{day.zfill(2)}-{month.zfill(2)}-{year[2:]}"
                    elif date_str and '-' in date_str:  # DD-MM-YY format (already correct)
                        return date_str
                    return None
                except:
                    return None

            if date_from:
                converted_from = convert_date_to_db_format(date_from)
                if converted_from:
                    # For date comparison, we need to ensure proper string comparison
                    filters.append(projects_table.c.date >= converted_from)
                else:
                    error = 'Invalid date format for "From Date". Use DD/MM/YYYY format.'

            if date_to:
                converted_to = convert_date_to_db_format(date_to)
                if converted_to:
                    # For date comparison, we need to ensure proper string comparison
                    filters.append(projects_table.c.date <= converted_to)
                else:
                    error = 'Invalid date format for "To Date". Use DD/MM/YYYY format.'

        # Parse intersection range filter
        intersection_range_enabled = request.form.get('relative_size') == '1'
        intersection_range_from = request.form.get('relative_size_from', '').strip()
        intersection_range_to = request.form.get('relative_size_to', '').strip()

        # Validation: if intersection range is enabled, both values must be provided and valid
        if intersection_range_enabled:
            if not intersection_range_from or not intersection_range_to:
                error = 'Please enter both "From" and "To" values for Intersection Range.'
            else:
                try:
                    float(intersection_range_from)
                    float(intersection_range_to)
                except ValueError:
                    error = 'Intersection range values must be valid numbers.'

        if error is None:
            with engine.connect() as conn:
                # Use the same aggregation approach for all search results to ensure consistent associated_scales
                # This matches the "All Projects" table approach exactly
                projects_join_stmt = projects_table.outerjoin(areas_table, projects_table.c.uuid == areas_table.c.project_id)
                sel = select(
                    projects_table.c.uuid,
                    projects_table.c.project_name,
                    projects_table.c.user_name,
                    projects_table.c.date,
                    projects_table.c.file_location,
                    projects_table.c.paper_size,
                    projects_table.c.description,
                    func.coalesce(func.group_concat(distinct(areas_table.c.scale)), '').label('associated_scales')
                ).select_from(projects_join_stmt)

                if filters:
                    sel = sel.where(and_(*filters))

                sel = sel.group_by(
                    projects_table.c.uuid,
                    projects_table.c.project_name,
                    projects_table.c.user_name,
                    projects_table.c.date,
                    projects_table.c.file_location,
                    projects_table.c.paper_size,
                    projects_table.c.description
                )
                
                search_results = conn.execute(sel)
                results = [row._mapping for row in search_results]

                # Apply intersection range filter if enabled (after aggregation)
                if intersection_range_enabled and bottom_left and top_right and intersection_range_from and intersection_range_to:
                    try:
                        intersection_from = float(intersection_range_from)
                        intersection_to = float(intersection_range_to)
                        required_area = calculate_area_size(xmin, ymin, xmax, ymax)
                        filtered_results = []
                        for res in results:
                            res_dict = row_to_dict(res)
                            # For intersection filtering, we need to check individual areas
                            # This requires a separate query to get area details
                            project_uuid = res_dict['uuid']
                            area_query = select(areas_table).where(areas_table.c.project_id == project_uuid)
                            project_areas = conn.execute(area_query).fetchall()
                            
                            # Check if any area meets the intersection criteria
                            area_meets_criteria = False
                            for area in project_areas:
                                area_dict = row_to_dict(area)
                                if all(area_dict.get(k) is not None for k in ['xmin', 'ymin', 'xmax', 'ymax']):
                                    # Calculate intersection area
                                    intersect_xmin = max(area_dict['xmin'], xmin)
                                    intersect_ymin = max(area_dict['ymin'], ymin)
                                    intersect_xmax = min(area_dict['xmax'], xmax)
                                    intersect_ymax = min(area_dict['ymax'], ymax)
                                    if intersect_xmin < intersect_xmax and intersect_ymin < intersect_ymax:
                                        intersection_area = (intersect_xmax - intersect_xmin) * (intersect_ymax - intersect_ymin)
                                        intersection_pct = (intersection_area / required_area) * 100 if required_area > 0 else 0
                                        if intersection_from <= intersection_pct <= intersection_to:
                                            area_meets_criteria = True
                                            break
                            
                            if area_meets_criteria:
                                filtered_results.append(res_dict)
                        results = filtered_results
                    except ValueError:
                        error = 'Intersection range values must be valid numbers.'


            # Add absolute file location for file explorer links
            processed_results = []
            for i, row in enumerate(results or []):
                proj = row_to_dict(row)
                
                rel_path = proj['file_location']
                abs_path = os.path.abspath(rel_path)
                proj['abs_file_location'] = abs_path
                proj['abs_file_location_url'] = abs_path.replace("\\", "/")

                file_types = [('pdf', 'pdf'), ('jpeg', 'img'), ('jpg', 'img'), ('png', 'img')]
                all_files = []
                most_recent = None

                for ext, ftype in file_types:
                    pattern = os.path.join(abs_path, f"*.{ext}")
                    files = glob2.glob(pattern)
                for f in files:
                    if file_exists_check(f):  # Only process files that actually exist and are readable
                        ctime = os.path.getctime(f)
                        file_info = {
                            'path': f,
                            'type': ftype,
                            'ctime': ctime,
                            'filename': os.path.basename(f),
                            'rel_path': safe_relpath(f, os.path.abspath('.'))
                        }
                        all_files.append(file_info)

                        if (most_recent is None) or (ctime > most_recent['ctime']):
                            most_recent = file_info
                    else:
                        print(f"Skipping inaccessible file: {f}")
                
                all_files.sort(key=lambda x: x['ctime'], reverse=True)
                proj['all_files'] = all_files
                proj['file_count'] = len(all_files)

                if most_recent:
                    proj['view_file_path'] = safe_relpath(most_recent['path'], PROJECT_ROOT)
                    proj['view_file_type'] = most_recent['type']
                else:
                    proj['view_file_path'] = None
                    proj['view_file_type'] = None

                processed_results.append(proj)

            results = processed_results
    # This block handles GET requests for pagination and table filters
    # For "All Projects" table
    projects_current_page = request.args.get('page', 1, type=int)
    projects_per_page = request.args.get('per_page', 10, type=int)

    projects_filters = {
        'uuid_filter': request.args.get('projects_uuid_filter', '', type=str),
        'project_name_filter': request.args.get('projects_project_name_filter', '', type=str),
        'user_name_filter': request.args.get('projects_user_name_filter', '', type=str),
        'date_filter': request.args.get('projects_date_filter', '', type=str),
        'date_from_filter': request.args.get('projects_date_from_filter', '', type=str),
        'date_to_filter': request.args.get('projects_date_to_filter', '', type=str),
        'file_location_filter': request.args.get('projects_file_location_filter', '', type=str),
        'paper_size_filter': request.args.get('projects_paper_size_filter', '', type=str),
        'associated_scales_filter': request.args.get('projects_associated_scales_filter', '', type=str) # New filter
    }

    projects_query_filters = []
    if projects_filters['uuid_filter']:
        projects_query_filters.append(projects_table.c.uuid.ilike(f"{projects_filters['uuid_filter']}%"))
    if projects_filters['project_name_filter']:
        projects_query_filters.append(projects_table.c.project_name.ilike(f"{projects_filters['project_name_filter']}%"))
    if projects_filters['user_name_filter']:
        projects_query_filters.append(projects_table.c.user_name.ilike(f"{projects_filters['user_name_filter']}%"))
    if projects_filters['date_filter']:
        projects_query_filters.append(projects_table.c.date.ilike(f"{projects_filters['date_filter']}%"))
    if projects_filters['file_location_filter']:
        projects_query_filters.append(projects_table.c.file_location.ilike(f"{projects_filters['file_location_filter']}%"))
    if projects_filters['paper_size_filter']:
        projects_query_filters.append(projects_table.c.paper_size.ilike(f"{projects_filters['paper_size_filter']}%"))
    if projects_filters['associated_scales_filter']:
        # This filter needs to apply to the aggregated 'associated_scales' string
        # It's more complex as it's not a direct column. We'll handle this in the main query.
        pass

    # For "All Areas" table
    areas_current_page = request.args.get('areas_page', 1, type=int)
    areas_per_page = request.args.get('areas_per_page', 10, type=int)

    areas_filters = {
        'id_filter': request.args.get('areas_id_filter', '', type=str),
        'project_id_filter': request.args.get('areas_project_id_filter', '', type=str),
        'xmin_filter': request.args.get('areas_xmin_filter', '', type=str),
        'ymin_filter': request.args.get('areas_ymin_filter', '', type=str),
        'xmax_filter': request.args.get('areas_xmax_filter', '', type=str),
        'ymax_filter': request.args.get('areas_ymax_filter', '', type=str),
        'scale_filter': request.args.get('areas_scale_filter', '', type=str),
    }

    areas_query_filters = []
    if areas_filters['id_filter']:
        try:
            id_val = int(areas_filters['id_filter'])
            areas_query_filters.append(areas_table.c.id == id_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.id == -1)
    if areas_filters['project_id_filter']:
        areas_query_filters.append(areas_table.c.project_id.ilike(f"%{areas_filters['project_id_filter']}%"))
    if areas_filters['xmin_filter']:
        try:
            xmin_val = float(areas_filters['xmin_filter'])
            areas_query_filters.append(areas_table.c.xmin == xmin_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.xmin == -1)
    if areas_filters['ymin_filter']:
        try:
            ymin_val = float(areas_filters['ymin_filter'])
            areas_query_filters.append(areas_table.c.ymin == ymin_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.ymin == -1)
    if areas_filters['xmax_filter']:
        try:
            xmax_val = float(areas_filters['xmax_filter'])
            areas_query_filters.append(areas_table.c.xmax == xmax_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.xmax == -1)
    if areas_filters['ymax_filter']:
        try:
            ymax_val = float(areas_filters['ymax_filter'])
            areas_query_filters.append(areas_table.c.ymax == ymax_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.ymax == -1)
    if areas_filters['scale_filter']:
        try:
            # Try to parse as float for backward compatibility
            scale_val = float(areas_filters['scale_filter'])
            areas_query_filters.append(areas_table.c.scale == str(scale_val))
        except ValueError:
            # If not a number, treat as string scale format
            areas_query_filters.append(areas_table.c.scale.ilike(f"%{areas_filters['scale_filter']}%"))


    with engine.connect() as conn:
        # For "All Projects" table: Join projects and areas, group by project, and aggregate scales
        projects_join_stmt = projects_table.outerjoin(areas_table, projects_table.c.uuid == areas_table.c.project_id)

        # Base query for projects with aggregated scales
        projects_base_query = select(
            projects_table.c.uuid,
            projects_table.c.project_name,
            projects_table.c.user_name,
            projects_table.c.date,
            projects_table.c.file_location,
            projects_table.c.paper_size,
            projects_table.c.description,  # <-- Added
            func.coalesce(func.group_concat(distinct(areas_table.c.scale)), '').label('associated_scales')
        ).select_from(projects_join_stmt).group_by(
            projects_table.c.uuid,
            projects_table.c.project_name,
            projects_table.c.user_name,
            projects_table.c.date,
            projects_table.c.file_location,
            projects_table.c.paper_size,
            projects_table.c.description  # <-- Added
        )

        # Apply basic filters directly
        for f in projects_query_filters:
            projects_base_query = projects_base_query.where(f)

        # If there's a filter for associated_scales, it needs to be applied after aggregation
        # This requires subquerying or applying a HAVING clause, which SQLAlchemy's `label` helps with.
        if projects_filters['associated_scales_filter']:
            scale_filter_val = projects_filters['associated_scales_filter']
            # Convert float to string for comparison with concatenated string
            projects_base_query = projects_base_query.having(
                func.coalesce(func.group_concat(distinct(areas_table.c.scale)), '').like(f"%{scale_filter_val}%")
            )


        # Get total count for projects pagination
        # This needs to be done carefully when using group_by.
        # A subquery is usually the safest way to count distinct projects after filtering and grouping.
        count_subquery = select(projects_table.c.uuid).select_from(projects_join_stmt)
        for f in projects_query_filters:
            count_subquery = count_subquery.where(f)
        count_subquery = count_subquery.group_by(
            projects_table.c.uuid,
            projects_table.c.project_name,
            projects_table.c.user_name,
            projects_table.c.date,
            projects_table.c.file_location,
            projects_table.c.paper_size,
            projects_table.c.description  # <-- Added
        )
        if projects_filters['associated_scales_filter']:
             scale_filter_val = projects_filters['associated_scales_filter']
             count_subquery = count_subquery.having(
                 func.coalesce(func.group_concat(distinct(areas_table.c.scale)), '').like(f"%{scale_filter_val}%")
             )

        projects_total_items = conn.execute(select(func.count()).select_from(count_subquery.subquery())).scalar_one()

        projects_total_pages = (projects_total_items + projects_per_page - 1) // projects_per_page
        if projects_current_page > projects_total_pages and projects_total_pages > 0:
            projects_current_page = projects_total_pages
        elif projects_total_pages == 0:
             projects_current_page = 1 # No pages if no items

        # Query projects for the current page with filters and pagination
        projects_stmt = projects_base_query.limit(projects_per_page).offset((projects_current_page - 1) * projects_per_page)
        
        projects = conn.execute(projects_stmt).fetchall()

        # Add file information for projects (same as in search results)
        projects_list = []
        for i, proj in enumerate(projects):
            proj_dict = row_to_dict(proj)
            
            rel_path = proj_dict['file_location']
            abs_path = os.path.abspath(rel_path)
            proj_dict['abs_file_location'] = abs_path
            proj_dict['abs_file_location_url'] = abs_path.replace("\\", "/")

            # Find all files (PDF, JPEG, PNG) for this project
            file_types = [('pdf', 'pdf'), ('jpeg', 'img'), ('jpg', 'img'), ('png', 'img')]
            all_files = []
            most_recent = None

            for ext, ftype in file_types:
                pattern = os.path.join(abs_path, f"*.{ext}")
                files = glob2.glob(pattern)
                for f in files:
                    if file_exists_check(f):  # Only process files that actually exist and are readable
                        ctime = os.path.getctime(f)
                        file_info = {
                            'path': f,
                            'type': ftype,
                            'ctime': ctime,
                            'filename': os.path.basename(f),
                            'rel_path': safe_relpath(f, os.path.abspath('.'))
                        }
                        all_files.append(file_info)

                        # Track the most recent file for the single "View" option
                        if (most_recent is None) or (ctime > most_recent['ctime']):
                            most_recent = file_info
                    else:
                        print(f"Skipping inaccessible project file: {f}")

            # Sort files by creation time (newest first)
            all_files.sort(key=lambda x: x['ctime'], reverse=True)
            proj_dict['all_files'] = all_files
            proj_dict['file_count'] = len(all_files)

            if most_recent:
                proj_dict['view_file_path'] = safe_relpath(most_recent['path'], PROJECT_ROOT)
                proj_dict['view_file_type'] = most_recent['type']
                # Debug info
                print(f"Project {proj_dict.get('project_name', 'Unknown')}: Found file {most_recent['filename']}, path: {proj_dict['view_file_path']}")
            else:
                proj_dict['view_file_path'] = None
                proj_dict['view_file_type'] = None
                print(f"Project {proj_dict.get('project_name', 'Unknown')}: No files found in {abs_path}")

            projects_list.append(proj_dict)

        projects = projects_list  # Replace the original list with the processed one

        # Get total count for areas pagination
        areas_count_stmt = select(func.count()).select_from(areas_table)
        if areas_query_filters:
            areas_count_stmt = areas_count_stmt.where(and_(*areas_query_filters))
        areas_total_items = conn.execute(areas_count_stmt).scalar_one()

        areas_total_pages = (areas_total_items + areas_per_page - 1) // areas_per_page
        if areas_current_page > areas_total_pages and areas_total_pages > 0:
            areas_current_page = areas_total_pages
        elif areas_total_pages == 0:
            areas_current_page = 1 # No pages if no items

        # Query areas for the current page with filters, joined with projects to get file location
        areas_stmt = select(areas_table.c.id, areas_table.c.project_id, areas_table.c.xmin, areas_table.c.ymin, areas_table.c.xmax, areas_table.c.ymax, areas_table.c.scale, projects_table.c.file_location.label('project_file_location'))
        areas_stmt = areas_stmt.select_from(areas_table.join(projects_table, areas_table.c.project_id == projects_table.c.uuid))
        if areas_query_filters:
            areas_stmt = areas_stmt.where(and_(*areas_query_filters))
        areas_stmt = areas_stmt.limit(areas_per_page).offset((areas_current_page - 1) * areas_per_page)
        areas = conn.execute(areas_stmt).fetchall()

        # Add file information for areas (show files of associated project)
        areas_list = []
        for area in areas:
            area_dict = row_to_dict(area)
            project_file_location = area_dict['project_file_location']
            abs_path = os.path.abspath(project_file_location)
            area_dict['project_abs_file_location'] = abs_path

            # Find all files (PDF, JPEG, PNG) for the associated project
            file_types = [('pdf', 'pdf'), ('jpeg', 'img'), ('jpg', 'img'), ('png', 'img')]
            all_files = []
            most_recent = None

            for ext, ftype in file_types:
                pattern = os.path.join(abs_path, f"*.{ext}")
                files = glob2.glob(pattern)
                for f in files:
                    if file_exists_check(f):  # Only process files that actually exist and are readable
                        ctime = os.path.getctime(f)
                        file_info = {
                            'path': f,
                            'type': ftype,
                            'ctime': ctime,
                            'filename': os.path.basename(f),
                            'rel_path': safe_relpath(f, os.path.abspath('.'))
                        }
                        all_files.append(file_info)

                        # Track the most recent file for the single "View" option
                        if (most_recent is None) or (ctime > most_recent['ctime']):
                            most_recent = file_info
                    else:
                        print(f"Skipping inaccessible area file: {f}")

            # Sort files by creation time (newest first)
            all_files.sort(key=lambda x: x['ctime'], reverse=True)
            area_dict['project_all_files'] = all_files
            area_dict['project_file_count'] = len(all_files)

            if most_recent:
                area_dict['project_view_file_path'] = most_recent['rel_path']
                area_dict['project_view_file_type'] = most_recent['type']
            else:
                area_dict['project_view_file_path'] = None
                area_dict['project_view_file_type'] = None

            areas_list.append(area_dict)

        areas = areas_list  # Replace the original list with the processed one


    return render_template(
        'index.html',
        results=results,
        error=error,
        projects=projects,
        areas=areas,
        user_names=user_names,
        selected_user_names=selected_user_names,
        projects_current_page=projects_current_page,
        projects_per_page=projects_per_page,
        projects_total_pages=projects_total_pages,
        projects_filters=projects_filters,
        areas_current_page=areas_current_page,
        areas_per_page=areas_per_page,
        areas_total_pages=areas_total_pages,
        areas_filters=areas_filters,
        request=request # Pass request object to access form values for sticky inputs
    )

@app.route('/view_file/<path:rel_path>')
def view_file(rel_path):
    import os
    
    # Handle absolute paths with ABS: prefix (for cross-drive scenarios)
    if rel_path.startswith('ABS:'):
        # Remove the ABS: prefix and use the absolute path directly
        abs_path = rel_path[4:]  # Remove 'ABS:' prefix
        print(f"Using absolute path: {abs_path}")
    else:
        # Handle relative paths normally
        abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, rel_path))
        print(f"Using relative path joined with PROJECT_ROOT: {abs_path}")
    
    print(f"Final path: {abs_path}")
    print(f"File exists: {os.path.exists(abs_path)}")
    
    # Check if file exists
    if not os.path.exists(abs_path):
        return "File not found", 404
    
    # Serve the file
    try:
        return send_file(abs_path)
    except Exception as e:
        print(f"Error serving file: {e}")
        return f"Error accessing file: {str(e)}", 500

@app.route('/delete_project/<uuid>', methods=['POST'])
def delete_project(uuid):
    import shutil
    # Use engine.begin() for a transaction that auto-commits
    with engine.begin() as conn:
        # Get the file location for this project
        sel = select(projects_table.c.file_location).where(projects_table.c.uuid == uuid)
        result = conn.execute(sel).first()
        print(f"[DEBUG] Deletion requested for UUID: {uuid}")
        if result and result[0]:
            folder = result[0]
            print(f"[DEBUG] Project folder to delete: {folder}")
            if os.path.exists(folder) and os.path.isdir(folder):
                try:
                    shutil.rmtree(folder)
                    print(f"[DEBUG] Folder deleted: {folder}")
                except Exception as e:
                    print(f"[DEBUG] Error deleting folder: {e}")
            else:
                print(f"[DEBUG] Folder does not exist or is not a directory: {folder}")
        proj_result = conn.execute(projects_table.delete().where(projects_table.c.uuid == uuid))
        print(f"[DEBUG] Projects deleted: {proj_result.rowcount}")
        area_result = conn.execute(areas_table.delete().where(areas_table.c.project_id == uuid))
        print(f"[DEBUG] Areas deleted: {area_result.rowcount}")
    print(f"[DEBUG] Deletion complete for UUID: {uuid}")
    return redirect(url_for('index'))

# No app.run() here - server execution is handled by main.py