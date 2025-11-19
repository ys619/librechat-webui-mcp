# LibreChat WebUI with MCP, Django & MongoDB - Complete Documentation

## 📖 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Installation & Setup](#installation--setup)
5. [How It Works](#how-it-works)
6. [File Structure](#file-structure)
7. [API Endpoints](#api-endpoints)
8. [MCP Tools](#mcp-tools)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)

---

##  Project Overview

**LibreChat WebUI with MCP, Django & MongoDB** is a complete, production-ready chat application that combines:

- **LibreChat**: Open-source chat UI
- **Google Gemini**: Advanced AI/LLM model
- **MCP (Model Context Protocol)**: Connects AI to custom tools
- **Django REST API**: Business logic layer
- **MongoDB**: NoSQL database for data persistence

This is a **4-tier application architecture** completely Dockerized, meaning everything runs in containers with one command: `docker-compose up -d`

### Use Cases

-  **Enterprise Chat Applications**: Build intelligent chatbots with database access
-  **Data Analytics Chat**: Query MongoDB data through natural language
-  **LLM Tool Integration**: Add custom tools to any LLM
-  **Educational Projects**: Learn Docker, Python, Django, MongoDB, FastAPI

---

##  Architecture

### 4-Tier System

```
┌────────────────────────────────────────────────────┐
│  User Browser (http://localhost:3080)              │
│  LibreChat Web UI                                  │
└────────────────┬─────────────────────────────────┘
                 │
                 ↓ (HTTP/REST)
┌────────────────────────────────────────────────────┐
│  Google Gemini API (Cloud)                         │
│  "List employees from MongoDB"                     │
└────────────────┬─────────────────────────────────┘
                 │
                 ↓ (Uses MCP tools)
┌────────────────────────────────────────────────────┐
│  MCP Server (Port 8000)                            │
│  FastMCP / bi_universal.py                         │
│  - Provides 10 tools to Gemini                      │
│  - Routes requests to Django                       │
└────────────────┬─────────────────────────────────┘
                 │
                 ↓ (HTTP/REST API)
┌────────────────────────────────────────────────────┐
│  Django REST API (Port 8001)                       │
│  Business Logic Layer                              │
│  - Handles data validation                         │
│  - Connects to MongoDB                             │
└────────────────┬─────────────────────────────────┘
                 │
                 ↓ (MongoClient)
┌────────────────────────────────────────────────────┐
│  MongoDB (Port 27017)                              │
│  Database (companyDB)                              │
│  - Collections: employees, projects, sales, etc.   │
└────────────────────────────────────────────────────┘
```

### Container Communication

All containers are on the **same Docker network** (`librechat-network`), so they communicate using service names:

- `librechat` → talks to `bi-universal` at `http://bi-universal:8000/mcp`
- `bi-universal` → talks to `django-api` at `http://django-api:8001/api`
- `django-api` → talks to `mongo` at `mongodb://admin:pass123@mongo:27017`

---

##  Features

### 1. **Web UI (LibreChat)**
- Clean, intuitive chat interface
- Google Gemini model integration
- Conversation history
- Real-time responses

### 2. **MCP Tools (10 Available)**
- `query_collection` - Query MongoDB data
- `insert_document` - Add new documents
- `update_document` - Modify existing data
- `delete_document` - Remove data
- `list_collections_via_django` - Show all collections
- `get_collection_info_via_django` - Get collection details
- `export_via_django` - Export data to JSON
- `smart_command` - Natural language commands
- `django_health_check` - API health status
- `create_plot` - Generate charts and graphs

### 3. **Django REST API**
- Fully RESTful endpoints
- MongoDB integration
- Request validation
- Error handling
- Health checks

### 4. **Database (MongoDB)**
- NoSQL database
- Flexible schema
- Full CRUD operations
- Compound queries

### 5. **Docker & DevOps**
- Multi-container orchestration
- Volume persistence
- Health checks
- Automatic restart policies
- Environment configuration

---

##  Installation & Setup

### Prerequisites

- Docker & Docker Compose installed
- Google Gemini API key (free from https://console.google.com/gen-ai)
- ~2GB free disk space

### Step 1: Clone Repository

```bash
git clone https://github.com/ys619/librechat-webui-mcp.git
cd librechat-webui-mcp
```

### Step 2: Configure Environment

Create or update `.env` file:

```env
# Google Gemini API Key (REQUIRED)
GOOGLE_KEY=your-api-key-here

# MongoDB Configuration
MONGO_URI=mongodb://admin:pass123@mongo:27017
MONGO_DB=companyDB
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=pass123

# MCP Configuration
DATABASE_TYPE=mongodb
ENABLE_DJANGO_API=true
DJANGO_API_URL=http://django-api:8001/api

# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

# LibreChat Configuration
NODE_ENV=production
ALLOW_REGISTRATION=true
ALLOW_GUEST_ACCESS=false
DEFAULT_MODEL=gemini-2.0-flash
```

### Step 3: Start All Services

```bash
# Build and start
docker-compose up -d --build

# Wait 30 seconds for services to initialize
sleep 30

# Verify all services running
docker-compose ps
```

Expected output:
```
NAME           STATUS              PORTS
mongo          Up (healthy)        27017/tcp
django-api     Up                  8001/tcp
bi-universal   Up                  8000/tcp
librechat      Up (healthy)        3080/tcp
```

### Step 4: Access Application

- **Chat UI**: http://localhost:3080
- **Django API**: http://localhost:8001/api/collections/
- **MCP Server**: http://localhost:8000/mcp
- **MongoDB**: localhost:27017 (internal)

### Step 5: First Query

1. Go to http://localhost:3080
2. Login (default credentials or create account)
3. Ask: **"List all collections"**
4. Gemini will use MCP tools to query MongoDB
5. Get response: Collection names and details

---

##  How It Works: Step-by-Step

### Example Query: "List employees from the Finance department"

#### **Step 1: User Input**
```
User types in LibreChat: "List employees from the Finance department"
```

#### **Step 2: LibreChat → Gemini API**
LibreChat sends the query to Google Gemini API with available tools.

#### **Step 3: Gemini Decides**
Gemini analyzes the query and decides:
- This needs data from database
- I should use the `query_collection` MCP tool
- Collection: `employees`
- Filter: `{department: "Finance"}`

#### **Step 4: Gemini → MCP Server**
Gemini calls the MCP tool at `http://bi-universal:8000/mcp`:

```json
{
  "tool": "query_collection",
  "args": {
    "collection": "employees",
    "filter": "{\"department\": \"Finance\"}",
    "limit": 100
  }
}
```

#### **Step 5: MCP → Django API**
MCP server receives request and forwards to Django API:

```
POST http://django-api:8001/api/collections/query/
{
  "collection": "employees",
  "filter": {"department": "Finance"},
  "limit": 100
}
```

#### **Step 6: Django → MongoDB**
Django REST API connects to MongoDB:

```python
from pymongo import MongoClient
client = MongoClient('mongodb://admin:pass123@mongo:27017')
db = client['companyDB']
collection = db['employees']
results = list(collection.find({"department": "Finance"}))
```

#### **Step 7: MongoDB Returns Data**
```json
[
  {
    "_id": "ObjectId(...)",
    "name": "Fahad",
    "department": "Finance",
    "salary": 72000,
    "city": "Thane"
  },
  {
    "_id": "ObjectId(...)",
    "name": "Priya",
    "department": "Finance",
    "salary": 68000,
    "city": "Mumbai"
  }
]
```

#### **Step 8: Data Returns Up the Stack**
- MongoDB → Django (formatted as JSON)
- Django → MCP (HTTP response)
- MCP → Gemini (tool result)
- Gemini → LibreChat (natural language response)

#### **Step 9: User Sees Answer**
```
LibreChat displays:
"Here are the employees in the Finance department:
- Fahad from Thane, salary: 72000
- Priya from Mumbai, salary: 68000"
```

---

## File Structure

```
librechat-webui-mcp/
│
├── docker-compose.yml              # Main orchestration file
├── .env                            # Environment variables
├── .gitignore                      # Git ignore rules
│
├── mcp/                            # MCP Server
│   ├── bi_universal.py             # Main MCP server with 10 tools
│   ├── requirements.txt            # Python dependencies
│   └── Dockerfile                  # Container config
│
├── django_project/                 # Django REST API
│   ├── manage.py                   # Django management
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Container config
│   ├── django_api/                 # Main Django app
│   │   ├── settings.py             # Django settings
│   │   ├── urls.py                 # URL routing
│   │   └── wsgi.py                 # WSGI config
│   └── mongodb_api/                # API app
│       ├── views.py                # REST API views
│       ├── urls.py                 # API routes
│       └── models.py               # Data models
│
├── librechat.yaml                  # LibreChat configuration
├── docs/                           # Documentation
│   ├── README.md                   # Project overview
│   └── README-DJANGO.md            # Django documentation
│
└── workspace/                      # MCP outputs
    └── bi_outputs/                 # Generated files (charts, logs)
```

---

## API Endpoints

### Django REST API (`http://localhost:8001/api/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/collections/` | List all collections |
| `POST` | `/collections/query/` | Query documents with filters |
| `POST` | `/collections/insert/` | Insert new document |
| `POST` | `/collections/update/` | Update existing documents |
| `POST` | `/collections/delete/` | Delete documents |
| `POST` | `/collections/export/` | Export collection to JSON |
| `GET` | `/health/` | Health check |

### Example API Call

```bash
# Query employees from Finance department
curl -X POST http://localhost:8001/api/collections/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "employees",
    "filter": {"department": "Finance"},
    "limit": 100
  }'

# Response:
{
  "collection": "employees",
  "documents_found": 2,
  "documents": [
    {"_id": "...", "name": "Fahad", "department": "Finance", ...},
    {"_id": "...", "name": "Priya", "department": "Finance", ...}
  ],
  "status": "success"
}
```

---

## 🧩 MCP Tools

### 1. **query_collection**
Query MongoDB with filters, sorting, and limits.

```
Input: collection name, filter dict, limit
Output: Array of documents
```

### 2. **insert_document**
Add new document to collection.

```
Input: collection name, document data
Output: Inserted document ID
```

### 3. **update_document**
Modify existing documents.

```
Input: collection name, filter, update data
Output: Number of documents updated
```

### 4. **delete_document**
Remove documents from collection.

```
Input: collection name, filter
Output: Number of documents deleted
```

### 5. **list_collections_via_django**
Get all collection names and counts.

```
Output: List of collections with document counts
```

### 6. **get_collection_info_via_django**
Get detailed info about a collection.

```
Input: collection name
Output: Field names, data types, total documents
```

### 7. **export_via_django**
Export entire collection as JSON.

```
Input: collection name
Output: JSON file path
```

### 8. **smart_command**
Natural language command execution.

```
Input: Natural language instruction
Output: Execution result
```

### 9. **django_health_check**
Check API health status.

```
Output: API status, uptime, response time
```

### 10. **create_plot**
Generate charts and graphs from data.

```
Input: Data, chart type (bar, line, pie, etc.)
Output: Chart image file path
```

---

##  Docker Commands

### Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f django-api

# Restart specific service
docker-compose restart django-api

# Remove everything (including volumes!)
docker-compose down -v

# Rebuild images
docker-compose build

# Scale a service
docker-compose up -d --scale bi-universal=2

# Check container status
docker-compose ps

# Execute command in container
docker-compose exec django-api python manage.py migrate
```

---

## Troubleshooting

### Issue: Services won't start

```bash
# Check Docker daemon is running
docker --version

# Check logs
docker-compose logs

# Common fix: restart Docker
sudo systemctl restart docker
```

### Issue: "Port 3080 already in use"

```bash
# Stop other services using the port
lsof -i :3080
kill -9 <PID>

# Or change port in docker-compose.yml
# Change: ports: - "3080:3080"
# To: ports: - "3081:3080"
```

### Issue: MongoDB connection refused

```bash
# Check MongoDB container is running
docker-compose ps mongo

# Verify credentials in .env
# Default: admin / pass123

# Check network
docker network ls
```

### Issue: Django API returns 404

```bash
# Check URL routing in django_api/urls.py
# Must have: path("api/", include("mongodb_api.urls"))

# Restart Django
docker-compose restart django-api
```

### Issue: MCP tools not available in Gemini

```bash
# Check MCP is running
docker-compose logs bi-universal

# Verify connection
curl http://localhost:8000/mcp

# Check librechat config (librechat.yaml)
# Must have: bi-universal endpoint configured
```

---

##  File Explanations

### `docker-compose.yml`
Orchestration file defining all 4 services:
- **mongo**: Database container
- **django-api**: REST API container
- **bi-universal**: MCP server container
- **librechat**: Web UI container

Specifies:
- Image/Dockerfile for each service
- Ports exposed
- Environment variables
- Volume mounts
- Health checks
- Dependencies
- Network configuration

### `mcp/bi_universal.py`
Main MCP server file that:
- Defines 10 MCP tools
- Routes requests to Django API
- Handles tool execution
- Returns results to Gemini

Key functions:
- `query_via_django()` - Query MongoDB
- `insert_via_django()` - Insert data
- `health_check()` - API status

### `django_project/mongodb_api/views.py`
REST API views handling:
- `list_collections()` - List all collections
- `query_collection()` - Query with filters
- `insert_document()` - Create new records
- `update_document()` - Modify records
- `delete_document()` - Remove records

### `django_project/mongodb_api/urls.py`
API routing - maps URLs to views:
- `GET /collections/` → list_collections()
- `POST /collections/query/` → query_collection()
- etc.

### `librechat.yaml`
LibreChat configuration:
- MCP server endpoints
- Gemini API settings
- UI customization
- Model selection

---

## Contributing

Want to extend this project?

### Add a New MCP Tool

1. Edit `mcp/bi_universal.py`
2. Add new tool function:

```python
@mcp_server.tool()
def new_tool(arg1: str, arg2: int) -> dict:
    """Description of tool"""
    # Implementation
    return {"result": "value"}
```

3. Rebuild and restart:

```bash
docker-compose build bi-universal
docker-compose up -d bi-universal
```

### Add New API Endpoint

1. Edit `django_project/mongodb_api/views.py`
2. Create new view:

```python
class NewApiView(APIView):
    def post(self, request):
        # Implementation
        return Response({"status": "success"})
```

3. Add URL routing in `urls.py`:

```python
path("new-endpoint/", views.new_api_view, name="new_endpoint")
```

4. Restart Django:

```bash
docker-compose restart django-api
```

---

##  License

MIT License - Feel free to use for personal and commercial projects.

---

##  Author

**Yash Singh** (@ys619)
- GitHub: https://github.com/ys619
- Project: https://github.com/ys619/librechat-webui-mcp

---

## Acknowledgments

- [LibreChat](https://github.com/danny-avila/LibreChat) - Open-source chat UI
- [Google Gemini](https://ai.google.dev/) - AI model
- [FastMCP](https://gofastmcp.com/) - MCP implementation
- [Django](https://www.djangoproject.com/) - Web framework
- [MongoDB](https://www.mongodb.com/) - Database
- [Docker](https://www.docker.com/) - Containerization

---

## Support

For issues, questions, or suggestions:
1. Check [Troubleshooting](#troubleshooting) section
2. Open GitHub Issue: https://github.com/ys619/librechat-webui-mcp/issues
3. Read individual README files in `/docs/`
4. For any queries, contact on yashjagvirsingh17@gmail.com
---

**Happy coding!**