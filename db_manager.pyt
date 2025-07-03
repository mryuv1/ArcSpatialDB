import arcpy
import uuid
import os
import getpass
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DB_NAME = "elements.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)
Base = declarative_base()
class Project(Base):
    __tablename__ = 'projects'
    uuid = Column(String, primary_key=True)
    project_name = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    date = Column(String, nullable=False)  # ISO format
    file_location = Column(String, nullable=False)
    paper_size = Column(String, nullable=False)
    areas = relationship('Area', back_populates='project', cascade='all, delete-orphan')

class Area(Base):
    __tablename__ = 'areas'
    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey('projects.uuid'), nullable=False)
    xmin = Column(Float, nullable=False)
    ymin = Column(Float, nullable=False)
    xmax = Column(Float, nullable=False)
    ymax = Column(Float, nullable=False)
    scale = Column(String, nullable=False)
    project = relationship('Project', back_populates='areas')

def detect_paper_size(width_mm, height_mm, tolerance=2):
    common_sizes = {
        "A0": (841, 1189),
        "A1": (594, 841),
        "A2": (420, 594),
        "A3": (297, 420),
        "A4": (210, 297),
        "A5": (148, 210),
        "B0": (1000, 1414),
    }

    for name, (w, h) in common_sizes.items():
        if (abs(width_mm - w) <= tolerance and abs(height_mm - h) <= tolerance) or \
           (abs(width_mm - h) <= tolerance and abs(height_mm - w) <= tolerance):
            orientation = "Portrait" if height_mm >= width_mm else "Landscape"
            return f"{name} ({orientation})"

    return f"Custom Size: Height: {height_mm / 1000} cm, Width: {width_mm / 1000} cm"

