from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'sqlite:///elements.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

# Reflect tables
elements_table = Table('elements', metadata, autoload_with=engine)
areas_table = Table('areas', metadata, autoload_with=engine)

# Print all elements
elements = session.execute(elements_table.select()).fetchall()
print('All elements:')
if elements:
    for elem in elements:
        print(f"  id={elem.id}, name={elem.name}, directory={elem.directory}")
else:
    print('  No elements found.')

# Print all areas
areas = session.execute(areas_table.select()).fetchall()
print('\nAll areas:')
if areas:
    for area in areas:
        print(f"  id={area.id}, element_id={area.element_id}, Bottom Left=({area.xmin}, {area.ymin}), Top Right=({area.xmax}, {area.ymax})")
else:
    print('  No areas found.')

session.close() 