import sqlite3
import os

def fix_database():
    """Fix file paths in the database to use relative paths and update some user names"""
    
    # Connect to the database
    conn = sqlite3.connect('elements.db')
    cursor = conn.cursor()
    
    # Define the mapping for user name changes
    user_name_changes = {
        'Yoav': {
            'first': 'Yoav',
            'second': 'Yoav', 
            'third': 'Yoav',
            'another_one': 'Sarah',
            'last_one': 'Sarah',
            'A3_test': 'Michael',
            'custom_size': 'Michael',
            'CustomSizeCorrect': 'Lisa',
            'A3_correct': 'Lisa'
        }
    }
    
    try:
        # Get all projects
        cursor.execute("SELECT uuid, project_name, user_name, file_location FROM projects")
        projects = cursor.fetchall()
        
        print("Current projects in database:")
        for project in projects:
            uuid, project_name, user_name, file_location = project
            print(f"  {uuid}: {project_name} by {user_name} at {file_location}")
        
        print("\nUpdating projects...")
        
        # Update each project
        for project in projects:
            uuid, project_name, user_name, file_location = project
            
            # Fix file location to use relative path
            new_file_location = f"sampleDataset/{project_name}"
            
            # Update user name based on mapping
            new_user_name = user_name_changes.get(user_name, {}).get(project_name, user_name)
            
            # Update the database
            cursor.execute("""
                UPDATE projects 
                SET file_location = ?, user_name = ?
                WHERE uuid = ?
            """, (new_file_location, new_user_name, uuid))
            
            print(f"  Updated {project_name}:")
            print(f"    File location: {file_location} -> {new_file_location}")
            print(f"    User name: {user_name} -> {new_user_name}")
        
        # Commit the changes
        conn.commit()
        
        print("\nVerifying changes...")
        
        # Verify the changes
        cursor.execute("SELECT uuid, project_name, user_name, file_location FROM projects")
        updated_projects = cursor.fetchall()
        
        print("Updated projects:")
        for project in updated_projects:
            uuid, project_name, user_name, file_location = project
            print(f"  {uuid}: {project_name} by {user_name} at {file_location}")
        
        print(f"\nSuccessfully updated {len(projects)} projects!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database() 