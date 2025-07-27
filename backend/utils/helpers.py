def parse_point(s):
    """Parse a point string in format 'X/Y' or 'X,Y' and return (x, y) coordinates"""
    try:
        s = s.strip()
        if '/' in s:
            x_str, y_str = s.split('/')
        elif ',' in s:
            x_str, y_str = s.split(',')
        else:
            return None
        return float(x_str), float(y_str)
    except Exception:
        return None

def calculate_area_size(xmin, ymin, xmax, ymax):
    """Calculate the area size in square meters using UTM coordinates"""
    width = abs(xmax - xmin)
    height = abs(ymax - ymin)
    return width * height

def calculate_overlap_percentage(area_xmin, area_ymin, area_xmax, area_ymax, query_xmin, query_ymin, query_xmax, query_ymax):
    """Calculate the percentage of area that overlaps with the query rectangle"""
    # Calculate intersection
    intersect_xmin = max(area_xmin, query_xmin)
    intersect_ymin = max(area_ymin, query_ymin)
    intersect_xmax = min(area_xmax, query_xmax)
    intersect_ymax = min(area_ymax, query_ymax)

    # Check if there's an intersection
    if intersect_xmin >= intersect_xmax or intersect_ymin >= intersect_ymax:
        return 0.0

    # Calculate areas
    area_size = (area_xmax - area_xmin) * (area_ymax - area_ymin)
    intersect_size = (intersect_xmax - intersect_xmin) * (intersect_ymax - intersect_ymin)

    if area_size == 0:
        return 0.0

    return (intersect_size / area_size) * 100.0

def convert_date_to_db_format(date_str):
    """Convert DD/MM/YYYY format to database format (DD-MM-YY) for comparison"""
    try:
        if date_str and '/' in date_str:  # DD/MM/YYYY format
            day, month, year = date_str.split('/')
            # Convert to DD-MM-YY format for database comparison
            return f"{day.zfill(2)}-{month.zfill(2)}-{year[2:]}"
        elif date_str and '-' in date_str:  # DD-MM-YY format (already correct)
            return date_str
        return None
    except:
        return None
