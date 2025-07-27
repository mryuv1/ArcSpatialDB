/**
 * Parse a point string in format 'X/Y' or 'X,Y' and return [x, y] coordinates
 */
function parsePoint(s) {
    try {
        s = s.trim();
        let coords;
        if (s.includes('/')) {
            coords = s.split('/');
        } else if (s.includes(',')) {
            coords = s.split(',');
        } else {
            return null;
        }
        return [parseFloat(coords[0]), parseFloat(coords[1])];
    } catch (e) {
        return null;
    }
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
    calculateAreaSize,
    calculateOverlapPercentage,
    convertDateToDbFormat
};
