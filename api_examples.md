# ArcSpatialDB API Examples

This document shows how to use the ArcSpatialDB API endpoints with complete examples.

## API Endpoints

- **POST** `/api/add_project` - Add a new project with areas
- **GET** `/api/get_project/<uuid>` - Retrieve a project by UUID

---

## 1. Add Project API

### Endpoint
```
POST /api/add_project
```

### Request Format

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "uuid": "abc12345",
  "project_name": "Jerusalem City Plan",
  "user_name": "gis_analyst",
  "date": "25-12-25",
  "file_location": "sampleDataset/jerusalem_city_plan",
  "paper_size": "A0 (Landscape)",
  "description": "Comprehensive city planning map for Jerusalem",
  "areas": [
    {
      "xmin": 220000,
      "ymin": 630000,
      "xmax": 230000,
      "ymax": 640000,
      "scale": "Scale: 1:25000"
    },
    {
      "xmin": 225000,
      "ymin": 635000,
      "xmax": 228000,
      "ymax": 638000,
      "scale": "Scale: 1:10000"
    }
  ]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uuid` | string | ✅ | Unique project identifier (8 characters) |
| `project_name` | string | ✅ | Name of the GIS project |
| `user_name` | string | ✅ | Name of the user who created the project |
| `date` | string | ✅ | Project date in DD-MM-YY format |
| `file_location` | string | ✅ | Path to project files |
| `paper_size` | string | ✅ | Paper size (e.g., "A3 (Portrait)", "Custom Size: Height: 29.7 cm, Width: 42.0 cm") |
| `description` | string | ✅ | Project description |
| `areas` | array | ❌ | Array of map areas (optional) |

### Area Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `xmin` | number | ✅ | Minimum X coordinate (UTM) |
| `ymin` | number | ✅ | Minimum Y coordinate (UTM) |
| `xmax` | number | ✅ | Maximum X coordinate (UTM) |
| `ymax` | number | ✅ | Maximum Y coordinate (UTM) |
| `scale` | string | ✅ | Map scale (e.g., "Scale: 1:25000") |

### Success Response (201 Created)

```json
{
  "message": "Project added successfully",
  "uuid": "abc12345"
}
```

### Error Responses

**Missing Fields (400 Bad Request):**
```json
{
  "error": "Missing fields: uuid, project_name"
}
```

**Invalid Area Data (400 Bad Request):**
```json
{
  "error": "Missing area fields: xmin, ymin"
}
```

**Database Error (500 Internal Server Error):**
```json
{
  "error": "UNIQUE constraint failed: projects.uuid"
}
```

---

## 2. Get Project API

### Endpoint
```
GET /api/get_project/{uuid}
```

### Example Request
```
GET /api/get_project/abc12345
```

### Success Response (200 OK)

```json
{
  "uuid": "abc12345",
  "project_name": "Jerusalem City Plan",
  "user_name": "gis_analyst",
  "date": "25-12-25",
  "file_location": "sampleDataset/jerusalem_city_plan",
  "paper_size": "A0 (Landscape)",
  "description": "Comprehensive city planning map for Jerusalem",
  "areas": [
    {
      "id": 1,
      "project_id": "abc12345",
      "xmin": 220000,
      "ymin": 630000,
      "xmax": 230000,
      "ymax": 640000,
      "scale": "Scale: 1:25000"
    },
    {
      "id": 2,
      "project_id": "abc12345",
      "xmin": 225000,
      "ymin": 635000,
      "xmax": 228000,
      "ymax": 638000,
      "scale": "Scale: 1:10000"
    }
  ]
}
```

### Error Response (404 Not Found)

```json
{
  "error": "Project not found"
}
```

---

## 3. Testing Examples

### Using cURL

**Add Project:**
```bash
curl -X POST http://localhost:5000/api/add_project \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "test1234",
    "project_name": "Test Project",
    "user_name": "test_user",
    "date": "25-12-25",
    "file_location": "sampleDataset/test_project",
    "paper_size": "A3 (Portrait)",
    "description": "Test project via API",
    "areas": [
      {
        "xmin": 100000,
        "ymin": 200000,
        "xmax": 110000,
        "ymax": 210000,
        "scale": "Scale: 1:50000"
      }
    ]
  }'
