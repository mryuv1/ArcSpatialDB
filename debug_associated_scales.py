#!/usr/bin/env python3
"""
Comprehensive debug script for associated_scales issue
"""

import sqlite3
from sqlalchemy import create_engine, select, func, distinct
from sqlalchemy import MetaData, Table, Column, String, Integer, Float, ForeignKey

# Database setup
DATABASE_URL = 'sqlite:///elements.db'
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define tables
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
    Column('scale', Float, nullable=False)
)

def debug_associated_scales():
    """Debug the associated_scales query"""
    print("🔍 Debugging associated_scales query...")
    
    with engine.connect() as conn:
        # First, let's see what's in the database
        print("\n📊 Current database contents:")
        
        # Check projects
        projects_result = conn.execute(select(projects_table)).fetchall()
        print(f"Projects: {len(projects_result)}")
        for proj in projects_result:
            print(f"  - {proj.project_name} (UUID: {proj.uuid})")
        
        # Check areas
        areas_result = conn.execute(select(areas_table)).fetchall()
        print(f"Areas: {len(areas_result)}")
        for area in areas_result:
            print(f"  - Project: {area.project_id}, Scale: {area.scale}")
        
        # Test the actual query that's used in the app
        print("\n🔍 Testing the associated_scales query:")
        
        projects_join_stmt = projects_table.outerjoin(areas_table, projects_table.c.uuid == areas_table.c.project_id)
        
        projects_base_query = select(
            projects_table.c.uuid,
            projects_table.c.project_name,
            projects_table.c.user_name,
            projects_table.c.date,
            projects_table.c.file_location,
            projects_table.c.paper_size,
            projects_table.c.description,
            func.group_concat(distinct(areas_table.c.scale)).label('associated_scales')
        ).select_from(projects_join_stmt).group_by(
            projects_table.c.uuid,
            projects_table.c.project_name,
            projects_table.c.user_name,
            projects_table.c.date,
            projects_table.c.file_location,
            projects_table.c.paper_size,
            projects_table.c.description
        )
        
        try:
            result = conn.execute(projects_base_query).fetchall()
            
            print(f"Query results: {len(result)}")
            for row in result:
                print(f"  - Project: {row.project_name}")
                print(f"    UUID: {row.uuid}")
                print(f"    Associated Scales: '{row.associated_scales}'")
                print(f"    Type of associated_scales: {type(row.associated_scales)}")
                print(f"    Raw row: {row}")
                print()
                
                # Test the row_to_dict function
                try:
                    if hasattr(row, '_mapping'):
                        row_dict = dict(row._mapping)
                    else:
                        row_dict = dict(row)
                    print(f"    Row as dict: {row_dict}")
                    print(f"    'associated_scales' in dict: {'associated_scales' in row_dict}")
                    print(f"    associated_scales value: {row_dict.get('associated_scales', 'NOT_FOUND')}")
                except Exception as e:
                    print(f"    Error converting to dict: {e}")
                print()
                
        except Exception as e:
            print(f"Error executing query: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_associated_scales() 