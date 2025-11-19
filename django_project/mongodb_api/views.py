from django.http import JsonResponse
from rest_framework.decorators import api_view
from pymongo import MongoClient
import os
import json
from bson import ObjectId
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:pass123@mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "companyDB")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]


def serialize_doc(doc):
    """Convert MongoDB document to JSON-safe format."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


@api_view(["GET"])
def list_collections(request):
    """List all collections in MongoDB."""
    try:
        collections = db.list_collection_names()
        return JsonResponse({
            "status": "success",
            "database": MONGO_DB,
            "collections": collections
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def query_collection(request):
    """Query documents with filters and limits."""
    try:
        body = json.loads(request.body)
        collection = body.get("collection")
        filter_ = body.get("filter", {})
        limit = int(body.get("limit", 100))

        docs = list(db[collection].find(filter_).limit(limit))
        docs = [serialize_doc(d) for d in docs]

        return JsonResponse({
            "status": "success",
            "collection": collection,
            "documents": docs
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def insert_document(request):
    """Insert a new document into MongoDB."""
    try:
        body = json.loads(request.body)
        collection = body.get("collection")
        document = body.get("document")

        result = db[collection].insert_one(document)
        return JsonResponse({
            "status": "success",
            "inserted_id": str(result.inserted_id)
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def update_document(request):
    """Update documents in MongoDB."""
    try:
        body = json.loads(request.body)
        collection = body.get("collection")
        filter_ = body.get("filter", {})
        update = body.get("update", {})

        if not any(k.startswith("$") for k in update.keys()):
            update = {"$set": update}

        result = db[collection].update_many(filter_, update)
        return JsonResponse({
            "status": "success",
            "matched": result.matched_count,
            "modified": result.modified_count
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def delete_document(request):
    """Delete documents matching a filter."""
    try:
        body = json.loads(request.body)
        collection = body.get("collection")
        filter_ = body.get("filter", {})

        result = db[collection].delete_many(filter_)
        return JsonResponse({
            "status": "success",
            "deleted_count": result.deleted_count
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
def get_collection_info(request, collection):
    """Return metadata and sample documents for a collection."""
    try:
        col = db[collection]
        count = col.count_documents({})
        sample = list(col.find({}).limit(2))
        sample = [serialize_doc(d) for d in sample]
        fields = list(sample[0].keys()) if sample else []

        return JsonResponse({
            "collection": collection,
            "document_count": count,
            "fields": fields,
            "sample_documents": sample,
            "status": "success"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def export_collection(request):
    """Export filtered documents to CSV format (inline response)."""
    try:
        body = json.loads(request.body)
        collection = body.get("collection")
        filter_ = body.get("filter", {})

        docs = list(db[collection].find(filter_))
        docs = [serialize_doc(d) for d in docs]

        df = pd.DataFrame(docs)
        return JsonResponse({
            "status": "success",
            "rows": len(docs),
            "data": docs
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
def health(request):
    """Simple health check for Django ↔ MongoDB."""
    try:
        client.admin.command("ping")
        return JsonResponse({"status": "healthy", "mongo_db": MONGO_DB})
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)