LibreChat with Django + MCP + MongoDB Setup
Complete stack with Django REST API layer between MCP Server and MongoDB.

Architecture
text
LibreChat (UI) 
    ↓ (via Gemini-2.0-flash)
MCP Server (bi_universal.py - Port 8000)
    ↓ (HTTP REST calls)
Django REST API (Port 8001)
    ↓ (PyMongo)
MongoDB (Port 27017)

Project Structure

text
Librechat_webUI_MCP/
├── docker-compose.yml          # Orchestrates all 4 services
├── Dockerfile                  # For MCP server
├── bi_universal.py             # MCP server (calls Django API)
├── requirements.txt            # Python dependencies
├── librechat.yaml              # LibreChat config with MCP
├── .env                        # Environment variables
├── setup_django.sh             # Django setup script
├── Dockerfile.django           # For Django service
├── django-settings.py          # Django settings template
├── django-views.py             # Django API views template
├── django-urls.py              # Django URL routing template
└── django_project/             # Created by setup script
    ├── Dockerfile
    ├── requirements.txt
    ├── manage.py
    ├── django_api/
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── mongodb_api/
        ├── __init__.py
        ├── apps.py
        ├── models.py
        ├── views.py
        └── urls.py

Setup Instructions
Step 1: Initialize Django Project
bash
cd /mnt/c/Yash_Files/office_work/Librechat_webUI_MCP

# Run setup script
chmod +x setup_django.sh
./setup_django.sh

Step 2: Build All Services
bash
# Build MCP server and Django API
docker-compose build

# Start all services
docker-compose up -d

# Wait for services to start
sleep 30

# Check status
docker-compose ps
Expected output:

text
NAME           STATUS
django-api     Up X seconds
bi-universal   Up X seconds
librechat      Up X seconds (healthy)
mongo          Up X seconds (healthy)


Step 3: Verify Django API
bash
# Test Django API directly
curl http://localhost:8001/api/collections/

# Expected response:
# {"collections": [...], "count": X, "database": "companyDB", "status": "success"}

Step 4: Verify MCP Server → Django Connection
bash
# Check MCP logs
docker logs bi-universal | grep "Django API"

# Should show: "Django API URL: http://django-api:8001/api"

Step 5: Test in LibreChat
Open http://localhost:3080

Login with your account

Select gemini-2.0-flash model

Ask: "List all MongoDB collections"

Expected: MCP calls Django API, Django queries MongoDB, returns data to MCP, which shows in chat!

Available Django API Endpoints
Endpoint	Method	Description
/api/collections/	GET	List all collections
/api/collections/{name}/info/	GET	Get collection details
/api/collections/query/	POST	Query documents
/api/collections/count/	POST	Count documents
/api/collections/insert/	POST	Insert document
/api/collections/update/	POST	Update documents
/api/collections/delete/	POST	Delete documents
/api/collections/export/	POST	Export to JSON
MCP Tools (via Django API)
All 8 MCP tools now use Django API:

list_collections → GET /api/collections/

get_collection_info → GET /api/collections/{name}/info/

query_collection → POST /api/collections/query/

count_documents → POST /api/collections/count/

export_to_csv → POST /api/collections/export/

insert_document → POST /api/collections/insert/

update_document → POST /api/collections/update/

delete_document → POST /api/collections/delete/

Testing
Test Django API Directly
bash
# List collections
curl http://localhost:8001/api/collections/

# Query collection
curl -X POST http://localhost:8001/api/collections/query/ \
  -H "Content-Type: application/json" \
  -d '{"collection": "users", "filter": {}, "limit": 5}'

# Count documents
curl -X POST http://localhost:8001/api/collections/count/ \
  -H "Content-Type: application/json" \
  -d '{"collection": "users", "filter": {}}'
Test MCP Server
bash
# Check MCP tools loaded
docker logs librechat | grep "Added.*MCP tools"

# Should show: "Added 8 MCP tools"
Troubleshooting
Django API not starting
bash
# Check logs
docker logs django-api

# Rebuild
docker-compose build django-api
docker-compose up -d django-api
MCP cannot reach Django
bash
# Check network connectivity
docker exec bi-universal ping django-api

# Check Django API URL
docker logs bi-universal | grep "Django API URL"
MongoDB connection issues
bash
# Check Django can connect to MongoDB
docker exec django-api python manage.py shell

# In shell:
from pymongo import MongoClient
client = MongoClient('mongodb://admin:pass123@mongo:27017')
print(client.list_database_names())
Development
Add New Django API Endpoint
Edit django_project/mongodb_api/views.py

Add new view class

Edit django_project/mongodb_api/urls.py

Add URL pattern

Restart: docker-compose restart django-api

Add New MCP Tool
Edit bi_universal.py

Add new @mcp.tool() function

Call Django API using call_django_api()

Restart: docker-compose restart bi-universal librechat

Benefits of Django Layer
✅ Business Logic Separation - Complex operations in Django
✅ Authentication - Can add Django auth later
✅ Data Validation - Django serializers
✅ API Documentation - Django REST framework
✅ Database Migrations - Django ORM (if needed)
✅ Admin Interface - Django admin (future)
✅ Caching - Django cache framework
✅ Testing - Django test framework

Ports
Service	Port
MongoDB	27017
Django API	8001
MCP Server	8000
LibreChat	3080
Environment Variables
Set in .env:

GOOGLE_KEY - Your Google Gemini API key

MONGO_URI - MongoDB connection string

MONGO_DB - Database name

DJANGO_API_URL - Django API URL (set automatically)

Setup complete! You now have a full 4-tier architecture: LibreChat → MCP → Django → MongoDB! 🚀