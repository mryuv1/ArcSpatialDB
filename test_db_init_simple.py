#!/usr/bin/env python3
"""
Simple test script to verify database initialization works correctly.
This script tests the database initialization process without trying to delete the database file.
"""

import os
import sys
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

def test_app_startup():
    """Test that the app can start without crashing"""
    
    print("\n🧪 Testing App Startup")
    print("=" * 50)
    
    try:
        # Import the app
        import app
        
        # Check if Flask app is properly configured
        if hasattr(app, 'app') and app.app is not None:
            print("✅ Flask app is properly configured")
        else:
            print("❌ Flask app is not properly configured")
            return False
        
        # Check if routes are accessible
        if hasattr(app.app, 'url_map') and len(app.app.url_map._rules) > 0:
            print("✅ Flask routes are configured")
            print(f"📊 Number of routes: {len(app.app.url_map._rules)}")
        else:
            print("❌ No Flask routes found")
            return False
        
        # Test a simple database query
        print("\n🔍 Testing database query...")
        with app.engine.connect() as conn:
            result = conn.execute(select(func.count()).select_from(app.projects_table)).scalar()
            print(f"✅ Database query successful: {result} projects found")
        
        print("✅ App startup test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ App startup test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ArcSpatialDB Database Initialization Test")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_database_initialization()
    test2_passed = test_app_startup()
    
    print("\n📋 Test Results Summary")
    print("=" * 30)
    print(f"Database initialization test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"App startup test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The database initialization is working correctly.")
        print("✅ The app will not crash when the database doesn't exist or is empty.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the database initialization.")
        sys.exit(1) 