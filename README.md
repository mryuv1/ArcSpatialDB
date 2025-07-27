# ArcSpatialDB: ArcGIS Pro Project Search and Management

ArcSpatialDB is a web-based tool designed to simplify the management and searching of ArcGIS Pro projects. It provides a user-friendly interface to query a database of your projects based on various spatial and metadata criteria.

## Key Features

- **Spatial Search**: Find projects based on their geographic extent. You can search for projects that are inside, outside, or overlap with a specified bounding box.
- **Metadata Filtering**: Filter projects by UUID, user name, creation date, paper size, and scale.
- **Interactive Map**: (Future implementation) Visualize project locations and search results on an interactive map.
- **File Management**: View project files (PDFs, images) directly in your browser and copy file paths to your clipboard.
- **Database Management**: Easily add, delete, and manage projects in your database.

## Getting Started

### Prerequisites

- Python 3.x
- Flask
- SQLAlchemy

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/ArcSpatialDB.git
   cd ArcSpatialDB
   ```

2. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database:**
   ```bash
   python generate_sample_db.py
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

The application will be available at `http://127.0.0.1:5000`.

## Usage

1. **Search for projects**: Use the search form to enter your desired criteria. You can search by spatial extent, metadata, or a combination of both.
2. **View results**: The search results will be displayed in a table. You can view project files, copy file paths, and delete projects from this table.
3. **Manage all projects**: The "All Projects" table displays all the projects in your database. You can filter and sort this table to find specific projects.
4. **Manage all areas**: The "All Areas" table displays all the spatial areas associated with your projects. You can filter and sort this table to find specific areas.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss your ideas.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## New Frontend-Backend Structure (Post-Split)

After splitting, your project will look like this:

```
ArcSpatialDB/
  backend/           # Python Flask API (no HTML rendering)
    app.py           # Modified to serve only API endpoints
    requirements.txt # Backend dependencies
    elements.db      # Database (or symlink/copy)
    ...
  frontend/          # HTML/JS frontend (static site)
    index.html       # Main UI (adapted from templates/index.html)
    static/          # Static assets (images, CSS, JS)
      rocket.jpg
    ...
```

### How to Run

**Backend:**
1. `cd backend`
2. `pip install -r requirements.txt`
3. `python app.py` (or use `server.py` for production)

**Frontend:**
1. `cd frontend`
2. Open `index.html` in your browser (or serve with a static file server for local development)

The frontend will communicate with the backend via HTTP API calls (e.g., `fetch('http://localhost:5000/api/get_project/123')`).

---