def commit_to_the_db(project_id, project_name, user_name, date, file_location, paper_size, info_per_map_frame):
    DATABASE_URL = f'sqlite:///{DB_PATH}'
    engine = create_engine(DATABASE_URL, echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    project = Project(
    uuid=project_id,
    project_name=project_name,
    user_name=user_name,
    date=date,
    file_location=file_location,
    paper_size=paper_size,
    )
    for info in info_per_map_frame:
        area = Area(
        xmin=info['x_min'],
        ymin=info['y_min'],
        xmax=info['x_max'],
        ymax=info['y_max'],
        scale=info['scale']
        )
        project.areas.append(area)
    session.add(project)
    session.commit()
    session.close()


class Toolbox(object):
    def __init__(self):
        self.label = "Export Layout With Unique ID"
        self.alias = "ExportLayoutID"
        self.tools = [ExportLayoutTool]

class ExportLayoutTool(object):
    def __init__(self):
        self.label = "Export Layout With ID"
        self.description = "Exports layout with a custom name, adds a unique ID, saves a copy of the project, and reports map extents."
        self.canRunInBackground = False

    def getParameterInfo(self):
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        layout_names = [lyt.name for lyt in aprx.listLayouts()]

        # Layout dropdown
        param0 = arcpy.Parameter(
            displayName="Layout",
            name="layout_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param0.filter.list = layout_names
        if layout_names:
            param0.value = layout_names[0]

        # Output folder
        param1 = arcpy.Parameter(
            displayName="Export Folder",
            name="export_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )

        # Export Name (used for folder and file names)
        param2 = arcpy.Parameter(
            displayName="Export Name",
            name="export_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        # Export format
        param3 = arcpy.Parameter(
            displayName="Export Format",
            name="export_format",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param3.filter.list = ["PDF", "PNG", "JPEG"]
        param3.value = "PDF"

        # DPI
        param4 = arcpy.Parameter(
            displayName="DPI (Dots Per Inch)",
            name="dpi",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
        )
        param4.value = 300

        # JPEG quality (0–100)
        param5 = arcpy.Parameter(
            displayName="JPEG quality (%)",
            name="jpeg_quality",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
        )
        param5.filter.type = "Range"
        param5.filter.list = [1, 100]
        param5.value = 80
        param5.enabled = False

        param6 = arcpy.Parameter(
            displayName="Output Image Size (pixels)",
            name="image_size",
            datatype="GPString",
            parameterType="Output",
            direction="Input"
        )
        param6.enabled = False
        param6.value = ""

        # Open exported file after export
        param7 = arcpy.Parameter(
            displayName="Open Exported File After Export?",
            name="open_after_export",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )
        param7.value = False  # Default is off

        return [param0, param1, param2, param3, param4, param5, param6, param7]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        layout_name = parameters[0].value
        dpi = parameters[4].value or 300
        export_format = parameters[3].value

        # Enable JPEG quality if format is JPEG
        parameters[5].enabled = (export_format == "JPEG")

        # Calculate image size from layout page size
        if layout_name:
            layout = next((lyt for lyt in aprx.listLayouts() if lyt.name == layout_name), None)
            if layout:
                width_inch = layout.pageWidth
                height_inch = layout.pageHeight
                width_px = int(round(width_inch * dpi / 25.4))
                height_px = int(round(height_inch * dpi / 25.4))
                parameters[6].enabled = True
                parameters[6].value = f"Height: {height_px} Width: {width_px}"

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        layout_name = parameters[0].valueAsText
        export_folder = parameters[1].valueAsText
        export_name = parameters[2].valueAsText.strip().replace(" ", "_")
        export_format = parameters[3].valueAsText.upper()
        dpi = int(parameters[4].value or 300)

        try:
            quality = int(parameters[5].value)
        except (TypeError, ValueError):
            messages.addWarningMessage("Invalid JPEG quality value. Using default (80).")
            quality = 80

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        layout = next((lyt for lyt in aprx.listLayouts() if lyt.name == layout_name), None)
        if not layout:
            raise Exception(f"Layout '{layout_name}' not found.")

        # Generate unique ID
        unique_id = str(uuid.uuid4())[:8]
        messages.addMessage(f"Export ID: {unique_id}")

        # Create new export directory
        export_subfolder = os.path.join(export_folder, export_name)
        os.makedirs(export_subfolder, exist_ok=True)

        # Update text element with export ID
        text_elements = layout.listElements("TEXT_ELEMENT")
        id_text = next((el for el in text_elements if el.name == "ExportID"), None)
        if id_text:
            id_text.text = f"Export ID: {unique_id}"
        else:
            messages.addWarningMessage("No text element named 'ExportID' found on layout.")

        # Report map extents
        map_frames = layout.listElements("MAPFRAME_ELEMENT")
        info_per_map_frame = []
        if not map_frames:
            messages.addWarningMessage("No map frames found.")
        else:
            for mf in map_frames:
                extent = mf.camera.getExtent()
                bottom_left = (extent.XMin, extent.YMin)
                top_right = (extent.XMax, extent.YMax)
                
                messages.addMessage(f"Map Frame '{mf.name}':")
                messages.addMessage(f"  Bottom Left (XMin, YMin): {bottom_left}")
                messages.addMessage(f"  Top Right  (XMax, YMax): {top_right}")
                scale = mf.camera.scale
                messages.addMessage(f"Map Frame '{mf.name}' Scale: 1:{int(scale)}")
                scale_str = f"Scale: 1:{int(scale)}"
                x_min = extent.XMin
                y_min = extent.YMin
                x_max = extent.XMax
                y_max = extent.YMax
                info_dict = {"scale":scale_str, "x_min": x_min ,"x_max": x_max,"y_min": y_min,"y_max": y_max}
                info_per_map_frame.append(info_dict)
                

        # Export layout
        export_file = os.path.join(export_subfolder, f"{export_name}.{export_format.lower()}")
            
        if export_format == "PDF":
            layout.exportToPDF(export_file, resolution=dpi)
        elif export_format == "PNG":
            layout.exportToPNG(export_file, resolution=dpi)
        elif export_format == "JPEG":
            export_file = os.path.join(export_subfolder, f"{export_name}")
            layout.exportToJPEG(export_file, resolution=dpi, jpeg_quality=quality)
        else:
            raise Exception("Unsupported export format.")

        messages.addMessage(f"Exported layout to: {export_file}")

        # Save project copy
        aprx_copy = os.path.join(export_subfolder, f"{export_name}.aprx")
        aprx.saveACopy(aprx_copy)
        messages.addMessage(f"Saved project copy as: {aprx_copy}")
        paper_size = detect_paper_size(layout.pageWidth, layout.pageHeight)
        messages.addMessage(f"{paper_size}")
        username = getpass.getuser()
        messages.addMessage(f"{username}")
        current_date = datetime.now().strftime("%d-%m-%y")
        messages.addMessage(f"{current_date}")
        open_after_export = bool(parameters[7].value)
        if open_after_export:
            try:
                os.startfile(export_file)
                messages.addMessage(f"Opened exported file: {export_file}")
            except Exception as e:
                messages.addWarningMessage(f"Failed to open file automatically: {e}")
        # commit to the SQL DB
        commit_to_the_db(unique_id, export_name, username, current_date, export_subfolder, paper_size, info_per_map_frame)
