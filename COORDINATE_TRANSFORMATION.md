# Coordinate Transformation to UTM

This document explains how the coordinate transformation functionality works in the ArcSpatialDB application.

## Overview

The application now automatically transforms all coordinate formats to UTM (Universal Transverse Mercator) format, similar to how the `db_manager.pyt` ArcGIS tool does it. This ensures consistent coordinate handling across the entire system.

## How It Works

### 1. **Transformation Process**

All coordinates go through the following process:

1. **Parse**: Extract coordinates from various input formats
2. **Identify Source CRS**: Determine the source coordinate reference system
3. **Transform to WGS84**: Convert to WGS84 Geographic (EPSG:4326)
4. **Calculate UTM Zone**: Determine appropriate UTM zone based on longitude/latitude
5. **Transform to UTM**: Convert to UTM coordinates in the appropriate zone

### 2. **Supported Input Formats**

The system accepts coordinates in these formats:

#### **Simple Numeric Formats**
```
123.456, 789.012    # Comma-separated
123.456/789.012      # Slash-separated
123.456:789.012      # Colon-separated
123.456 789.012      # Space-separated
```

#### **Coordinate System Prefixes**
```
WGS84: 35.5, 32.2                    # WGS84 Geographic
EPSG:4326: 35.5, 32.2                # WGS84 Geographic (EPSG)
EPSG:3857: 1234567, 8901234          # Web Mercator
EPSG:32636: 735712, 3563829          # UTM Zone 36N (EPSG)
UTM 36N: 735712, 3563829             # UTM with zone prefix
```

#### **Complex WGS84 Formats**
```
WGS84 UTM 36N 735712 E / 3563829 N  # UTM format (stays as-is)
WGS84 Geo 35° 30' 0.11" E / 32° 11' 9.88" N  # DMS format
```

### 3. **UTM Zone Calculation**

The system automatically calculates the appropriate UTM zone:

```python
zone_number = int((longitude + 180) / 6) + 1
is_northern = latitude >= 0
utm_epsg = 32600 + zone_number if is_northern else 32700 + zone_number
```

- **Northern Hemisphere**: EPSG 32601-32660
- **Southern Hemisphere**: EPSG 32701-32760

### 4. **Dependencies**

The transformation requires the `pyproj` library:

```bash
pip install pyproj==3.6.1
```

If `pyproj` is not available, the system will:
- Show a warning message
- Continue without transformation (coordinates used as-is)
- Still parse various formats but won't transform them

## Implementation Details

### **Key Functions**

#### `transform_to_utm(x, y, source_crs=None)`
- Transforms coordinates to UTM format
- Uses pyproj for coordinate transformations
- Returns `(x_utm, y_utm, utm_epsg)` or `(x, y, None)` if transformation fails

#### `dms_to_decimal(degrees, minutes, seconds, direction)`
- Converts degrees, minutes, seconds to decimal degrees
- Handles North/South and East/West directions

#### `parse_point(s)`
- Parses coordinate strings in various formats
- Automatically transforms all coordinates to UTM
- Returns `(x_utm, y_utm)` or `(None, error_message)`

### **Error Handling**

The system gracefully handles:
- Missing pyproj library
- Invalid coordinate formats
- Transformation failures
- Unsupported coordinate systems

## Testing

Run the test script to verify the transformation functionality:

```bash
python test_coordinate_transformation.py
```

This will test various coordinate formats and verify they're all transformed to UTM.

## Comparison with db_manager.pyt

| Feature | db_manager.pyt (ArcPy) | app.py (pyproj) |
|---------|------------------------|------------------|
| **Library** | ArcPy (ArcGIS only) | pyproj (cross-platform) |
| **Transformation** | ✅ Full CRS support | ✅ Full CRS support |
| **UTM Zone** | ✅ Automatic calculation | ✅ Automatic calculation |
| **DMS Support** | ✅ Manual conversion | ✅ Manual conversion |
| **Error Handling** | ✅ Comprehensive | ✅ Comprehensive |

## Usage Examples

### **In the Web Application**

When users input coordinates in the search form:

```python
# Input: "35.5, 32.2" (WGS84 Geographic)
# Output: (735712.45, 3563829.12) (UTM Zone 36N)

# Input: "WGS84 Geo 35° 30' 0" E / 32° 11' 0" N"
# Output: (735712.45, 3563829.12) (UTM Zone 36N)

# Input: "WGS84 UTM 36N 735712 E / 3563829 N"
# Output: (735712.0, 3563829.0) (stays as-is)
```

### **In the API**

The same transformation applies to API endpoints:

```python
# POST /api/add_project
{
    "areas": [
        {
            "xmin": 35.5,  # Will be transformed to UTM
            "ymin": 32.2,  # Will be transformed to UTM
            "xmax": 35.6,
            "ymax": 32.3,
            "scale": "1:1000"
        }
    ]
}
```

## Benefits

1. **Consistency**: All coordinates are stored in UTM format
2. **Accuracy**: Proper coordinate system transformations
3. **Flexibility**: Accepts multiple input formats
4. **Compatibility**: Works with existing ArcGIS workflows
5. **Reliability**: Graceful fallback when transformations fail

## Troubleshooting

### **Common Issues**

1. **pyproj not installed**
   ```
   ⚠️  pyproj not available. Coordinate transformation will be disabled.
   Install with: pip install pyproj
   ```

2. **Invalid coordinate format**
   ```
   Error: Invalid coordinate format: 'invalid'. Expected formats: 'x,y', 'x/y', ...
   ```

3. **Transformation failure**
   ```
   ⚠️  Coordinate transformation failed: [error details]
   ```

### **Solutions**

1. Install pyproj: `pip install pyproj==3.6.1`
2. Check coordinate format syntax
3. Verify coordinate system is supported by pyproj
4. Check that coordinates are within valid ranges

## Future Enhancements

- Support for more coordinate systems
- Custom UTM zone selection
- Coordinate validation and bounds checking
- Performance optimization for bulk transformations 