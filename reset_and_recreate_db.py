#!/usr/bin/env python3
"""
Script to reset and recreate the database with the correct schema but empty.
This will fix the scale column type to String but create an empty database.
"""

import os
import shutil
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, Integer, ForeignKey, select, func

def reset_and_recreate_database():
    """Reset the database and recreate it with correct schema but empty"""
    
    print("🔄 Resetting and recreating database...")
    
    # Backup current database if it exists
    if os.path.exists('elements.db'):
        backup_name = f'elements_backup_{int(os.path.getmtime("elements.db"))}.db'
        shutil.copy2('elements.db', backup_name)
        print(f"📦 Backed up current database to: {backup_name}")
        
        # Remove current database
        os.remove('elements.db')
        print("🗑️ Removed current database")
    
    # Create new database with correct schema
    DATABASE_URL = 'sqlite:///elements.db'
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    
    # Define tables with correct schema
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
        Column('xmin', Integer, nullable=False),
        Column('ymin', Integer, nullable=False),
        Column('xmax', Integer, nullable=False),
        Column('ymax', Integer, nullable=False),
        Column('scale', String, nullable=False)  # String type for scale
    )
    
    # Create tables
    metadata.create_all(engine)
    print("✅ Database tables created with correct schema")
    
    # Verify the empty database
    with engine.connect() as conn:
        projects_count = conn.execute(select(func.count()).select_from(projects_table)).scalar()
        areas_count = conn.execute(select(func.count()).select_from(areas_table)).scalar()
        
        print(f"📊 Database now contains:")
        print(f"   - {projects_count} projects")
        print(f"   - {areas_count} areas")
        
        # Verify schema
        print("\n📋 Database schema:")
        print("   - projects table: uuid, project_name, user_name, date, file_location, paper_size, description")
        print("   - areas table: id, project_id, xmin, ymin, xmax, ymax, scale (String type)")
        print("   - coordinates (xmin, ymin, xmax, ymax) are now Integer type")
    
    print("\n🎉 Database reset and recreated successfully!")
    print("✅ Scale column is now String type (correct)")
    print("✅ Database is empty (no sample data)")
    print("✅ Template should now work correctly")
    print("✅ Ready for real data insertion")

if __name__ == "__main__":
    reset_and_recreate_database() 