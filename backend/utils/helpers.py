def parse_point(s):
    """
    Parse coordinate string with support for various separators and formats.
    Supports: '/', ',', ':', ';', '|', ' ', '\t', '\\', and combinations
    Also handles WGS84 format and other coordinate system prefixes
    Handles complex formats like:
    - WGS84 UTM 36N 735712 E / 3563829 N
    - WGS84 Geo 35° 30' 0.11" E / 32° 11' 9.88" N
    
    Returns: (x, y) if successful, or (None, error_message) if failed
    """
    import re
    try:
        s = str(s).strip()
        
        # Check for empty or whitespace-only input
        if not s:
            return None, "Empty coordinate string provided"
        
        # Handle complex WGS84 UTM format: "WGS84 UTM 36N 735712 E / 3563829 N"
        if 'WGS84 UTM' in s.upper():
            # Pattern: WGS84 UTM [zone][N/S] [easting] [E/W] / [northing] [N/S]
            utm_pattern = r'WGS84\s+UTM\s+(\d+[NS])\s+(\d+)\s*[EW]\s*/\s*(\d+)\s*[NS]'
            match = re.search(utm_pattern, s, re.IGNORECASE)
            if match:
                try:
                    zone = match.group(1)
                    easting = float(match.group(2))
                    northing = float(match.group(3))
                    return (easting, northing), None
                except ValueError as e:
                    return None, f"Invalid UTM coordinates in '{s}': {str(e)}"
            else:
                return None, f"Invalid WGS84 UTM format. Expected: 'WGS84 UTM [zone][N/S] [easting] [E/W] / [northing] [N/S]'"
        
        # Handle complex WGS84 Geographic format: "WGS84 Geo 35° 30' 0.11" E / 32° 11' 9.88" N"
        if 'WGS84 GEO' in s.upper():
            # Pattern: WGS84 Geo [deg]° [min]' [sec]" [E/W] / [deg]° [min]' [sec]" [N/S]
            geo_pattern = r'WGS84\s+GEO\s+(\d+)°\s*(\d+)\'\s*([\d.]+)"\s*[EW]\s*/\s*(\d+)°\s*(\d+)\'\s*([\d.]+)"\s*[NS]'
            match = re.search(geo_pattern, s, re.IGNORECASE)
            if match:
                try:
                    # Convert DMS to decimal degrees
                    lon_deg, lon_min, lon_sec = float(match.group(1)), float(match.group(2)), float(match.group(3))
                    lat_deg, lat_min, lat_sec = float(match.group(4)), float(match.group(5)), float(match.group(6))
                    
                    # Check if longitude is East or West
                    if 'W' in s.upper():
                        lon_deg = -lon_deg
                    if 'S' in s.upper():
                        lat_deg = -lat_deg
                    
                    # Convert to decimal degrees
                    lon_decimal = lon_deg + (lon_min / 60) + (lon_sec / 3600)
                    lat_decimal = lat_deg + (lat_min / 60) + (lat_sec / 3600)
                    
                    return (lon_decimal, lat_decimal), None
                except ValueError as e:
                    return None, f"Invalid geographic coordinates in '{s}': {str(e)}"
            else:
                return None, f"Invalid WGS84 Geographic format. Expected: 'WGS84 Geo [deg]° [min]' [sec]\" [E/W] / [deg]° [min]' [sec]\" [N/S]'"
        
        # Handle simple WGS84 and other coordinate system prefixes
        if s.upper().startswith(('WGS', 'EPSG', 'UTM', 'GEO', 'PROJ')):
            # Extract coordinates after the prefix
            # Look for common patterns like "WGS84: 123.456, 789.012" or "UTM 36N: 123456, 789012"
            # Match coordinates after any prefix
            coord_match = re.search(r'[:\s]+([-\d.,\s]+)$', s)
            if coord_match:
                s = coord_match.group(1).strip()
            else:
                return None, f"Invalid coordinate system format. Expected: '[SYSTEM]: [x], [y]' or '[SYSTEM] [x], [y]'"
        
        # Remove any parentheses, brackets, or quotes
        s = s.strip('()[]{}"\'\'')
        
        # Try multiple separators in order of preference
        separators = ['/', ',', ':', ';', '|', '\\', '\t']
        
        # First try exact separators
        for sep in separators:
            if sep in s:
                parts = s.split(sep, 1)  # Split only on first occurrence
                if len(parts) == 2:
                    x_str, y_str = parts[0].strip(), parts[1].strip()
                    # Try to convert to float
                    try:
                        return (float(x_str), float(y_str)), None
                    except ValueError:
                        continue
        
        # If no separator found, try splitting on whitespace
        if ' ' in s:
            parts = s.split()
            if len(parts) >= 2:
                try:
                    return (float(parts[0]), float(parts[1])), None
                except ValueError:
                    pass
        
        # Try regex pattern for coordinates with optional spaces and various separators
        # Pattern: number, optional spaces, separator, optional spaces, number
        coord_pattern = r'([-+]?\d*\.?\d+)\s*[\/,:;|\t\\]\s*([-+]?\d*\.?\d+)'
        match = re.search(coord_pattern, s)
        if match:
            try:
                return (float(match.group(1)), float(match.group(2))), None
            except ValueError:
                pass
        
        # Try pattern for coordinates separated by whitespace
        space_pattern = r'([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)'
        match = re.search(space_pattern, s)
        if match:
            try:
                return (float(match.group(1)), float(match.group(2))), None
            except ValueError:
                pass
        
        # If we get here, no valid format was found
        return None, f"Invalid coordinate format: '{s}'. Expected formats: 'x,y', 'x/y', 'x:y', 'WGS84 UTM 36N 735712 E / 3563829 N', 'WGS84 Geo 35° 30' 0.11\" E / 32° 11' 9.88\" N', etc."
    except Exception as e:
        return None, f"Error parsing coordinates '{s}': {str(e)}"

def parse_point_simple(s):
    """
    Simple wrapper for backwards compatibility - returns only coordinates or None
    """
    result = parse_point(s)
    if result[0] is not None:
        return result[0]
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
