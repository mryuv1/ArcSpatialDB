from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'sqlite:///elements.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

def print_table(table, session_or_conn, label):
    print(f'\n{label}:')
    rows = session_or_conn.execute(table.select()).fetchall()
    if rows:
        for row in rows:
            props = ', '.join(f"{col}={getattr(row, col)}" for col in table.columns.keys())
            print(f"  {props}")
    else:
        print(f'  No {label} found.')

# Reflect tables
try:
    elements_table = Table('elements', metadata, autoload_with=engine)
    print_table(elements_table, session, 'elements')
except Exception as e:
    print('Could not reflect or print elements table:', e)

try:
    areas_table = Table('areas', metadata, autoload_with=engine)
    print_table(areas_table, session, 'areas')
except Exception as e:
    print('Could not reflect or print areas table:', e)

try:
    projects_table = Table('projects', metadata, autoload_with=engine)
    with engine.connect() as conn:
        print_table(projects_table, conn, 'projects')
except Exception as e:
    print('Could not reflect or print projects table:', e)

session.close() 