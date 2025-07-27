const express = require('express');
const database = require('../models/database');
const { getProjectFiles } = require('../utils/fileUtils');

const router = express.Router();

router.get('/areas', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const perPage = parseInt(req.query.per_page) || 10;
        
        // Filters
        const filters = {
            idFilter: req.query.id_filter || '',
            projectIdFilter: req.query.project_id_filter || '',
            xminFilter: req.query.xmin_filter || '',
            yminFilter: req.query.ymin_filter || '',
            xmaxFilter: req.query.xmax_filter || '',
            ymaxFilter: req.query.ymax_filter || '',
            scaleFilter: req.query.scale_filter || ''
        };

        let whereConditions = [];
        let params = [];

        // Build WHERE conditions
        if (filters.idFilter) {
            const idVal = parseInt(filters.idFilter);
            if (!isNaN(idVal)) {
                whereConditions.push('a.id = ?');
                params.push(idVal);
            } else {
                whereConditions.push('a.id = ?');
                params.push(-1); // Invalid condition to return no results
            }
        }
        if (filters.projectIdFilter) {
            whereConditions.push('a.project_id LIKE ?');
            params.push(`%${filters.projectIdFilter}%`);
        }
        if (filters.xminFilter) {
            const xminVal = parseFloat(filters.xminFilter);
            if (!isNaN(xminVal)) {
                whereConditions.push('a.xmin = ?');
                params.push(xminVal);
            } else {
                whereConditions.push('a.xmin = ?');
                params.push(-1); // Invalid condition
            }
        }
        if (filters.yminFilter) {
            const yminVal = parseFloat(filters.yminFilter);
            if (!isNaN(yminVal)) {
                whereConditions.push('a.ymin = ?');
                params.push(yminVal);
            } else {
                whereConditions.push('a.ymin = ?');
                params.push(-1); // Invalid condition
            }
        }
        if (filters.xmaxFilter) {
            const xmaxVal = parseFloat(filters.xmaxFilter);
            if (!isNaN(xmaxVal)) {
                whereConditions.push('a.xmax = ?');
                params.push(xmaxVal);
            } else {
                whereConditions.push('a.xmax = ?');
                params.push(-1); // Invalid condition
            }
        }
        if (filters.ymaxFilter) {
            const ymaxVal = parseFloat(filters.ymaxFilter);
            if (!isNaN(ymaxVal)) {
                whereConditions.push('a.ymax = ?');
                params.push(ymaxVal);
            } else {
                whereConditions.push('a.ymax = ?');
                params.push(-1); // Invalid condition
            }
        }
        if (filters.scaleFilter) {
            whereConditions.push('a.scale LIKE ?');
            params.push(`%${filters.scaleFilter}%`);
        }

        const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';
        
        // Get total count for pagination
        const countQuery = `SELECT COUNT(*) as total FROM areas a ${whereClause}`;
        const countResult = await database.get(countQuery, params);
        const totalItems = countResult.total;
        const totalPages = Math.ceil(totalItems / perPage);

        if (page > totalPages && totalPages > 0) {
            return res.status(400).json({
                error: 'Page number exceeds total pages',
                total_pages: totalPages,
                current_page: page
            });
        }

        // Main query with pagination
        const offset = (page - 1) * perPage;
        const query = `
            SELECT 
                a.*,
                p.project_name,
                p.file_location
            FROM areas a
            LEFT JOIN projects p ON a.project_id = p.uuid
            ${whereClause}
            ORDER BY a.id
            LIMIT ? OFFSET ?
        `;
        const queryParams = [...params, perPage, offset];

        const areas = await database.all(query, queryParams);

        // Enhance areas with file information
        const enhancedAreas = [];
        for (const area of areas) {
            try {
                if (area.file_location) {
                    const fileInfo = getProjectFiles(area.file_location);
                    enhancedAreas.push({
                        ...area,
                        file_count: fileInfo.file_count,
                        most_recent_file: fileInfo.most_recent,
                        all_files: fileInfo.all_files,
                        // Add frontend-expected properties
                        project_all_files: fileInfo.all_files,
                        project_file_location: area.file_location
                    });
                } else {
                    enhancedAreas.push({
                        ...area,
                        file_count: 0,
                        most_recent_file: null,
                        all_files: [],
                        // Add frontend-expected properties
                        project_all_files: [],
                        project_file_location: area.file_location || ''
                    });
                }
            } catch (error) {
                console.warn(`Error getting file info for area ${area.id}:`, error.message);
                enhancedAreas.push({
                    ...area,
                    file_count: 0,
                    most_recent_file: null,
                    all_files: [],
                    // Add frontend-expected properties
                    project_all_files: [],
                    project_file_location: area.file_location || ''
                });
            }
        }

        res.json({
            areas: enhancedAreas,
            pagination: {
                page: page,
                per_page: perPage,
                total_items: totalItems,
                total_pages: totalPages,
                has_prev: page > 1,
                has_next: page < totalPages
            },
            filters: filters
        });

    } catch (error) {
        console.error('Error in get_all_areas:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.get('/areas/:id', async (req, res) => {
    try {
        const id = parseInt(req.params.id);
        
        if (isNaN(id)) {
            return res.status(400).json({ error: 'Invalid area ID' });
        }

        const query = `
            SELECT 
                a.*,
                p.project_name,
                p.file_location
            FROM areas a
            LEFT JOIN projects p ON a.project_id = p.uuid
            WHERE a.id = ?
        `;

        const area = await database.get(query, [id]);
        
        if (!area) {
            return res.status(404).json({ error: 'Area not found' });
        }

        // Get file information
        try {
            if (area.file_location) {
                const fileInfo = getProjectFiles(area.file_location);
                area.file_count = fileInfo.file_count;
                area.most_recent_file = fileInfo.most_recent;
                area.all_files = fileInfo.all_files;
                // Add frontend-expected properties
                area.project_all_files = fileInfo.all_files;
                area.project_file_location = area.file_location;
            } else {
                area.file_count = 0;
                area.most_recent_file = null;
                area.all_files = [];
                // Add frontend-expected properties
                area.project_all_files = [];
                area.project_file_location = '';
            }
        } catch (error) {
            console.warn(`Error getting file info for area ${id}:`, error.message);
            area.file_count = 0;
            area.most_recent_file = null;
            area.all_files = [];
            // Add frontend-expected properties
            area.project_all_files = [];
            area.project_file_location = area.file_location || '';
        }

        res.json(area);

    } catch (error) {
        console.error('Error in get_area:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

module.exports = router;
