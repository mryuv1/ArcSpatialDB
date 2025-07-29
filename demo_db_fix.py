#!/usr/bin/env python3
"""
Demonstration script showing the database initialization fix.
This script shows how the app now handles empty or missing databases gracefully.
"""

import os
import shutil
import tempfile
from sqlalchemy import create_engine, MetaData, select, func

def demo_database_fix():
    """Demonstrate the database initialization fix"""
    
    print("🚀 ArcSpatialDB Database Initialization Fix Demo")
    print("=" * 60)
    
    # Step 1: Show current state
    print("\n📊 Step 1: Current Database State")
    print("-" * 40)
    
    if os.path.exists('elements.db'):
        print("✅ Database file exists")
        file_size = os.path.getsize('elements.db')
        print(f"📁 File size: {file_size} bytes")
        
        # Count current records
        engine = create_engine('sqlite:///elements.db')
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        with engine.connect() as conn:
            if 'projects' in metadata.tables:
                projects_count = conn.execute(select(func.count()).select_from(metadata.tables['projects'])).scalar()
                print(f"📋 Projects: {projects_count}")
            
            if 'areas' in metadata.tables:
                areas_count = conn.execute(select(func.count()).select_from(metadata.tables['areas'])).scalar()
                print(f"📋 Areas: {areas_count}")
    else:
        print("❌ Database file does not exist")
    
    # Step 2: Create a backup
    print("\n📦 Step 2: Creating Backup")
    print("-" * 40)
    
    backup_file = 'elements.db.backup'
    if os.path.exists('elements.db'):
        shutil.copy2('elements.db', backup_file)
        print(f"✅ Backup created: {backup_file}")
    else:
        print("⚠️ No database to backup")
    
    # Step 3: Remove the database
    print("\n🗑️ Step 3: Removing Database")
    print("-" * 40)
    
    if os.path.exists('elements.db'):
        os.remove('elements.db')
        print("✅ Database file removed")
    else:
        print("⚠️ Database file was already missing")
    
    # Step 4: Test app import (this should create the database)
    print("\n🔄 Step 4: Testing App Import")
    print("-" * 40)
    
    try:
        print("📥 Importing app module...")
        import app
        print("✅ App imported successfully!")
        
        # Check if database was created
        if os.path.exists('elements.db'):
            print("✅ Database file was created automatically")
            file_size = os.path.getsize('elements.db')
            print(f"📁 New file size: {file_size} bytes")
        else:
            print("❌ Database file was not created")
            return False
        
        # Check if tables were created
        engine = create_engine('sqlite:///elements.db')
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        tables_created = True
        if 'projects' not in metadata.tables:
            print("❌ 'projects' table was not created")
            tables_created = False
        else:
            print("✅ 'projects' table was created")
        
        if 'areas' not in metadata.tables:
            print("❌ 'areas' table was not created")
            tables_created = False
        else:
            print("✅ 'areas' table was created")
        
        if not tables_created:
            return False
        
        # Check if sample data was added
        with engine.connect() as conn:
            projects_count = conn.execute(select(func.count()).select_from(metadata.tables['projects'])).scalar()
            areas_count = conn.execute(select(func.count()).select_from(metadata.tables['areas'])).scalar()
            
            print(f"📊 Projects in new database: {projects_count}")
            print(f"📊 Areas in new database: {areas_count}")
            
            if projects_count > 0:
                print("✅ Sample data was added automatically")
            else:
                print("⚠️ No sample data was added")
        
        # Test a simple query
        print("\n🔍 Step 5: Testing Database Query")
        print("-" * 40)
        
        try:
            with app.engine.connect() as conn:
                result = conn.execute(select(func.count()).select_from(app.projects_table)).scalar()
                print(f"✅ Database query successful: {result} projects found")
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            return False
        
        print("\n🎉 Step 6: Demo Completed Successfully!")
        print("-" * 40)
        print("✅ The app now handles empty/missing databases gracefully")
        print("✅ Database and tables are created automatically")
        print("✅ Sample data is added if the database is empty")
        print("✅ The app will not crash when the database doesn't exist")
        
        return True
        
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False
    
    finally:
        # Step 7: Restore backup
        print("\n🔄 Step 7: Restoring Original Database")
        print("-" * 40)
        
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, 'elements.db')
            os.remove(backup_file)
            print("✅ Original database restored")
        else:
            print("⚠️ No backup to restore")

if __name__ == "__main__":
    success = demo_database_fix()
    
    if success:
        print("\n🎉 DEMO SUCCESSFUL!")
        print("The database initialization fix is working correctly.")
        print("Your app will no longer crash when the database is empty or missing.")
    else:
        print("\n❌ DEMO FAILED!")
        print("There may still be issues with the database initialization.") 