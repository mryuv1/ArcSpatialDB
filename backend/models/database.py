from sqlalchemy import create_engine, MetaData, Table

# Database configuration
import os
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'elements.db')
DATABASE_URL = f'sqlite:///{DB_PATH}'
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Reflect tables from existing database
projects_table = Table('projects', metadata, autoload_with=engine)
areas_table = Table('areas', metadata, autoload_with=engine)
