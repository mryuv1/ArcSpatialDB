# ArcSpatialDB Node.js Backend

This is a Node.js implementation of the ArcSpatialDB backend, providing the same functionality as the original Flask backend.

## Features

- Full REST API compatibility with the Flask backend
- SQLite database integration
- Project and area management
- File serving capabilities
- CORS support for frontend integration
- Pagination and filtering support

## Installation

1. Navigate to the backend_node directory:
   ```bash
   cd backend_node
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Running the Server

### Production Mode
```bash
npm start
```
Or use the batch file:
```bash
start_backend_node.bat
```

### Development Mode (with auto-restart)
```bash
npm run dev
```
Or use the batch file:
```bash
start_backend_dev.bat
```

The server will run on `http://localhost:5000` by default.

## Environment Variables

- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: 0.0.0.0)

## API Endpoints

### Health Check
- `GET /api/health` - Check if the API is running

### Projects
- `GET /api/projects` - Get all projects with pagination and filtering
- `GET /api/projects/:uuid` - Get a specific project by UUID
- `GET /api/projects/:uuid/areas` - Get all areas for a specific project

### Areas
- `GET /api/areas` - Get all areas with pagination and filtering
- `GET /api/areas/:id` - Get a specific area by ID

### Files
- `GET /view_file/*` - Serve project files for viewing

## Query Parameters

### Projects Filtering
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 10)
- `uuid_filter` - Filter by UUID prefix
- `project_name_filter` - Filter by project name prefix
- `user_name_filter` - Filter by user name prefix
- `date_filter` - Filter by date prefix
- `file_location_filter` - Filter by file location prefix
- `paper_size_filter` - Filter by paper size prefix
- `associated_scales_filter` - Filter by associated scales

### Areas Filtering
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 10)
- `id_filter` - Filter by area ID
- `project_id_filter` - Filter by project ID
- `xmin_filter`, `ymin_filter`, `xmax_filter`, `ymax_filter` - Filter by coordinates
- `scale_filter` - Filter by scale

## Testing

Run the API test script:
```bash
node test_api.js
```

This will test the main endpoints and display the results.

## Dependencies

- **express**: Web framework
- **cors**: Cross-origin resource sharing
- **sqlite3**: SQLite database driver
- **glob**: File pattern matching
- **multer**: File upload handling
- **path**: Path utilities

## Dev Dependencies

- **nodemon**: Development server with auto-restart

## Database

The backend connects to the same `elements.db` SQLite database used by the Flask backend, ensuring data compatibility.

## File Structure

```
backend_node/
├── api/
│   ├── projects.js    # Projects API routes
│   ├── areas.js       # Areas API routes
│   └── files.js       # File serving routes
├── models/
│   └── database.js    # Database connection and utilities
├── utils/
│   ├── helpers.js     # Helper functions
│   └── fileUtils.js   # File utility functions
├── app.js             # Main application file
├── package.json       # Node.js dependencies
├── test_api.js        # API testing script
└── *.bat              # Windows batch files for easy startup
```

## Compatibility

This Node.js backend is fully compatible with the existing frontend and provides identical API responses to the Flask backend.
