#!/usr/bin/env python3
"""
Test script for the enhanced coordinate parsing function.
Demonstrates support for various separators and coordinate formats.
"""

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
    try:
        s = str(s).strip()
        
        # Check for empty or whitespace-only input
        if not s:
            return None, "Empty coordinate string provided"
        
        # Handle complex WGS84 UTM format: "WGS84 UTM 36N 735712 E / 3563829 N"
        if 'WGS84 UTM' in s.upper():
            import re
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
            import re
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
            import re
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
        import re
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

def test_coordinate_parsing():
    """Test the enhanced coordinate parsing function with various formats."""
    
    test_cases = [
        # Basic separators
        ("123.456/789.012", "Forward slash"),
        ("123.456,789.012", "Comma"),
        ("123.456:789.012", "Colon"),
        ("123.456;789.012", "Semicolon"),
        ("123.456|789.012", "Pipe"),
        ("123.456\\789.012", "Backslash"),
        ("123.456\t789.012", "Tab"),
        
        # With spaces
        ("123.456 / 789.012", "Forward slash with spaces"),
        ("123.456 , 789.012", "Comma with spaces"),
        ("123.456 : 789.012", "Colon with spaces"),
        ("123.456 ; 789.012", "Semicolon with spaces"),
        ("123.456 | 789.012", "Pipe with spaces"),
        ("123.456 \\ 789.012", "Backslash with spaces"),
        
        # Whitespace separated
        ("123.456 789.012", "Space separated"),
        ("123.456\t789.012", "Tab separated"),
        
        # With parentheses and brackets
        ("(123.456, 789.012)", "Parentheses with comma"),
        ("[123.456, 789.012]", "Brackets with comma"),
        ("{123.456, 789.012}", "Braces with comma"),
        ("(123.456/789.012)", "Parentheses with slash"),
        
        # With quotes
        ("\"123.456, 789.012\"", "Double quotes"),
        ("'123.456, 789.012'", "Single quotes"),
        
        # Coordinate system prefixes
        ("WGS84: 123.456, 789.012", "WGS84 prefix with colon"),
        ("WGS84 123.456, 789.012", "WGS84 prefix with space"),
        ("UTM 36N: 123456, 789012", "UTM prefix with colon"),
        ("EPSG:4326 123.456, 789.012", "EPSG prefix"),
        ("GEO: 123.456, 789.012", "GEO prefix"),
        ("PROJ: 123.456, 789.012", "PROJ prefix"),
        
        # Complex WGS84 UTM format (from the image)
        ("WGS84 UTM 36N 735712 E / 3563829 N", "WGS84 UTM format with zone"),
        ("WGS84 UTM 36S 735712 E / 3563829 S", "WGS84 UTM format southern hemisphere"),
        ("WGS84 UTM 36N 735712 W / 3563829 N", "WGS84 UTM format with West"),
        
        # Complex WGS84 Geographic format (from the image)
        ("WGS84 Geo 35° 30' 0.11\" E / 32° 11' 9.88\" N", "WGS84 Geo DMS format"),
        ("WGS84 Geo 35° 30' 0.11\" W / 32° 11' 9.88\" S", "WGS84 Geo DMS format West/South"),
        ("WGS84 Geo 35° 30' 0\" E / 32° 11' 0\" N", "WGS84 Geo DMS format no seconds"),
        
        # Negative coordinates
        ("-123.456, -789.012", "Negative coordinates"),
        ("-123.456/-789.012", "Negative coordinates with slash"),
        
        # Integer coordinates
        ("123, 789", "Integer coordinates"),
        ("123/789", "Integer coordinates with slash"),
        
        # Mixed formats
        ("123.456,789.012", "No spaces"),
        ("123.456 ,789.012", "Space before comma"),
        ("123.456, 789.012", "Space after comma"),
        ("123.456 , 789.012", "Spaces around comma"),
        
        # Edge cases
        ("0, 0", "Zero coordinates"),
        ("0.0, 0.0", "Zero decimal coordinates"),
        ("123.456789, 789.012345", "High precision"),
        
        # Invalid cases (should return None)
        ("invalid", "Invalid string"),
        ("123.456", "Single number"),
        ("123.456,", "Incomplete coordinates"),
        (", 789.012", "Incomplete coordinates"),
        ("", "Empty string"),
        ("   ", "Whitespace only"),
    ]
    
    print("Testing Enhanced Coordinate Parsing Function")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_input, description in test_cases:
        result, error_msg = parse_point(test_input)
        
        if result is not None:
            x, y = result
            print(f"✅ PASS: {description:30} | Input: '{test_input:20}' | Output: ({x}, {y})")
            passed += 1
        else:
            print(f"❌ FAIL: {description:30} | Input: '{test_input:20}' | Error: {error_msg}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: {passed} passed, {failed} failed")
    print(f"Success rate: {passed/(passed+failed)*100:.1f}%")

if __name__ == "__main__":
    test_coordinate_parsing() 