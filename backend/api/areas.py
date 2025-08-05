from flask import Blueprint, jsonify, request
from sqlalchemy import select, func, and_
from models.database import engine, areas_table, projects_table
from utils.file_utils import get_project_files
import os

areas_bp = Blueprint('areas', __name__)

@areas_bp.route('/areas', methods=['GET'])
def get_all_areas():
    """Get all areas with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filters
        filters = {}
        filters['id_filter'] = request.args.get('id_filter', '', type=str)
        filters['project_id_filter'] = request.args.get('project_id_filter', '', type=str)
        filters['xmin_filter'] = request.args.get('xmin_filter', '', type=str)
        filters['ymin_filter'] = request.args.get('ymin_filter', '', type=str)
        filters['xmax_filter'] = request.args.get('xmax_filter', '', type=str)
        filters['ymax_filter'] = request.args.get('ymax_filter', '', type=str)
        filters['scale_filter'] = request.args.get('scale_filter', '', type=str)
        
        query_filters = []
        if filters['id_filter']:
            try:
                id_val = int(filters['id_filter'])
                query_filters.append(areas_table.c.id == id_val)
            except ValueError:
                query_filters.append(areas_table.c.id == -1)
        if filters['project_id_filter']:
            query_filters.append(areas_table.c.project_id.ilike(f"%{filters['project_id_filter']}%"))
        if filters['xmin_filter']:
            try:
                xmin_val = float(filters['xmin_filter'])
                query_filters.append(areas_table.c.xmin == xmin_val)
            except ValueError:
                query_filters.append(areas_table.c.xmin == -1)
        if filters['ymin_filter']:
            try:
                ymin_val = float(filters['ymin_filter'])
                query_filters.append(areas_table.c.ymin == ymin_val)
            except ValueError:
                query_filters.append(areas_table.c.ymin == -1)
        if filters['xmax_filter']:
            try:
                xmax_val = float(filters['xmax_filter'])
                query_filters.append(areas_table.c.xmax == xmax_val)
            except ValueError:
                query_filters.append(areas_table.c.xmax == -1)
        if filters['ymax_filter']:
            try:
                ymax_val = float(filters['ymax_filter'])
                query_filters.append(areas_table.c.ymax == ymax_val)
            except ValueError:
                query_filters.append(areas_table.c.ymax == -1)
        if filters['scale_filter']:
            try:
                # Try to parse as float for backward compatibility
                scale_val = float(filters['scale_filter'])
                query_filters.append(areas_table.c.scale == str(scale_val))
            except ValueError:
                # If not a number, treat as string scale format
                query_filters.append(areas_table.c.scale.ilike(f"%{filters['scale_filter']}%"))

        with engine.connect() as conn:
            # Get total count for areas pagination
            count_stmt = select(func.count()).select_from(areas_table)
            if query_filters:
                count_stmt = count_stmt.where(and_(*query_filters))
            total_items = conn.execute(count_stmt).scalar_one()

            total_pages = (total_items + per_page - 1) // per_page
            if page > total_pages and total_pages > 0:
                page = total_pages
            elif total_pages == 0:
                page = 1

            # Query areas for the current page with filters, joined with projects to get file location
            stmt = select(
                areas_table.c.id, 
                areas_table.c.project_id, 
                areas_table.c.xmin, 
                areas_table.c.ymin, 
                areas_table.c.xmax, 
                areas_table.c.ymax, 
                areas_table.c.scale, 
                projects_table.c.file_location.label('project_file_location')
            )
            stmt = stmt.select_from(areas_table.join(projects_table, areas_table.c.project_id == projects_table.c.uuid))
            
            if query_filters:
                stmt = stmt.where(and_(*query_filters))
            
            stmt = stmt.limit(per_page).offset((page - 1) * per_page)
            areas = conn.execute(stmt).fetchall()

            # Add file information for areas (show files of associated project)
            areas_list = []
            for area in areas:
                area_dict = dict(area)
                project_file_location = area_dict['project_file_location']
                
                # Add file information
                file_info = get_project_files(project_file_location)
                area_dict['project_all_files'] = file_info['all_files']
                area_dict['project_file_count'] = file_info['file_count']
                
                # Add absolute file location
                abs_path = os.path.abspath(project_file_location)
                area_dict['project_abs_file_location'] = abs_path
                
                if file_info['most_recent']:
                    area_dict['project_view_file_path'] = file_info['most_recent']['rel_path']
                    area_dict['project_view_file_type'] = file_info['most_recent']['type']
                else:
                    area_dict['project_view_file_path'] = None
                    area_dict['project_view_file_type'] = None

                areas_list.append(area_dict)

            return jsonify({
                'areas': areas_list,
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
