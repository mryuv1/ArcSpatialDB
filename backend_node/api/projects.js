const express = require('express');
const database = require('../models/database');
const { parsePoint, calculateAreaSize, convertDateToDbFormat } = require('../utils/helpers');
const { getProjectFiles } = require('../utils/fileUtils');

const router = express.Router();

router.get('/projects', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const perPage = parseInt(req.query.per_page) || 10;
        
        // Filters
        const filters = {
            uuidFilter: req.query.uuid_filter || '',
            projectNameFilter: req.query.project_name_filter || '',
            userNameFilter: req.query.user_name_filter || '',
            dateFilter: req.query.date_filter || '',
            dateFromFilter: req.query.date_from_filter || '',
            dateToFilter: req.query.date_to_filter || '',
            fileLocationFilter: req.query.file_location_filter || '',
            paperSizeFilter: req.query.paper_size_filter || '',
            associatedScalesFilter: req.query.associated_scales_filter || ''
        };

        let whereConditions = [];
        let params = [];

        // Build WHERE conditions
        if (filters.uuidFilter) {
            whereConditions.push('p.uuid LIKE ?');
            params.push(`${filters.uuidFilter}%`);
        }
        if (filters.projectNameFilter) {
            whereConditions.push('p.project_name LIKE ?');
            params.push(`${filters.projectNameFilter}%`);
        }
        if (filters.userNameFilter) {
            whereConditions.push('p.user_name LIKE ?');
            params.push(`${filters.userNameFilter}%`);
        }
        if (filters.dateFilter) {
            whereConditions.push('p.date LIKE ?');
            params.push(`${filters.dateFilter}%`);
        }
        if (filters.fileLocationFilter) {
            whereConditions.push('p.file_location LIKE ?');
            params.push(`${filters.fileLocationFilter}%`);
        }
        if (filters.paperSizeFilter) {
            whereConditions.push('p.paper_size LIKE ?');
            params.push(`${filters.paperSizeFilter}%`);
        }

        const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';
        
        // Base query with aggregated scales
        let baseQuery = `
            SELECT 
                p.uuid,
                p.project_name,
                p.user_name,
                p.date,
                p.file_location,
                p.paper_size,
                p.description,
                GROUP_CONCAT(DISTINCT a.scale) as associated_scales
            FROM projects p
            LEFT JOIN areas a ON p.uuid = a.project_id
            ${whereClause}
            GROUP BY p.uuid, p.project_name, p.user_name, p.date, p.file_location, p.paper_size, p.description
        `;

        // Handle associated scales filter
        if (filters.associatedScalesFilter) {
            baseQuery += ` HAVING associated_scales LIKE ?`;
            params.push(`%${filters.associatedScalesFilter}%`);
        }

        // Get total count for pagination
        const countQuery = `SELECT COUNT(*) as total FROM (${baseQuery}) as subquery`;
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

        // Add pagination
        const offset = (page - 1) * perPage;
        const finalQuery = `${baseQuery} ORDER BY p.project_name LIMIT ? OFFSET ?`;
        const finalParams = [...params, perPage, offset];

        const projects = await database.all(finalQuery, finalParams);

        // Enhance projects with file information
        const enhancedProjects = [];
        for (const project of projects) {
            try {
                const fileInfo = getProjectFiles(project.file_location);
                const enhancedProject = {
                    ...project,
                    file_count: fileInfo.file_count,
                    most_recent_file: fileInfo.most_recent,
                    all_files: fileInfo.all_files
                };
                
                // Add view file properties for frontend compatibility
                if (fileInfo.most_recent) {
                    enhancedProject.view_file_path = fileInfo.most_recent.rel_path;
                    enhancedProject.view_file_type = fileInfo.most_recent.type;
                } else {
                    enhancedProject.view_file_path = null;
                    enhancedProject.view_file_type = null;
                }
                
                enhancedProjects.push(enhancedProject);
            } catch (error) {
                console.warn(`Error getting file info for project ${project.uuid}:`, error.message);
                enhancedProjects.push({
                    ...project,
                    file_count: 0,
                    most_recent_file: null,
                    all_files: [],
                    view_file_path: null,
                    view_file_type: null
                });
            }
        }

        res.json({
            projects: enhancedProjects,
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
        console.error('Error in get_all_projects:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.get('/projects/:uuid', async (req, res) => {
    try {
        const uuid = req.params.uuid;
        
        const query = `
            SELECT 
                p.uuid,
                p.project_name,
                p.user_name,
                p.date,
                p.file_location,
                p.paper_size,
                p.description,
                GROUP_CONCAT(DISTINCT a.scale) as associated_scales
            FROM projects p
            LEFT JOIN areas a ON p.uuid = a.project_id
            WHERE p.uuid = ?
            GROUP BY p.uuid, p.project_name, p.user_name, p.date, p.file_location, p.paper_size, p.description
        `;

        const project = await database.get(query, [uuid]);
        
        if (!project) {
            return res.status(404).json({ error: 'Project not found' });
        }

        // Get file information
        try {
            const fileInfo = getProjectFiles(project.file_location);
            project.file_count = fileInfo.file_count;
            project.most_recent_file = fileInfo.most_recent;
            project.all_files = fileInfo.all_files;
            
            // Add view file properties for frontend compatibility
            if (fileInfo.most_recent) {
                project.view_file_path = fileInfo.most_recent.rel_path;
                project.view_file_type = fileInfo.most_recent.type;
            } else {
                project.view_file_path = null;
                project.view_file_type = null;
            }
        } catch (error) {
            console.warn(`Error getting file info for project ${uuid}:`, error.message);
            project.file_count = 0;
            project.most_recent_file = null;
            project.all_files = [];
            project.view_file_path = null;
            project.view_file_type = null;
        }

        res.json(project);

    } catch (error) {
        console.error('Error in get_project:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.get('/projects/:uuid/areas', async (req, res) => {
    try {
        const uuid = req.params.uuid;
        
        const query = 'SELECT * FROM areas WHERE project_id = ? ORDER BY id';
        const areas = await database.all(query, [uuid]);

        res.json({ areas: areas });

    } catch (error) {
        console.error('Error in get_project_areas:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.post('/projects/search', async (req, res) => {
    try {
        const searchData = req.body;
        
        // This endpoint typically returns search results based on criteria
        // For now, implementing basic search functionality
        let whereConditions = [];
        let params = [];
        
        // Handle user names search
        if (searchData.user_names && searchData.user_names.length > 0) {
            const userConditions = searchData.user_names.map(() => 'p.user_name LIKE ?');
            whereConditions.push(`(${userConditions.join(' OR ')})`);
            searchData.user_names.forEach(name => params.push(`${name}%`));
        }
        
        // Handle other search criteria if provided
        if (searchData.project_name) {
            whereConditions.push('p.project_name LIKE ?');
            params.push(`%${searchData.project_name}%`);
        }
        
        const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';
        
        const query = `
            SELECT 
                p.uuid,
                p.project_name,
                p.user_name,
                p.date,
                p.file_location,
                p.paper_size,
                p.description,
                GROUP_CONCAT(DISTINCT a.scale) as associated_scales
            FROM projects p
            LEFT JOIN areas a ON p.uuid = a.project_id
            ${whereClause}
            GROUP BY p.uuid, p.project_name, p.user_name, p.date, p.file_location, p.paper_size, p.description
            ORDER BY p.project_name
        `;
        
        const projects = await database.all(query, params);
        
        // Enhance projects with file information
        const enhancedProjects = [];
        for (const project of projects) {
            try {
                const fileInfo = getProjectFiles(project.file_location);
                const enhancedProject = {
                    ...project,
                    file_count: fileInfo.file_count,
                    most_recent_file: fileInfo.most_recent,
                    all_files: fileInfo.all_files
                };
                
                if (fileInfo.most_recent) {
                    enhancedProject.view_file_path = fileInfo.most_recent.rel_path;
                    enhancedProject.view_file_type = fileInfo.most_recent.type;
                } else {
                    enhancedProject.view_file_path = null;
                    enhancedProject.view_file_type = null;
                }
                
                enhancedProjects.push(enhancedProject);
            } catch (error) {
                console.warn(`Error getting file info for project ${project.uuid}:`, error.message);
                enhancedProjects.push({
                    ...project,
                    file_count: 0,
                    most_recent_file: null,
                    all_files: [],
                    view_file_path: null,
                    view_file_type: null
                });
            }
        }
        
        res.json({ results: enhancedProjects });

    } catch (error) {
        console.error('Error in search_projects:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.delete('/projects/:uuid', async (req, res) => {
    try {
        const uuid = req.params.uuid;
        
        // First delete associated areas
        await database.run('DELETE FROM areas WHERE project_id = ?', [uuid]);
        
        // Then delete the project
        const result = await database.run('DELETE FROM projects WHERE uuid = ?', [uuid]);
        
        if (result.changes === 0) {
            return res.status(404).json({ error: 'Project not found' });
        }
        
        res.json({ message: 'Project deleted successfully' });

    } catch (error) {
        console.error('Error in delete_project:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.get('/projects/:uuid/files', async (req, res) => {
    try {
        const uuid = req.params.uuid;
        
        // First get the project to find its file location
        const project = await database.get('SELECT file_location FROM projects WHERE uuid = ?', [uuid]);
        
        if (!project) {
            return res.status(404).json({ error: 'Project not found' });
        }
        
        // Get file information
        try {
            const fileInfo = getProjectFiles(project.file_location);
            res.json({
                files: fileInfo.all_files,
                file_count: fileInfo.file_count,
                most_recent_file: fileInfo.most_recent
            });
        } catch (error) {
            console.warn(`Error getting files for project ${uuid}:`, error.message);
            res.json({
                files: [],
                file_count: 0,
                most_recent_file: null
            });
        }

    } catch (error) {
        console.error('Error in get_project_files:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.get('/user_names', async (req, res) => {
    try {
        const query = 'SELECT DISTINCT user_name FROM projects WHERE user_name IS NOT NULL ORDER BY user_name';
        const results = await database.all(query, []);
        
        const userNames = results.map(row => row.user_name);
        
        res.json({ user_names: userNames });

    } catch (error) {
        console.error('Error in get_user_names:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

module.exports = router;
