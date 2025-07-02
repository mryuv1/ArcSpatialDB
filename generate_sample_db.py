from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Define the SQLite database file
DATABASE_URL = 'sqlite:///elements.db'

# Set up SQLAlchemy base and engine
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

# Define the Element model
class Element(Base):
    __tablename__ = 'elements'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    directory = Column(String, nullable=False)
    areas = relationship('Area', back_populates='element', cascade='all, delete-orphan')

class Area(Base):
    __tablename__ = 'areas'
    id = Column(Integer, primary_key=True)
    element_id = Column(Integer, ForeignKey('elements.id'), nullable=False)
    xmin = Column(Float, nullable=False)  # Bottom Left X
    ymin = Column(Float, nullable=False)  # Bottom Left Y
    xmax = Column(Float, nullable=False)  # Top Right X
    ymax = Column(Float, nullable=False)  # Top Right Y
    element = relationship('Element', back_populates='areas')

# Create tables
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# Sample data with realistic coordinates
sample_elements = [
    {
        'name': 'ProjectA',
        'directory': '/projects/a',
        'areas': [
            {'xmin': 732387.349494434, 'ymin': 3595538.730993807, 'xmax': 740294.943002, 'ymax': 3601127.26183221}
        ]
    },
    {
        'name': 'ProjectB',
        'directory': '/projects/b',
        'areas': [
            {'xmin': 732400.5778397045, 'ymin': 3595595.882709242, 'xmax': 740308.1713472705, 'ymax': 3601184.413547645},
            {'xmin': 741000.000000, 'ymin': 3600000.000000, 'xmax': 742000.000000, 'ymax': 3602000.000000}
        ]
    },
    {
        'name': 'ProjectC',
        'directory': '/projects/c',
        'areas': [
            {'xmin': 733000.123456, 'ymin': 3596000.654321, 'xmax': 734000.654321, 'ymax': 3599000.123456}
        ]
    },
    {
        'name': 'ProjectD',
        'directory': '/projects/d',
        'areas': [
            {'xmin': 735000.000000, 'ymin': 3598000.000000, 'xmax': 736000.000000, 'ymax': 3600000.000000},
            {'xmin': 737000.000000, 'ymin': 3600500.000000, 'xmax': 738000.000000, 'ymax': 3601500.000000}
        ]
    },
    {
        'name': 'ProjectE',
        'directory': '/projects/e',
        'areas': [
            {'xmin': 739000.000000, 'ymin': 3601000.000000, 'xmax': 740000.000000, 'ymax': 3602000.000000}
        ]
    },
]

# Insert data
for elem in sample_elements:
    element = Element(name=elem['name'], directory=elem['directory'])
    for area in elem['areas']:
        element.areas.append(Area(**area))
    session.add(element)
session.commit()

# Print summary
print('\nDatabase contents:')
for element in session.query(Element).all():
    print(f"Element: {element.name}, Directory: {element.directory}")
    for area in element.areas:
        print(f"  Area: Bottom Left ({area.xmin}, {area.ymin}), Top Right ({area.xmax}, {area.ymax})")

session.close() 