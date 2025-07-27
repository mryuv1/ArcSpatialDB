/**
 * Parse coordinate string with support for various separators and formats.
 * Supports: '/', ',', ':', ';', '|', ' ', '\t', '\\', and combinations
 * Also handles WGS84 format and other coordinate system prefixes
 * Handles complex formats like:
 * - WGS84 UTM 36N 735712 E / 3563829 N
 * - WGS84 Geo 35° 30' 0.11" E / 32° 11' 9.88" N
 * 
 * Returns: [x, y] if successful, or [null, error_message] if failed
 */
function parsePoint(s) {
    try {
        s = String(s).trim();
        
        // Check for empty or whitespace-only input
        if (!s) {
            return [null, "Empty coordinate string provided"];
        }
        
        // Handle complex WGS84 UTM format: "WGS84 UTM 36N 735712 E / 3563829 N"
        if (s.toUpperCase().includes('WGS84 UTM')) {
            // Pattern: WGS84 UTM [zone][N/S] [easting] [E/W] / [northing] [N/S]
            const utmPattern = /WGS84\s+UTM\s+(\d+[NS])\s+(\d+)\s*[EW]\s*\/\s*(\d+)\s*[NS]/i;
            const match = s.match(utmPattern);
            if (match) {
                try {
                    const zone = match[1];
                    const easting = parseFloat(match[2]);
                    const northing = parseFloat(match[3]);
                    return [[easting, northing], null];
                } catch (e) {
                    return [null, `Invalid UTM coordinates in '${s}': ${e.message}`];
                }
            } else {
                return [null, "Invalid WGS84 UTM format. Expected: 'WGS84 UTM [zone][N/S] [easting] [E/W] / [northing] [N/S]'"];
            }
        }
        
        // Handle complex WGS84 Geographic format: "WGS84 Geo 35° 30' 0.11" E / 32° 11' 9.88" N"
        if (s.toUpperCase().includes('WGS84 GEO')) {
            // Pattern: WGS84 Geo [deg]° [min]' [sec]" [E/W] / [deg]° [min]' [sec]" [N/S]
            const geoPattern = /WGS84\s+GEO\s+(\d+)°\s*(\d+)'\s*([\d.]+)"\s*[EW]\s*\/\s*(\d+)°\s*(\d+)'\s*([\d.]+)"\s*[NS]/i;
            const match = s.match(geoPattern);
            if (match) {
                try {
                    // Convert DMS to decimal degrees
                    let lonDeg = parseFloat(match[1]);
                    const lonMin = parseFloat(match[2]);
                    const lonSec = parseFloat(match[3]);
                    let latDeg = parseFloat(match[4]);
                    const latMin = parseFloat(match[5]);
                    const latSec = parseFloat(match[6]);
                    
                    // Check if longitude is East or West
                    if (s.toUpperCase().includes('W')) {
                        lonDeg = -lonDeg;
                    }
                    if (s.toUpperCase().includes('S')) {
                        latDeg = -latDeg;
                    }
                    
                    // Convert to decimal degrees
                    const lonDecimal = lonDeg + (lonMin / 60) + (lonSec / 3600);
                    const latDecimal = latDeg + (latMin / 60) + (latSec / 3600);
                    
                    return [[lonDecimal, latDecimal], null];
                } catch (e) {
                    return [null, `Invalid geographic coordinates in '${s}': ${e.message}`];
                }
            } else {
                return [null, "Invalid WGS84 Geographic format. Expected: 'WGS84 Geo [deg]° [min]' [sec]\" [E/W] / [deg]° [min]' [sec]\" [N/S]'"];
            }
        }
        
        // Handle simple WGS84 and other coordinate system prefixes
        const upperS = s.toUpperCase();
        if (upperS.startsWith('WGS') || upperS.startsWith('EPSG') || upperS.startsWith('UTM') || 
            upperS.startsWith('GEO') || upperS.startsWith('PROJ')) {
            // Extract coordinates after the prefix
            // Look for common patterns like "WGS84: 123.456, 789.012" or "UTM 36N: 123456, 789012"
            const coordMatch = s.match(/[:\s]+([-\d.,\s]+)$/);
            if (coordMatch) {
                s = coordMatch[1].trim();
            } else {
                return [null, "Invalid coordinate system format. Expected: '[SYSTEM]: [x], [y]' or '[SYSTEM] [x], [y]'"];
            }
        }
        
        // Remove any parentheses, brackets, or quotes
        s = s.replace(/^[\(\)\[\]{}\"']+|[\(\)\[\]{}\"']+$/g, '');
        
        // Try multiple separators in order of preference
        const separators = ['/', ',', ':', ';', '|', '\\', '\t'];
        
        // First try exact separators
        for (const sep of separators) {
            if (s.includes(sep)) {
                const parts = s.split(sep, 2); // Split only on first occurrence
                if (parts.length === 2) {
                    const xStr = parts[0].trim();
                    const yStr = parts[1].trim();
                    // Try to convert to float
                    try {
                        const x = parseFloat(xStr);
                        const y = parseFloat(yStr);
                        if (!isNaN(x) && !isNaN(y)) {
                            return [[x, y], null];
                        }
                    } catch (e) {
                        continue;
                    }
                }
            }
        }
        
        // If no separator found, try splitting on whitespace
        if (s.includes(' ')) {
            const parts = s.split(/\s+/);
            if (parts.length >= 2) {
                try {
                    const x = parseFloat(parts[0]);
                    const y = parseFloat(parts[1]);
                    if (!isNaN(x) && !isNaN(y)) {
                        return [[x, y], null];
                    }
                } catch (e) {
                    // Continue to other patterns
                }
            }
        }
        
        // Try regex pattern for coordinates with optional spaces and various separators
        // Pattern: number, optional spaces, separator, optional spaces, number
        const coordPattern = /([-+]?\d*\.?\d+)\s*[\/,:;|\t\\]\s*([-+]?\d*\.?\d+)/;
        let match = s.match(coordPattern);
        if (match) {
            try {
                const x = parseFloat(match[1]);
                const y = parseFloat(match[2]);
                if (!isNaN(x) && !isNaN(y)) {
                    return [[x, y], null];
                }
            } catch (e) {
                // Continue to other patterns
            }
        }
        
        // Try pattern for coordinates separated by whitespace
        const spacePattern = /([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)/;
        match = s.match(spacePattern);
        if (match) {
            try {
                const x = parseFloat(match[1]);
                const y = parseFloat(match[2]);
                if (!isNaN(x) && !isNaN(y)) {
                    return [[x, y], null];
                }
            } catch (e) {
                // Continue
            }
        }
        
        // If we get here, no valid format was found
        return [null, `Invalid coordinate format: '${s}'. Expected formats: 'x,y', 'x/y', 'x:y', 'WGS84 UTM 36N 735712 E / 3563829 N', 'WGS84 Geo 35° 30' 0.11" E / 32° 11' 9.88" N', etc.`];
    } catch (e) {
        return [null, `Error parsing coordinates '${s}': ${e.message}`];
    }
}

/**
 * Simple wrapper for backwards compatibility - returns only coordinates or null
 */
function parsePointSimple(s) {
    const result = parsePoint(s);
    if (result[0] !== null) {
        return result[0];
    }
    return null;
}

/**
 * Calculate the area size in square meters using UTM coordinates
 */
function calculateAreaSize(xmin, ymin, xmax, ymax) {
    const width = Math.abs(xmax - xmin);
    const height = Math.abs(ymax - ymin);
    return width * height;
}

/**
 * Calculate the percentage of area that overlaps with the query rectangle
 */
function calculateOverlapPercentage(areaXmin, areaYmin, areaXmax, areaYmax, queryXmin, queryYmin, queryXmax, queryYmax) {
    // Calculate intersection
    const intersectXmin = Math.max(areaXmin, queryXmin);
    const intersectYmin = Math.max(areaYmin, queryYmin);
    const intersectXmax = Math.min(areaXmax, queryXmax);
    const intersectYmax = Math.min(areaYmax, queryYmax);

    // Check if there's an intersection
    if (intersectXmin >= intersectXmax || intersectYmin >= intersectYmax) {
        return 0.0;
    }

    // Calculate areas
    const areaSize = (areaXmax - areaXmin) * (areaYmax - areaYmin);
    const intersectSize = (intersectXmax - intersectXmin) * (intersectYmax - intersectYmin);

    if (areaSize === 0) {
        return 0.0;
    }

    return (intersectSize / areaSize) * 100.0;
}

/**
 * Convert DD/MM/YYYY format to database format (DD-MM-YY) for comparison
 */
function convertDateToDbFormat(dateStr) {
    try {
        if (dateStr && dateStr.includes('/')) { // DD/MM/YYYY format
            const [day, month, year] = dateStr.split('/');
            // Convert to DD-MM-YY format for database comparison
            return `${day.padStart(2, '0')}-${month.padStart(2, '0')}-${year.slice(2)}`;
        } else if (dateStr && dateStr.includes('-')) { // DD-MM-YY format (already correct)
            return dateStr;
        }
        return dateStr;
    } catch (e) {
        return dateStr;
    }
}

module.exports = {
    parsePoint,
    parsePointSimple,
    calculateAreaSize,
    calculateOverlapPercentage,
    convertDateToDbFormat
};
