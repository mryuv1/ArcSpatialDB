#!/usr/bin/env python3
"""
Test script to verify database initialization works correctly.
This script tests the database initialization process and ensures the app doesn't crash.
"""

import os
import sys
import sqlite3
from sqlalchemy import create_engine, MetaData, Table, select, func

def test_database_initialization():
    """Test the database initialization process"""
    
    print("🧪 Testing Database Initialization")
    print("=" * 50)
    
    # Test 1: Check if database file exists
    db_file = 'elements.db'
    print(f"📁 Checking database file: {db_file}")
    
    if os.path.exists(db_file):
        print(f"✅ Database file exists: {db_file}")
        file_size = os.path.getsize(db_file)
        print(f"📊 File size: {file_size} bytes")
    else:
        print(f"❌ Database file does not exist: {db_file}")
    
    # Test 2: Try to connect to database
    print("\n🔌 Testing database connection...")
    try:
        engine = create_engine('sqlite:///elements.db')
        with engine.connect() as conn:
            print("✅ Database connection successful")
            
            # Test 3: Check if tables exist
            print("\n📋 Checking database tables...")
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            if 'projects' in metadata.tables:
                print("✅ 'projects' table exists")
                projects_table = metadata.tables['projects']
                
                # Count projects
                result = conn.execute(select(func.count()).select_from(projects_table)).scalar()
                print(f"📊 Number of projects: {result}")
            else:
                print("❌ 'projects' table does not exist")
            
            if 'areas' in metadata.tables:
                print("✅ 'areas' table exists")
                areas_table = metadata.tables['areas']
                
                # Count areas
                result = conn.execute(select(func.count()).select_from(areas_table)).scalar()
                print(f"📊 Number of areas: {result}")
            else:
                print("❌ 'areas' table does not exist")
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 4: Try to import and run the app
    print("\n🚀 Testing app import...")
    try:
        # Import the app module
        import app
        print("✅ App module imported successfully")
        
        # Check if tables are accessible
        if hasattr(app, 'projects_table') and hasattr(app, 'areas_table'):
            print("✅ Table references are available")
        else:
            print("❌ Table references are missing")
            
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False
    
    print("\n🎉 All tests completed successfully!")
    return True

def test_empty_database():
    """Test with a completely empty database"""
    
    print("\n🧪 Testing Empty Database Scenario")
    print("=" * 50)
    
    # Backup existing database if it exists
    db_file = 'elements.db'
    backup_file = 'elements.db.backup'
    
    if os.path.exists(db_file):
        print(f"📦 Backing up existing database to {backup_file}")
        import shutil
        shutil.copy2(db_file, backup_file)
    
    # Remove the database file
    if os.path.exists(db_file):
        os.remove(db_file)
        print("🗑️ Removed existing database file")
    
    # Try to import the app (this should create the database)
    print("🔄 Importing app to create new database...")
    try:
        import app
        print("✅ App imported successfully with empty database")
        
        # Check if database was created
        if os.path.exists(db_file):
            print("✅ Database file was created")
            
            # Check if tables were created
            engine = create_engine('sqlite:///elements.db')
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            if 'projects' in metadata.tables and 'areas' in metadata.tables:
                print("✅ Tables were created successfully")
                
                # Check if sample data was added
                with engine.connect() as conn:
                    projects_count = conn.execute(select(func.count()).select_from(metadata.tables['projects'])).scalar()
                    areas_count = conn.execute(select(func.count()).select_from(metadata.tables['areas'])).scalar()
                    
                    print(f"📊 Projects in new database: {projects_count}")
                    print(f"📊 Areas in new database: {areas_count}")
                    
                    if projects_count > 0:
                        print("✅ Sample data was added successfully")
                    else:
                        print("⚠️ No sample data was added")
            else:
                print("❌ Tables were not created")
        else:
            print("❌ Database file was not created")
            
    except Exception as e:
        print(f"❌ App import failed with empty database: {e}")
        return False
    
    # Restore backup if it existed
    if os.path.exists(backup_file):
        print(f"🔄 Restoring original database from {backup_file}")
        import shutil
        shutil.copy2(backup_file, db_file)
        os.remove(backup_file)
        print("✅ Original database restored")
    
    print("\n🎉 Empty database test completed!")
    return True

if __name__ == "__main__":
    print("🚀 ArcSpatialDB Database Initialization Test")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_database_initialization()
    test2_passed = test_empty_database()
    
    print("\n📋 Test Results Summary")
    print("=" * 30)
    print(f"Database initialization test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Empty database test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The database initialization is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the database initialization.")
        sys.exit(1) 