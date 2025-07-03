from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid as uuid_lib

DATABASE_URL = 'sqlite:///elements.db'
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

class Project(Base):
    __tablename__ = 'projects'
    uuid = Column(String, primary_key=True)
    project_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    date = Column(String, nullable=False)  # ISO format
    file_location = Column(String, nullable=False)
    paper_size = Column(String, nullable=False)
    scale = Column(Float, nullable=False)
    areas = relationship('Area', back_populates='project', cascade='all, delete-orphan')

class Area(Base):
    __tablename__ = 'areas'
    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey('projects.uuid'), nullable=False)
    xmin = Column(Float, nullable=False)
    ymin = Column(Float, nullable=False)
    xmax = Column(Float, nullable=False)
    ymax = Column(Float, nullable=False)
    project = relationship('Project', back_populates='areas')

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

sample_projects = [
    {
        'project_name': 'ProjectA',
        'user_name': 'alice',
        'date': '2024-06-01',
        'file_location': '/projects/a/file1.dwg',
        'paper_size': 'A1',
        'scale': 1.0,
        'areas': [
            {'xmin': 732387.35, 'ymin': 3595538.73, 'xmax': 740294.94, 'ymax': 3601127.26}
        ]
    },
    {
        'project_name': 'ProjectB',
        'user_name': 'bob',
        'date': '2024-06-02',
        'file_location': '/projects/b/file2.dwg',
        'paper_size': 'A2',
        'scale': 0.5,
        'areas': [
            {'xmin': 741000.00, 'ymin': 3600000.00, 'xmax': 742000.00, 'ymax': 3602000.00},
            {'xmin': 732400.57, 'ymin': 3595595.88, 'xmax': 740308.17, 'ymax': 3601184.41}
        ]
    },
    {
        'project_name': 'ProjectC',
        'user_name': 'carol',
        'date': '2024-06-03',
        'file_location': '/projects/c/file3.dwg',
        'paper_size': 'A3',
        'scale': 2.0,
        'areas': [
            {'xmin': 733000.12, 'ymin': 3596000.65, 'xmax': 734000.65, 'ymax': 3599000.12}
        ]
    },
    {
        'project_name': 'ProjectD',
        'user_name': 'dave',
        'date': '2024-06-04',
        'file_location': '/projects/d/file4.dwg',
        'paper_size': 'A0',
        'scale': 1.5,
        'areas': [
            {'xmin': 735000.00, 'ymin': 3598000.00, 'xmax': 736000.00, 'ymax': 3600000.00},
            {'xmin': 737000.00, 'ymin': 3600500.00, 'xmax': 738000.00, 'ymax': 3601500.00}
        ]
    },
    {
        'project_name': 'ProjectE',
        'user_name': 'eve',
        'date': '2024-06-05',
        'file_location': '/projects/e/file5.dwg',
        'paper_size': 'A4',
        'scale': 0.75,
        'areas': [
            {'xmin': 739000.00, 'ymin': 3601000.00, 'xmax': 740000.00, 'ymax': 3602000.00}
        ]
    },
    {
        'project_name': 'ProjectF',
        'user_name': 'frank',
        'date': '2024-06-06',
        'file_location': '/projects/f/file6.dwg',
        'paper_size': 'A2',
        'scale': 1.25,
        'areas': [
            {'xmin': 740500.00, 'ymin': 3603000.00, 'xmax': 741500.00, 'ymax': 3604000.00},
            {'xmin': 742000.00, 'ymin': 3605000.00, 'xmax': 743000.00, 'ymax': 3606000.00},
            {'xmin': 744000.00, 'ymin': 3607000.00, 'xmax': 745000.00, 'ymax': 3608000.00}
        ]
    }
]

for proj in sample_projects:
    project = Project(
        uuid=str(uuid_lib.uuid4()),
        project_name=proj['project_name'],
        user_name=proj['user_name'],
        date=proj['date'],
        file_location=proj['file_location'],
        paper_size=proj['paper_size'],
        scale=proj['scale']
    )
    for area in proj['areas']:
        project.areas.append(Area(**area))
    session.add(project)
session.commit()

print('\nDatabase contents:')
for project in session.query(Project).all():
    print(f"Project: {project.project_name}, User: {project.user_name}, Date: {project.date}, File: {project.file_location}, Paper Size: {project.paper_size}, Scale: {project.scale}")
    for area in project.areas:
        print(f"  Area: id={area.id}, xmin={area.xmin}, ymin={area.ymin}, xmax={area.xmax}, ymax={area.ymax}")

session.close() 