from flask import Blueprint, jsonify, request
from sqlalchemy import select, distinct, func, and_, or_
from models.database import engine, projects_table, areas_table
from utils.helpers import parse_point, calculate_area_size, convert_date_to_db_format
from utils.file_utils import get_project_files
import os
import uuid

def generate_unique_uuid():
    """
    Generate a unique UUID that doesn't exist in the database.
    
    Returns:
        str: A unique UUID string
    """
    with engine.connect() as conn:
        while True:
            generated_uuid = str(uuid.uuid4())
            # Check if UUID already exists
            existing = conn.execute(
                select(projects_table.c.uuid).where(projects_table.c.uuid == generated_uuid)
            ).first()
            if not existing:
                return generated_uuid

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/projects', methods=['GET'])
def get_all_projects():
    """Get all projects with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filters
        filters = {}
        filters['uuid_filter'] = request.args.get('uuid_filter', '', type=str)
        filters['project_name_filter'] = request.args.get('project_name_filter', '', type=str)
        filters['user_name_filter'] = request.args.get('user_name_filter', '', type=str)
        filters['date_filter'] = request.args.get('date_filter', '', type=str)
        filters['date_from_filter'] = request.args.get('date_from_filter', '', type=str)
        filters['date_to_filter'] = request.args.get('date_to_filter', '', type=str)
        filters['file_location_filter'] = request.args.get('file_location_filter', '', type=str)
        filters['paper_size_filter'] = request.args.get('paper_size_filter', '', type=str)
        filters['associated_scales_filter'] = request.args.get('associated_scales_filter', '', type=str)
        
        query_filters = []
        if filters['uuid_filter']:
            query_filters.append(projects_table.c.uuid.ilike(f"{filters['uuid_filter']}%"))
        if filters['project_name_filter']:
            query_filters.append(projects_table.c.project_name.ilike(f"{filters['project_name_filter']}%"))
        if filters['user_name_filter']:
            query_filters.append(projects_table.c.user_name.ilike(f"{filters['user_name_filter']}%"))
        if filters['date_filter']:
            query_filters.append(projects_table.c.date.ilike(f"{filters['date_filter']}%"))
        if filters['file_location_filter']:
            query_filters.append(projects_table.c.file_location.ilike(f"{filters['file_location_filter']}%"))
        if filters['paper_size_filter']:
            query_filters.append(projects_table.c.paper_size.ilike(f"{filters['paper_size_filter']}%"))

        with engine.connect() as conn:
            # Join projects and areas, group by project, and aggregate scales
            join_stmt = projects_table.outerjoin(areas_table, projects_table.c.uuid == areas_table.c.project_id)

            # Base query for projects with aggregated scales
            base_query = select(
                projects_table.c.uuid,
                projects_table.c.project_name,
                projects_table.c.user_name,
                projects_table.c.date,
                projects_table.c.file_location,
                projects_table.c.paper_size,
                projects_table.c.description,
                func.group_concat(distinct(areas_table.c.scale)).label('associated_scales')
            ).select_from(join_stmt).group_by(
                projects_table.c.uuid,
                projects_table.c.project_name,
                projects_table.c.user_name,
                projects_table.c.date,
                projects_table.c.file_location,
                projects_table.c.paper_size,
                projects_table.c.description
            )

            # Apply basic filters
            for f in query_filters:
                base_query = base_query.where(f)

            # Handle associated scales filter
            if filters['associated_scales_filter']:
                scale_filter_val = filters['associated_scales_filter']
                base_query = base_query.having(
                    func.group_concat(distinct(areas_table.c.scale)).like(f"%{scale_filter_val}%")
                )

            # Get total count for pagination
            count_subquery = select(projects_table.c.uuid).select_from(join_stmt)
            for f in query_filters:
                count_subquery = count_subquery.where(f)
            count_subquery = count_subquery.group_by(
                projects_table.c.uuid,
                projects_table.c.project_name,
                projects_table.c.user_name,
                projects_table.c.date,
                projects_table.c.file_location,
                projects_table.c.paper_size,
                projects_table.c.description
            )
            if filters['associated_scales_filter']:
                scale_filter_val = filters['associated_scales_filter']
                count_subquery = count_subquery.having(
                    func.group_concat(distinct(areas_table.c.scale)).like(f"%{scale_filter_val}%")
                )

            total_items = conn.execute(select(func.count()).select_from(count_subquery.subquery())).scalar_one()
            total_pages = (total_items + per_page - 1) // per_page

            if page > total_pages and total_pages > 0:
                page = total_pages
            elif total_pages == 0:
                page = 1

            # Query projects for the current page
            stmt = base_query.limit(per_page).offset((page - 1) * per_page)
            projects = conn.execute(stmt).fetchall()

            # Process projects and add file information
            projects_list = []
            for proj in projects:
                proj_dict = dict(proj)
                
                # Add file information
                file_info = get_project_files(proj_dict['file_location'])
                proj_dict.update(file_info)
                
                # Add absolute file location
                abs_path = os.path.abspath(proj_dict['file_location'])
                proj_dict['abs_file_location'] = abs_path
                proj_dict['abs_file_location_url'] = abs_path.replace("\\", "/")
                
                if file_info['most_recent']:
                    proj_dict['view_file_path'] = file_info['most_recent']['rel_path']
                    proj_dict['view_file_type'] = file_info['most_recent']['type']
                else:
                    proj_dict['view_file_path'] = None
                    proj_dict['view_file_type'] = None

                projects_list.append(proj_dict)

            return jsonify({
                'projects': projects_list,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'total_items': total_items
                },
                'filters': filters
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/search', methods=['POST'])
def search_projects():
    """Search projects with advanced filtering"""
    try:
        data = request.get_json() or {}
        
        filters = []
        join_areas = False

        # Parse spatial box
        bottom_left = data.get('bottom_left', '').strip()
        top_right = data.get('top_right', '').strip()
        
        if bottom_left and top_right:
            bl_result = parse_point(bottom_left)
            tr_result = parse_point(top_right)
            
            # Check for parsing errors
            if bl_result[1] is not None:  # Error in bottom_left
                return jsonify({'error': f'Bottom Left: {bl_result[1]}'}), 400
            elif tr_result[1] is not None:  # Error in top_right
                return jsonify({'error': f'Top Right: {tr_result[1]}'}), 400
            elif not bl_result[0] or not tr_result[0]:  # No coordinates returned
                return jsonify({'error': 'Invalid input format. Please use X/Y or X,Y for both points.'}), 400
            else:
                xmin, ymin = bl_result[0]
                xmax, ymax = tr_result[0]
                if xmin >= xmax or ymin >= ymax:
                    return jsonify({'error': 'Bottom Left must be southwest (smaller X and Y) of Top Right. Please check your input.'}), 400
                
                join_areas = True
                # Default INSIDE spatial filter
                inside_filters = [
                    areas_table.c.xmin >= xmin,
                    areas_table.c.xmax <= xmax,
                    areas_table.c.ymin >= ymin,
                    areas_table.c.ymax <= ymax
                ]
                filters.append(and_(*inside_filters))

        # Parse other filters
        uuid = data.get('uuid', '').strip()
        if uuid:
            filters.append(projects_table.c.uuid.ilike(f"{uuid}%"))

        user_names = data.get('user_names', [])
        if user_names:
            filters.append(or_(*[projects_table.c.user_name.ilike(f"{n}%") for n in user_names]))

        paper_size = data.get('paper_size', '').strip()
        custom_height = data.get('custom_height', '').strip()
        custom_width = data.get('custom_width', '').strip()

        if paper_size:
            if paper_size == 'custom' and custom_height and custom_width:
                try:
                    height_cm = float(custom_height)
                    width_cm = float(custom_width)
                    custom_size_format = f"Custom Size: Height: {height_cm} cm, Width: {width_cm} cm"
                    filters.append(projects_table.c.paper_size.ilike(f"{custom_size_format}%"))
                except ValueError:
                    return jsonify({'error': 'Custom height and width must be valid numbers.'}), 400
            elif paper_size != 'custom':
                filters.append(projects_table.c.paper_size.ilike(f"{paper_size}%"))
            elif paper_size == 'custom' and (not custom_height or not custom_width):
                return jsonify({'error': 'Please enter both height and width for custom size.'}), 400

        scale = data.get('scale', '').strip()
        if scale:
            try:
                scale_val = float(scale)
                join_areas = True
                filters.append(areas_table.c.scale == scale_val)
            except ValueError:
                return jsonify({'error': 'Scale must be a number.'}), 400

        # Parse date range
        date_from = data.get('date_from', '').strip()
        date_to = data.get('date_to', '').strip()

        if date_from:
            converted_from = convert_date_to_db_format(date_from)
            if converted_from:
                filters.append(projects_table.c.date >= converted_from)
            else:
                return jsonify({'error': 'Invalid date format for "From Date". Use DD/MM/YYYY format.'}), 400

        if date_to:
            converted_to = convert_date_to_db_format(date_to)
            if converted_to:
                filters.append(projects_table.c.date <= converted_to)
            else:
                return jsonify({'error': 'Invalid date format for "To Date". Use DD/MM/YYYY format.'}), 400

        # Parse intersection range filter
        intersection_range_enabled = data.get('relative_size', False)
        intersection_range_from = data.get('relative_size_from', '').strip()
        intersection_range_to = data.get('relative_size_to', '').strip()

        if intersection_range_enabled:
            if not intersection_range_from or not intersection_range_to:
                return jsonify({'error': 'Please enter both "From" and "To" values for Intersection Range.'}), 400
            try:
                float(intersection_range_from)
                float(intersection_range_to)
            except ValueError:
                return jsonify({'error': 'Intersection range values must be valid numbers.'}), 400

        with engine.connect() as conn:
            # Join areas to retrieve scales
            join_stmt = projects_table.join(areas_table, projects_table.c.uuid == areas_table.c.project_id, isouter=True)

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
                            res_dict = dict(res)
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
                                filtered_results.append(res_dict)
                        
                        results = filtered_results
                    except ValueError:
                        return jsonify({'error': 'Intersection range values must be valid numbers.'}), 400
            else:
                # Get all projects with aggregated scales
                sel = select(
                    projects_table.c.uuid,
                    projects_table.c.project_name,
                    projects_table.c.user_name,
                    projects_table.c.date,
                    projects_table.c.file_location,
                    projects_table.c.paper_size,
                    projects_table.c.description,
                    func.group_concat(distinct(areas_table.c.scale)).label('associated_scales')
                ).select_from(join_stmt).group_by(
                    projects_table.c.uuid,
                    projects_table.c.project_name,
                    projects_table.c.user_name,
                    projects_table.c.date,
                    projects_table.c.file_location,
                    projects_table.c.paper_size,
                    projects_table.c.description
                )
                
                results = [row for row in conn.execute(sel)]

            # Process results and add file information
            processed_results = []
            for row in results or []:
                proj = dict(row)
                
                # Add file information
                file_info = get_project_files(proj['file_location'])
                proj.update(file_info)
                
                # Add absolute file location
                abs_path = os.path.abspath(proj['file_location'])
                proj['abs_file_location'] = abs_path
                proj['abs_file_location_url'] = abs_path.replace("\\", "/")
                
                if file_info['most_recent']:
                    proj['view_file_path'] = file_info['most_recent']['rel_path']
                    proj['view_file_type'] = file_info['most_recent']['type']
                else:
                    proj['view_file_path'] = None
                    proj['view_file_type'] = None

                processed_results.append(proj)

            return jsonify({'results': processed_results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<uuid>', methods=['GET'])
def get_project(uuid):
    """Get a specific project by UUID"""
    try:
        with engine.connect() as conn:
            # Get project details
            project_result = conn.execute(
                select(projects_table).where(projects_table.c.uuid == uuid)
            ).first()
            
            if not project_result:
                return jsonify({'error': 'Project not found'}), 404
            
            project_dict = dict(project_result)
            
            # Get associated areas
            areas_result = conn.execute(
                select(areas_table).where(areas_table.c.project_id == uuid)
            ).fetchall()
            
            areas_list = [dict(area) for area in areas_result]
            project_dict['areas'] = areas_list
            
            # Add file information
            file_info = get_project_files(project_dict['file_location'])
            project_dict.update(file_info)
            
            return jsonify(project_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<uuid>/files', methods=['GET'])
def get_project_files_endpoint(uuid):
    """Get all files for a specific project"""
    try:
        with engine.connect() as conn:
            # Get project file location
            project_result = conn.execute(
                select(projects_table.c.file_location).where(projects_table.c.uuid == uuid)
            ).first()
            
            if not project_result:
                return jsonify({'error': 'Project not found'}), 404
            
            file_location = project_result[0]
            file_info = get_project_files(file_location)
            
            return jsonify(file_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<uuid>', methods=['DELETE'])
def delete_project(uuid):
    """Delete a project and its associated areas"""
    try:
        import shutil
        
        with engine.begin() as conn:
            # Get the file location for this project
            sel = select(projects_table.c.file_location).where(projects_table.c.uuid == uuid)
            result = conn.execute(sel).first()
            
            if result and result[0]:
                folder = result[0]
                if os.path.exists(folder) and os.path.isdir(folder):
                    try:
                        shutil.rmtree(folder)
                    except Exception as e:
                        print(f"Error deleting folder: {e}")
            
            # Delete from database
            proj_result = conn.execute(projects_table.delete().where(projects_table.c.uuid == uuid))
            area_result = conn.execute(areas_table.delete().where(areas_table.c.project_id == uuid))
            
            if proj_result.rowcount == 0:
                return jsonify({'error': 'Project not found'}), 404
            
            return jsonify({
                'message': 'Project deleted successfully',
                'projects_deleted': proj_result.rowcount,
                'areas_deleted': area_result.rowcount
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects', methods=['POST'])
def add_project():
    """Add a new project"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    required_fields = ['project_name', 'user_name', 'date', 'file_location', 'paper_size', 'description']
    missing_fields = [f for f in required_fields if f not in data]
    
    if missing_fields:
        return jsonify({'error': f"Missing fields: {', '.join(missing_fields)}"}), 400
    
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
                        return jsonify({'error': f"Missing area fields: {', '.join(area_missing_fields)}"}), 400
                    
                    conn.execute(areas_table.insert().values(
                        project_id=generated_uuid,
                        xmin=area_data['xmin'],
                        ymin=area_data['ymin'],
                        xmax=area_data['xmax'],
                        ymax=area_data['ymax'],
                        scale=area_data['scale']
                    ))
        
        return jsonify({'message': 'Project added successfully', 'uuid': generated_uuid}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/get_new_uuid', methods=['POST'])
def get_new_uuid():
    """Generate a new unique UUID"""
    try:
        # Use the reusable UUID generation function
        generated_uuid = generate_unique_uuid()
        return jsonify({"uuid": generated_uuid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/user_names', methods=['GET'])
def get_user_names():
    """Get all unique user names"""
    try:
        with engine.connect() as conn:
            user_names = [row[0] for row in conn.execute(select(projects_table.c.user_name).distinct())]
            return jsonify({'user_names': user_names})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