```

**Get Project:**
```bash
curl http://localhost:5000/api/get_project/test1234
```

### Using Python requests

```python
import requests
import json

# API base URL
base_url = "http://localhost:5000"

# Add project
project_data = {
    "uuid": "test1234",
    "project_name": "Test Project",
    "user_name": "test_user",
    "date": "25-12-25",
    "file_location": "sampleDataset/test_project",
    "paper_size": "A3 (Portrait)",
    "description": "Test project via API",
    "areas": [
        {
            "xmin": 100000,
            "ymin": 200000,
            "xmax": 110000,
            "ymax": 210000,
            "scale": "Scale: 1:50000"
        }
    ]
}

# Send POST request
response = requests.post(f"{base_url}/api/add_project", json=project_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Get project
if response.status_code == 201:
    uuid = response.json()["uuid"]
    get_response = requests.get(f"{base_url}/api/get_project/{uuid}")
    print(f"Get Status: {get_response.status_code}")
    print(f"Project Data: {json.dumps(get_response.json(), indent=2)}")
```

### Using JavaScript (fetch)

```javascript
// Add project
const projectData = {
    uuid: "test1234",
    project_name: "Test Project",
    user_name: "test_user",
    date: "25-12-25",
    file_location: "sampleDataset/test_project",
    paper_size: "A3 (Portrait)",
    description: "Test project via API",
    areas: [
        {
            xmin: 100000,
            ymin: 200000,
            xmax: 110000,
            ymax: 210000,
            scale: "Scale: 1:50000"
        }
    ]
};

fetch('http://localhost:5000/api/add_project', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(projectData)
})
.then(response => response.json())
.then(data => {
    console.log('Success:', data);
    
    // Get the project
    return fetch(`http://localhost:5000/api/get_project/${data.uuid}`);
})
.then(response => response.json())
.then(project => {
    console.log('Project:', project);
})
.catch(error => {
    console.error('Error:', error);
});
```

---

## 4. Real-World Example from ArcGIS Pro

This is what the `db_manager.pyt` plugin sends to the API:

```json
{
  "uuid": "a1b2c3d4",
  "project_name": "Tel_Aviv_Urban_Planning",
  "user_name": "arcgis_user",
  "date": "25-12-25",
  "file_location": "sampleDataset/Tel_Aviv_Urban_Planning",
  "paper_size": "A1 (Landscape)",
  "description": "Urban planning map for Tel Aviv downtown area",
  "areas": [
    {
      "xmin": 180000,
      "ymin": 660000,
      "xmax": 190000,
      "ymax": 670000,
      "scale": "Scale: 1:15000"
    }
  ]
}
```

---

## 5. Common Paper Size Formats

The API accepts these paper size formats:

- `"A0 (Portrait)"` / `"A0 (Landscape)"`
- `"A1 (Portrait)"` / `"A1 (Landscape)"`
- `"A2 (Portrait)"` / `"A2 (Landscape)"`
- `"A3 (Portrait)"` / `"A3 (Landscape)"`
- `"A4 (Portrait)"` / `"A4 (Landscape)"`
- `"Custom Size: Height: 29.7 cm, Width: 42.0 cm"`

---

## 6. Coordinate System

All coordinates should be in **UTM (Universal Transverse Mercator)** format:
- X coordinates: Easting (typically 6-7 digits)
- Y coordinates: Northing (typically 6-7 digits)
- Example: `xmin: 220000, ymin: 630000`

The coordinates are automatically converted from the original coordinate system to UTM by the ArcGIS Pro plugin. 