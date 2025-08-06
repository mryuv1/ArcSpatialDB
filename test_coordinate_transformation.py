#!/usr/bin/env python3
"""
Test script for coordinate transformation functionality.
This script tests the parse_point function with various coordinate formats
and verifies that they are all transformed to UTM format.
"""

import sys
import os

# Add the current directory to the path so we can import from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the parse_point function from app.py
from app import parse_point, transform_to_utm, dms_to_decimal

def test_coordinate_transformation():
    """Test coordinate transformation with various formats"""
    
    print("🧪 Testing Coordinate Transformation to UTM")
    print("=" * 50)
    
    # Test cases with different coordinate formats
    test_cases = [
        # Simple numeric formats
        ("123.456, 789.012", "Simple comma-separated"),
        ("123.456/789.012", "Simple slash-separated"),
        ("123.456:789.012", "Simple colon-separated"),
        ("123.456 789.012", "Simple space-separated"),
        
        # WGS84 Geographic coordinates
        ("35.5, 32.2", "WGS84 decimal degrees"),
        ("WGS84: 35.5, 32.2", "WGS84 with prefix"),
        ("EPSG:4326: 35.5, 32.2", "EPSG:4326 format"),
        
        # Complex WGS84 Geographic format (DMS)
        ("WGS84 Geo 35° 30' 0.11\" E / 32° 11' 9.88\" N", "WGS84 DMS format"),
        ("WGS84 Geo 35° 30' 0\" E / 32° 11' 0\" N", "WGS84 DMS format (simplified)"),
        
        # UTM coordinates (should remain as-is)
        ("WGS84 UTM 36N 735712 E / 3563829 N", "WGS84 UTM format"),
        ("UTM 36N: 735712, 3563829", "UTM with prefix"),
        
        # Other coordinate systems
        ("EPSG:3857: 1234567, 8901234", "Web Mercator"),
        ("EPSG:32636: 735712, 3563829", "UTM Zone 36N (EPSG)"),
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for test_input, description in test_cases:
        print(f"\n📝 Testing: {description}")
        print(f"   Input: {test_input}")
        
        try:
            result, error_msg = parse_point(test_input)
            
            if error_msg is not None:
                print(f"   ❌ Error: {error_msg}")
            else:
                x_utm, y_utm = result
                print(f"   ✅ Success: ({x_utm:.2f}, {y_utm:.2f})")
                successful_tests += 1
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("🎉 All coordinate transformation tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return successful_tests == total_tests

def test_transformation_functions():
    """Test the individual transformation functions"""
    
    print("\n🧪 Testing Individual Transformation Functions")
    print("=" * 50)
    
    # Test DMS to decimal conversion
    print("\n📝 Testing DMS to Decimal conversion:")
    test_dms = [
        (35, 30, 0.11, 'E', "35° 30' 0.11\" E"),
        (32, 11, 9.88, 'N', "32° 11' 9.88\" N"),
        (35, 30, 0, 'W', "35° 30' 0\" W"),
        (32, 11, 0, 'S', "32° 11' 0\" S"),
    ]
    
    for deg, min, sec, direction, description in test_dms:
        decimal = dms_to_decimal(deg, min, sec, direction)
        print(f"   {description} → {decimal:.6f}")
    
    # Test UTM transformation
    print("\n📝 Testing UTM transformation:")
    test_coords = [
        (35.5, 32.2, "EPSG:4326", "WGS84 Geographic"),
        (35.5, 32.2, None, "WGS84 Geographic (default)"),
    ]
    
    for x, y, crs, description in test_coords:
        x_utm, y_utm, utm_epsg = transform_to_utm(x, y, crs)
        print(f"   {description}: ({x}, {y}) → UTM EPSG:{utm_epsg}: ({x_utm:.2f}, {y_utm:.2f})")

if __name__ == "__main__":
    print("🚀 Starting Coordinate Transformation Tests")
    print("=" * 50)
    
    # Test individual functions
    test_transformation_functions()
    
    # Test full coordinate parsing and transformation
    success = test_coordinate_transformation()
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 