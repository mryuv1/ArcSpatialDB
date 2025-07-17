from flask import Flask, render_template, request, url_for, send_file, redirect
from sqlalchemy import create_engine, MetaData, Table, and_, select, distinct, func, text, or_
import os
import glob2
from datetime import datetime
import shutil

app = Flask(__name__)
DATABASE = 'elements.db'
UPLOAD_FOLDER = 'sampleDataset'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = sqlite3.connect(DATABASE)

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
    try:
        s = s.strip()
        if '/' in s:
            x_str, y_str = s.split('/')
        elif ',' in s:
            x_str, y_str = s.split(',')
        else:
            return None
        return float(x_str), float(y_str)
    except Exception:
        return None

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
        relative_size_enabled = request.form.get('relative_size') == '1'
        size_percentage = request.form.get('size_percentage', '10').strip()

        # New spatial relationship options
        inside_enabled = request.form.get('inside') == '1'
        outside_enabled = request.form.get('outside') == '1'
        percentage_overlap_enabled = request.form.get('percentage_overlap') == '1'
        overlap_percentage = request.form.get('overlap_percentage', '50').strip()

        if bottom_left and top_right:
            bl = parse_point(bottom_left)
            tr = parse_point(top_right)
            if not bl or not tr:
                error = 'Invalid input format. Please use X/Y or X,Y for both points.'
            else:
                xmin, ymin = bl
                xmax, ymax = tr
                if xmin >= xmax or ymin >= ymax:
                    error = 'Bottom Left must be southwest (smaller X and Y) of Top Right. Please check your input.'
                else:
                    join_areas = True

                    # Build spatial filters based on selected options
                    spatial_filters = []

                    if relative_size_enabled:
                        try:
                            percentage = float(size_percentage)
                            if percentage < 0 or percentage > 1000:
                                error = 'Percentage must be between 0 and 1000.'
                            else:
                                # Calculate the reference area size
                                reference_area_size = calculate_area_size(xmin, ymin, xmax, ymax)

                                # Calculate the size range (±percentage)
                                min_size = reference_area_size * (1 - percentage / 100)
                                max_size = reference_area_size * (1 + percentage / 100)

                                # Add size comparison filter using calculated area
                                area_size_expr = (areas_table.c.xmax - areas_table.c.xmin) * (areas_table.c.ymax - areas_table.c.ymin)
                                size_filters = [
                                    area_size_expr >= min_size,
                                    area_size_expr <= max_size
                                ]
                                spatial_filters.append(and_(*size_filters))
                        except ValueError:
                            error = 'Percentage must be a valid number.'
                    # Add spatial relationship filters
                    if inside_enabled:
                        # Inside: area is completely within the query rectangle
                        inside_filters = [
                            areas_table.c.xmin >= xmin,
                            areas_table.c.xmax <= xmax,
                            areas_table.c.ymin >= ymin,
                            areas_table.c.ymax <= ymax
                        ]
                        spatial_filters.append(and_(*inside_filters))

                    if outside_enabled:
                        # Outside: area is completely outside the query rectangle
                        outside_filters = [
                            or_(
                                areas_table.c.xmax < xmin,
                                areas_table.c.xmin > xmax,
                                areas_table.c.ymax < ymin,
                                areas_table.c.ymin > ymax
                            )
                        ]
                        spatial_filters.append(or_(*outside_filters))

                    if percentage_overlap_enabled:
                        try:
                            overlap_percentage_val = float(overlap_percentage)
                            if overlap_percentage_val < 0 or overlap_percentage_val > 100:
                                error = 'Overlap percentage must be between 0 and 100.'
                            else:
                                # For percentage overlap, we'll filter after the query
                                # Store the parameters for post-processing
                                spatial_filters.append(text("1=1"))  # Include all areas for percentage calculation
                        except ValueError:
                            error = 'Overlap percentage must be a valid number.'

                    # If no specific spatial relationship is selected, use standard overlap
                    if not (relative_size_enabled or inside_enabled or outside_enabled or percentage_overlap_enabled):
                        # Standard spatial overlap
                        overlap_filters = [
                            areas_table.c.xmin < xmax,
                            areas_table.c.xmax > xmin,
                            areas_table.c.ymin < ymax,
                            areas_table.c.ymax > ymin
                        ]
                        spatial_filters.append(and_(*overlap_filters))

                    # Combine all spatial filters with OR operator
                    if spatial_filters:
                        filters.append(or_(*spatial_filters))
        # Parse other filters
        uuid = request.form.get('uuid', '').strip()
        if uuid:
            filters.append(projects_table.c.uuid.ilike(f"{uuid}%"))
        user_name_list = request.form.getlist('user_name')
        selected_user_names = [n for n in user_name_list if n]
        if selected_user_names:
            filters.append(or_(*[projects_table.c.user_name.ilike(f"{n}%") for n in selected_user_names]))
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

        if error is None:
            with engine.connect() as conn:
                # Always join areas to retrieve scales if we're going to display them
                # For search results, we want to show all scales for a project if multiple exist
                join_stmt = projects_table.join(areas_table, projects_table.c.uuid == areas_table.c.project_id, isouter=True)

                if percentage_overlap_enabled:
                    # Get all areas and projects first, then filter by percentage
                    sel = select(projects_table.c, areas_table.c).select_from(join_stmt)
                    if filters:
                        # Apply filters that are not related to percentage overlap
                        sel = sel.where(and_(*[f for f in filters if f != text("1=1")])) # Exclude the dummy filter
                    all_results = conn.execute(sel).fetchall()

                    # Filter by percentage overlap
                    filtered_project_uuids = set()
                    project_scales = {} # To store unique scales for each project
                    for row in all_results:
                        project_data = {col: getattr(row, col) for col in projects_table.c.keys()}
                        area_data = {col: getattr(row, col) for col in areas_table.c.keys()}

                        # Only calculate overlap if area data exists
                        if area_data['xmin'] is not None and area_data['ymin'] is not None and \
                           area_data['xmax'] is not None and area_data['ymax'] is not None:
                            overlap_pct = calculate_overlap_percentage(
                                area_data['xmin'], area_data['ymin'], area_data['xmax'], area_data['ymax'],
                                xmin, ymin, xmax, ymax
                            )

                            if overlap_pct >= float(overlap_percentage):
                                filtered_project_uuids.add(project_data['uuid'])
                                if project_data['uuid'] not in project_scales:
                                    project_scales[project_data['uuid']] = set()
                                if area_data['scale'] is not None:
                                    project_scales[project_data['uuid']].add(area_data['scale'])
                        else: # Include project if it has no associated areas and no spatial filter applies
                            if not (bottom_left and top_right): # If no spatial filter, include projects without areas
                                filtered_project_uuids.add(project_data['uuid'])
                                if project_data['uuid'] not in project_scales:
                                    project_scales[project_data['uuid']] = set()


                    # Get the filtered projects and their associated scales
                    results = []
                    if filtered_project_uuids:
                        # Select distinct projects and group their scales
                        sel = select(
                            projects_table.c.uuid,
                            projects_table.c.project_name,
                            projects_table.c.user_name,
                            projects_table.c.date,
                            projects_table.c.file_location,
                            projects_table.c.paper_size,
                            func.group_concat(distinct(areas_table.c.scale)).label('associated_scales')
                        ).select_from(join_stmt).where(
                            projects_table.c.uuid.in_(list(filtered_project_uuids))
                        ).group_by(
                            projects_table.c.uuid,
                            projects_table.c.project_name,
                            projects_table.c.user_name,
                            projects_table.c.date,
                            projects_table.c.file_location,
                            projects_table.c.paper_size
                        )
                        results = [row._mapping for row in conn.execute(sel)]

                        # Post-process to ensure only relevant scales are added from the original project_scales dict
                        processed_results = []
                        for res in results:
                            res_dict = dict(res)  # Convert RowMapping to dict
                            uuid = res_dict['uuid']
                            if uuid in project_scales:
                                scales = sorted(list(project_scales[uuid]))
                                res_dict['associated_scales'] = ', '.join(map(str, scales)) if scales else None
                            else:
                                res_dict['associated_scales'] = None
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
                        projects_table.c.paper_size
                    )
                    results = [row._mapping for row in conn.execute(sel)]

            # Add absolute file location for file explorer links
            processed_results = []
            for row in results or []:
                proj = dict(row)
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
                    proj['view_file_path'] = most_recent['path']
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
            func.group_concat(distinct(areas_table.c.scale)).label('associated_scales')
        ).select_from(projects_join_stmt).group_by(
            projects_table.c.uuid,
            projects_table.c.project_name,
            projects_table.c.user_name,
            projects_table.c.date,
            projects_table.c.file_location,
            projects_table.c.paper_size
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
            projects_table.c.paper_size
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
            proj_dict = dict(proj._mapping)  # Convert Row to dict
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
                proj_dict['view_file_path'] = most_recent['path']
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
            area_dict = dict(area._mapping)  # Convert Row to dict
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
    abs_path = os.path.abspath(rel_path)
    # Security: Only allow files inside your project directory
    if not abs_path.startswith(os.path.abspath('.')):
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

if __name__ == '__main__':
    app.run(debug=True)