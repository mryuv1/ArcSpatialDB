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
    description = Column(String, nullable=True)
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

def commit_to_the_db(project_name, user_name, date, file_location, paper_size, info_per_map_frame, description):
    DATABASE_URL = f'sqlite:///{DB_PATH}'
    engine = create_engine(DATABASE_URL, echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    # Generate unique ID
    unique_id = str(uuid.uuid4())[:8]
    while session.query(Project).filter(Project.uuid == unique_id).first():
        unique_id = str(uuid.uuid4())[:8]
    project = Project(
    uuid=unique_id,
    project_name=project_name,
    description=description,
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
    return unique_id
    
def convert_any_to_wgs84_utm(x, y, spatial_ref=None):
    """
    Convert (x, y) from any spatial reference to WGS84 UTM.
    If spatial_ref is None, assumes input is WGS84 Geographic (EPSG:4326).
    Returns: (x_utm, y_utm, utm_epsg)
    """
    # Fallback to WGS84 GEO if spatial_ref is None
    if spatial_ref is None:
        spatial_ref = arcpy.SpatialReference(4326)

    try:
        point = arcpy.PointGeometry(arcpy.Point(x, y), spatial_ref)
    except Exception as e:
        raise RuntimeError(f"Failed to create PointGeometry: {e}")

    try:
        point_geo = point.projectAs(arcpy.SpatialReference(4326))  # Ensure in WGS84 GEO
    except Exception as e:
        raise RuntimeError(f"Failed to project to WGS84: {e}")

    lon, lat = point_geo.centroid.X, point_geo.centroid.Y

    # Compute UTM zone and hemisphere
    zone_number = int((lon + 180) / 6) + 1
    is_northern = lat >= 0
    utm_epsg = 32600 + zone_number if is_northern else 32700 + zone_number

    try:
        utm_ref = arcpy.SpatialReference(utm_epsg)
        point_utm = point_geo.projectAs(utm_ref)
    except Exception as e:
        raise RuntimeError(f"Failed to project to UTM EPSG:{utm_epsg}: {e}")

    return point_utm.centroid.X, point_utm.centroid.Y, utm_epsg




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
        param2b = arcpy.Parameter(
            displayName="Description",
            name="description",
            datatype="GPString",
            parameterType="Optional",
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

        return [param0, param1, param2, param2b, param3, param4, param5, param6, param7]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        layout_name = parameters[0].value
        dpi = parameters[5].value or 300
        export_format = parameters[4].value

        # Enable JPEG quality if format is JPEG
        parameters[6].enabled = (export_format == "JPEG")

        # Calculate image size from layout page size
        if layout_name:
            layout = next((lyt for lyt in aprx.listLayouts() if lyt.name == layout_name), None)
            if layout:
                width_inch = layout.pageWidth
                height_inch = layout.pageHeight
                width_px = int(round(width_inch * dpi / 25.4))
                height_px = int(round(height_inch * dpi / 25.4))
                parameters[7].enabled = True
                parameters[7].value = f"Height: {height_px} Width: {width_px}"

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        layout_name = parameters[0].valueAsText
        export_folder = parameters[1].valueAsText
        export_name = parameters[2].valueAsText.strip().replace(" ", "_")
        export_format = parameters[4].valueAsText.upper()
        dpi = int(parameters[5].value or 300)
        description = parameters[3].valueAsText if parameters[3].value else ""

        try:
            quality = int(parameters[6].value)
        except (TypeError, ValueError):
            messages.addWarningMessage("Invalid JPEG quality value. Using default (80).")
            quality = 80

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        layout = next((lyt for lyt in aprx.listLayouts() if lyt.name == layout_name), None)
        if not layout:
            raise Exception(f"Layout '{layout_name}' not found.")

        # Create new export directory
        export_subfolder = os.path.join(export_folder, export_name)
        os.makedirs(export_subfolder, exist_ok=True)

        # Report map extents
        map_frames = layout.listElements("MAPFRAME_ELEMENT")
        info_per_map_frame = []
        if not map_frames:
            messages.addWarningMessage("No map frames found.")
        else:
            for mf in map_frames:
                extent = mf.camera.getExtent()
                spatial_ref = extent.spatialReference  # original CRS
                messages.addMessage(f"Map Frame '{mf.name}', spatial_ref: {spatial_ref}")
                messages.addMessage(f"Map Frame '{mf.name}', X/Y original: {extent.XMin}, {extent.YMin}")
                # Convert corners to UTM
                x_min_utm, y_min_utm, utm_epsg = convert_any_to_wgs84_utm(extent.XMin, extent.YMin, spatial_ref)
                x_max_utm, y_max_utm, _ = convert_any_to_wgs84_utm(extent.XMax, extent.YMax, spatial_ref)

                messages.addMessage(f"Map Frame '{mf.name}' in WGS84 UTM (EPSG:{utm_epsg}):")
                messages.addMessage(f"  Bottom Left (XMin, YMin): ({x_min_utm}, {y_min_utm})")
                messages.addMessage(f"  Top Right  (XMax, YMax): ({x_max_utm}, {y_max_utm})")
                scale = mf.camera.scale
                messages.addMessage(f"Map Frame '{mf.name}' Scale: 1:{int(scale)}")
                scale_str = f"Scale: 1:{int(scale)}"
                info_dict = {
                    "scale": scale_str,
                    "x_min": int(x_min_utm),
                    "y_min": int(y_min_utm),
                    "x_max": int(x_max_utm),
                    "y_max": int(y_max_utm)
                }
                info_per_map_frame.append(info_dict)
                messages.addMessage(f"{info_dict['x_min']}")
                

        # Export layout
        export_file = os.path.join(export_subfolder, f"{export_name}.{export_format.lower()}")
        # commit to the SQL DB
        paper_size = detect_paper_size(layout.pageWidth, layout.pageHeight)
        messages.addMessage(f"{paper_size}")
        username = getpass.getuser()
        messages.addMessage(f"{username}")
        current_date = datetime.now().strftime("%d-%m-%y")
        messages.addMessage(f"{current_date}")
        unique_id = commit_to_the_db(export_name, username, current_date, export_subfolder, paper_size, info_per_map_frame, description)
        messages.addMessage(f"Export ID: {unique_id}")
        # Update text element with export ID
        text_elements = layout.listElements("TEXT_ELEMENT")
        id_text = next((el for el in text_elements if el.name == "ExportID"), None)
        if id_text:
            id_text.text = f"Export ID: {unique_id}"
        else:
            messages.addWarningMessage("No text element named 'ExportID' found on layout.")
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
        open_after_export = bool(parameters[8].value)
        if open_after_export:
            try:
                os.startfile(export_file)
                messages.addMessage(f"Opened exported file: {export_file}")
            except Exception as e:
                messages.addWarningMessage(f"Failed to open file automatically: {e}")

