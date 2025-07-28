from flask import Flask, render_template, request, url_for, send_file, redirect, jsonify
from sqlalchemy import create_engine, MetaData, Table, and_, select, distinct, func, text, or_
import os
import glob2
from datetime import datetime
import shutil
import uuid

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

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
DATABASE = 'elements.db'


# Custom filter for datetime formatting
@app.template_filter('datetime')
def datetime_filter(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

DATABASE_URL = 'sqlite:///elements.db'
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Reflect only the tables that exist
projects_table = Table('projects', metadata, autoload_with=engine)
areas_table = Table('areas', metadata, autoload_with=engine)

def parse_point(s):
    """
    Parse coordinate string with support for various separators and formats.
    Supports: '/', ',', ':', ';', '|', ' ', '\t', '\\', and combinations
    Also handles WGS84 format and other coordinate system prefixes
    Handles complex formats like:
    - WGS84 UTM 36N 735712 E / 3563829 N
    - WGS84 Geo 35° 30' 0.11" E / 32° 11' 9.88" N
    
    Returns: (x, y) if successful, or (None, error_message) if failed
    """
    try:
        s = str(s).strip()
        
        # Check for empty or whitespace-only input
        if not s:
            return None, "Empty coordinate string provided"
        
        # Handle complex WGS84 UTM format: "WGS84 UTM 36N 735712 E / 3563829 N"
        if 'WGS84 UTM' in s.upper():
            import re
            # Pattern: WGS84 UTM [zone][N/S] [easting] [E/W] / [northing] [N/S]
            utm_pattern = r'WGS84\s+UTM\s+(\d+[NS])\s+(\d+)\s*[EW]\s*/\s*(\d+)\s*[NS]'
            match = re.search(utm_pattern, s, re.IGNORECASE)
            if match:
                try:
                    zone = match.group(1)
                    easting = float(match.group(2))
                    northing = float(match.group(3))
                    return (easting, northing), None
                except ValueError as e:
                    return None, f"Invalid UTM coordinates in '{s}': {str(e)}"
            else:
                return None, f"Invalid WGS84 UTM format. Expected: 'WGS84 UTM [zone][N/S] [easting] [E/W] / [northing] [N/S]'"
        
        # Handle complex WGS84 Geographic format: "WGS84 Geo 35° 30' 0.11" E / 32° 11' 9.88" N"
        if 'WGS84 GEO' in s.upper():
            import re
            # Pattern: WGS84 Geo [deg]° [min]' [sec]" [E/W] / [deg]° [min]' [sec]" [N/S]
            geo_pattern = r'WGS84\s+GEO\s+(\d+)°\s*(\d+)\'\s*([\d.]+)"\s*[EW]\s*/\s*(\d+)°\s*(\d+)\'\s*([\d.]+)"\s*[NS]'
            match = re.search(geo_pattern, s, re.IGNORECASE)
            if match:
                try:
                    # Convert DMS to decimal degrees
                    lon_deg, lon_min, lon_sec = float(match.group(1)), float(match.group(2)), float(match.group(3))
                    lat_deg, lat_min, lat_sec = float(match.group(4)), float(match.group(5)), float(match.group(6))
                    
                    # Check if longitude is East or West
                    if 'W' in s.upper():
                        lon_deg = -lon_deg
                    if 'S' in s.upper():
                        lat_deg = -lat_deg
                    
                    # Convert to decimal degrees
                    lon_decimal = lon_deg + (lon_min / 60) + (lon_sec / 3600)
                    lat_decimal = lat_deg + (lat_min / 60) + (lat_sec / 3600)
                    
                    return (lon_decimal, lat_decimal), None
                except ValueError as e:
                    return None, f"Invalid geographic coordinates in '{s}': {str(e)}"
            else:
                return None, f"Invalid WGS84 Geographic format. Expected: 'WGS84 Geo [deg]° [min]' [sec]\" [E/W] / [deg]° [min]' [sec]\" [N/S]'"
        
        # Handle simple WGS84 and other coordinate system prefixes
        if s.upper().startswith(('WGS', 'EPSG', 'UTM', 'GEO', 'PROJ')):
            # Extract coordinates after the prefix
            # Look for common patterns like "WGS84: 123.456, 789.012" or "UTM 36N: 123456, 789012"
            import re
            # Match coordinates after any prefix
            coord_match = re.search(r'[:\s]+([-\d.,\s]+)$', s)
            if coord_match:
                s = coord_match.group(1).strip()
            else:
                return None, f"Invalid coordinate system format. Expected: '[SYSTEM]: [x], [y]' or '[SYSTEM] [x], [y]'"
        
        # Remove any parentheses, brackets, or quotes
        s = s.strip('()[]{}"\'\'')
        
        # Try multiple separators in order of preference
        separators = ['/', ',', ':', ';', '|', '\\', '\t']
        
        # First try exact separators
        for sep in separators:
            if sep in s:
                parts = s.split(sep, 1)  # Split only on first occurrence
                if len(parts) == 2:
                    x_str, y_str = parts[0].strip(), parts[1].strip()
                    # Try to convert to float
                    try:
                        return (float(x_str), float(y_str)), None
                    except ValueError:
                        continue
        
        # If no separator found, try splitting on whitespace
        if ' ' in s:
            parts = s.split()
            if len(parts) >= 2:
                try:
                    return (float(parts[0]), float(parts[1])), None
                except ValueError:
                    pass
        
        # Try regex pattern for coordinates with optional spaces and various separators
        import re
        # Pattern: number, optional spaces, separator, optional spaces, number
        coord_pattern = r'([-+]?\d*\.?\d+)\s*[\/,:;|\t\\]\s*([-+]?\d*\.?\d+)'
        match = re.search(coord_pattern, s)
        if match:
            try:
                return (float(match.group(1)), float(match.group(2))), None
            except ValueError:
                pass
        
        # Try pattern for coordinates separated by whitespace
        space_pattern = r'([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)'
        match = re.search(space_pattern, s)
        if match:
            try:
                return (float(match.group(1)), float(match.group(2))), None
            except ValueError:
                pass
        
        # If we get here, no valid format was found
        return None, f"Invalid coordinate format: '{s}'. Expected formats: 'x,y', 'x/y', 'x:y', 'WGS84 UTM 36N 735712 E / 3563829 N', 'WGS84 Geo 35° 30' 0.11\" E / 32° 11' 9.88\" N', etc."
    except Exception as e:
        return None, f"Error parsing coordinates '{s}': {str(e)}"

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
                    
                    conn.execute(areas_table.insert().values(
                        project_id=generated_uuid,
                        xmin=area_data['xmin'],
                        ymin=area_data['ymin'],
                        xmax=area_data['xmax'],
                        ymax=area_data['ymax'],
                        scale=area_data['scale']
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
        join_areas = False
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
                    join_areas = True
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
            try:
                scale_val = float(scale)
                # Filter projects by checking if *any* associated area has this scale
                join_areas = True # Ensure join is active if scale is filtered
                filters.append(areas_table.c.scale == scale_val)
            except ValueError:
                error = 'Scale must be a number.'

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
                # Always join areas to retrieve scales if we're going to display them
                # For search results, we want to show all scales for a project if multiple exist
                join_stmt = projects_table.join(areas_table, projects_table.c.uuid == areas_table.c.project_id, isouter=True)

                # Remove all references to relative_size, inside, outside, percentage_overlap, and their post-processing
                # The percentage_overlap_enabled and overlap_percentage logic is removed.
                # The default spatial filter is now always INSIDE.

                # Combine all spatial filters with OR operator
                if filters:
                    results = conn.execute(select(*projects_table.c, *areas_table.c).select_from(join_stmt).where(and_(*filters))).fetchall()

                    # Apply intersection range filter if enabled
                    if intersection_range_enabled and bottom_left and top_right and intersection_range_from and intersection_range_to:
                        try:
                            intersection_from = float(intersection_range_from)
                            intersection_to = float(intersection_range_to)
                            required_area = calculate_area_size(xmin, ymin, xmax, ymax)
                            filtered_results = []
                            for res in results:
                                res_dict = row_to_dict(res)
                                # Only filter if area coordinates are present
                                if all(res_dict.get(k) is not None for k in ['xmin', 'ymin', 'xmax', 'ymax']):
                                    # Calculate intersection area
                                    intersect_xmin = max(res_dict['xmin'], xmin)
                                    intersect_ymin = max(res_dict['ymin'], ymin)
                                    intersect_xmax = min(res_dict['xmax'], xmax)
                                    intersect_ymax = min(res_dict['ymax'], ymax)
                                    if intersect_xmin < intersect_xmax and intersect_ymin < intersect_ymax:
                                        intersection_area = (intersect_xmax - intersect_xmin) * (intersect_ymax - intersect_ymin)
                                        intersection_pct = (intersection_area / required_area) * 100 if required_area > 0 else 0
                                        if intersection_from <= intersection_pct <= intersection_to:
                                            filtered_results.append(res_dict)
                                else:
                                    # If area coordinates are missing, skip filtering
                                    filtered_results.append(res_dict)
                            results = filtered_results
                        except ValueError:
                            error = 'Intersection range values must be valid numbers.'

                    # Get the filtered projects and their associated scales
                    processed_results = []
                    for res in results:
                        res_dict = row_to_dict(res)
                        uuid = res_dict['uuid']
                        # The project_scales logic is removed as percentage overlap is gone.
                        # If you want to show associated_scales, use the value from the query or set to None.
                        res_dict['associated_scales'] = res_dict.get('associated_scales', None)
                        processed_results.append(res_dict)
                    results = processed_results
                else:
                    # Standard filtering - we need to group by project to get all scales per project
                    sel = select(
                        projects_table.c.uuid,
                        projects_table.c.project_name,
                        projects_table.c.user_name,
                        projects_table.c.date,
                        projects_table.c.file_location,
                        projects_table.c.paper_size,
                        projects_table.c.description,  # <-- Added
                        func.group_concat(distinct(areas_table.c.scale)).label('associated_scales') # Aggregate scales
                    ).select_from(join_stmt)

                    if filters:
                        sel = sel.where(and_(*filters))

                    sel = sel.group_by(
                        projects_table.c.uuid,
                        projects_table.c.project_name,
                        projects_table.c.user_name,
                        projects_table.c.date,
                        projects_table.c.file_location,
                        projects_table.c.paper_size,
                        projects_table.c.description  # <-- Added
                    )
                    results = [row._mapping for row in conn.execute(sel)]

            # Add absolute file location for file explorer links
            processed_results = []
            for row in results or []:
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
                        ctime = os.path.getctime(f)
                        file_info = {
                            'path': f,
                            'type': ftype,
                            'ctime': ctime,
                            'filename': os.path.basename(f),
                            'rel_path': os.path.relpath(f, os.path.abspath('.'))
                        }
                        all_files.append(file_info)

                        if (most_recent is None) or (ctime > most_recent['ctime']):
                            most_recent = file_info

                all_files.sort(key=lambda x: x['ctime'], reverse=True)
                proj['all_files'] = all_files
                proj['file_count'] = len(all_files)

                if most_recent:
                    proj['view_file_path'] = os.path.relpath(most_recent['path'], PROJECT_ROOT)
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
            scale_val = float(areas_filters['scale_filter'])
            areas_query_filters.append(areas_table.c.scale == scale_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.scale == -1)


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
            func.group_concat(distinct(areas_table.c.scale)).label('associated_scales')
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
                func.group_concat(distinct(areas_table.c.scale)).like(f"%{scale_filter_val}%")
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
                 func.group_concat(distinct(areas_table.c.scale)).like(f"%{scale_filter_val}%")
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
        for proj in projects:
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
                    ctime = os.path.getctime(f)
                    file_info = {
                        'path': f,
                        'type': ftype,
                        'ctime': ctime,
                        'filename': os.path.basename(f),
                        'rel_path': os.path.relpath(f, os.path.abspath('.'))
                    }
                    all_files.append(file_info)

                    # Track the most recent file for the single "View" option
                    if (most_recent is None) or (ctime > most_recent['ctime']):
                        most_recent = file_info

            # Sort files by creation time (newest first)
            all_files.sort(key=lambda x: x['ctime'], reverse=True)
            proj_dict['all_files'] = all_files
            proj_dict['file_count'] = len(all_files)

            if most_recent:
                proj_dict['view_file_path'] = os.path.relpath(most_recent['path'], PROJECT_ROOT)
                proj_dict['view_file_type'] = most_recent['type']
            else:
                proj_dict['view_file_path'] = None
                proj_dict['view_file_type'] = None

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
                    ctime = os.path.getctime(f)
                    file_info = {
                        'path': f,
                        'type': ftype,
                        'ctime': ctime,
                        'filename': os.path.basename(f),
                        'rel_path': os.path.relpath(f, os.path.abspath('.'))
                    }
                    all_files.append(file_info)

                    # Track the most recent file for the single "View" option
                    if (most_recent is None) or (ctime > most_recent['ctime']):
                        most_recent = file_info

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
    abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, rel_path))
    print(f"Requested: {abs_path}")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Startswith: {abs_path.startswith(PROJECT_ROOT)}")
    # Security: Only allow files inside your project directory
    if not abs_path.startswith(PROJECT_ROOT):
        return "Access denied", 403
    return send_file(abs_path)

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