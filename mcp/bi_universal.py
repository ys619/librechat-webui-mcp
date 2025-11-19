# bi_universal.py - MCP Server (MCP -> Django API -> MongoDB)
# Revised: add stronger natural language parsing (who owns X, which employee is from Y, etc.)

from fastmcp import FastMCP
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import uuid
from dotenv import load_dotenv
from typing import Any, Dict, List
import sys
import re
import requests
from urllib.parse import urljoin

# ================= STEP 1: Load Environment =================
load_dotenv()

# ================= STEP 2: Initialize MCP =================
mcp = FastMCP("bi-universal")

# ================= STEP 3: Django API Configuration =================
ENABLE_DJANGO_API = os.getenv("ENABLE_DJANGO_API", "true").lower() in ("1", "true", "yes")
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001/api")

OUTPUT_DIR = "/app/bi_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def call_django_api(endpoint: str, method: str = "GET", data: dict = None) -> Dict[str, Any]:
    """Make HTTP requests to Django API (small wrapper)."""
    if not ENABLE_DJANGO_API:
        return {"error": "Django API disabled (ENABLE_DJANGO_API=false)"}
    url = urljoin(DJANGO_API_URL.rstrip("/") + "/", endpoint.lstrip("/"))
    try:
        headers = {"Content-Type": "application/json"}
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=20)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=20)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": f"Django API request timeout at {url}"}
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to Django API at {url}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Django API request failed: {str(e)}"}


# ================= STEP 4: Utilities =================
def format_as_table(docs: List[Dict[str, Any]], keys=None) -> str:
    """Format a list of dicts into a simple markdown table string (unique by name)."""
    if not docs:
        return "No records found."
    if keys is None:
        keys = ["_id", "name", "department", "salary", "city", "joinDate"]
    header = "| " + " | ".join(keys) + " |\n"
    header += "| " + " | ".join(["---"] * len(keys)) + " |\n"
    rows = ""
    seen = set()
    for d in docs:
        name = d.get("name", "")
        if name and name in seen:
            continue
        if name:
            seen.add(name)
        row = []
        for k in keys:
            v = d.get(k, "")
            if isinstance(v, dict) or isinstance(v, list):
                v = json.dumps(v, ensure_ascii=False)
            row.append(str(v))
        rows += "| " + " | ".join(row) + " |\n"
    return header + rows


def _build_vehicle_regex_filter(vehicle_text: str) -> Dict[str, Any]:
    """
    Build a Mongo-like filter that searches common vehicle subfields for the vehicle_text.
    The MCP uses the Django API query endpoint, so we return a filter dict suitable for Mongo find.
    """
    # escape regex special chars in user text (but keep spaces)
    pattern = re.escape(vehicle_text.strip())
    # allow partial matching and optional '125' etc. (case-insensitive)
    # e.g. 'honda shine', 'honda shine 125', 'shine 125'
    # Build regex to match anywhere in the type string
    regex = f".*{pattern}.*"

    or_conditions = [
        {"vehicles.four_wheeler.type": {"$regex": regex, "$options": "i"}},
        {"vehicles.two_wheeler_bike.type": {"$regex": regex, "$options": "i"}},
        {"vehicles.two_wheeler_scooty.type": {"$regex": regex, "$options": "i"}},
        # also check for exact top-level 'vehicle' keys if present
        {"vehicles.type": {"$regex": regex, "$options": "i"}},
    ]
    return {"$or": or_conditions}


# ================= STEP 5: MCP Tools (Django-only data access) =================
@mcp.tool()
def query_collection(collection: str, filter_dict: str = None, limit: int = 100) -> Dict[str, Any]:
    """Query a collection via Django API (POST)."""
    try:
        payload = {"collection": collection, "filter": json.loads(filter_dict) if filter_dict else {}, "limit": limit}
        return call_django_api("collections/query/", method="POST", data=payload)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def insert_document(collection: str, document: str) -> Dict[str, Any]:
    try:
        payload = {"collection": collection, "document": json.loads(document)}
        return call_django_api("collections/insert/", method="POST", data=payload)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def update_document(collection: str, filter_dict: str, update_dict: str) -> Dict[str, Any]:
    try:
        payload = {"collection": collection, "filter": json.loads(filter_dict), "update": json.loads(update_dict)}
        return call_django_api("collections/update/", method="POST", data=payload)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def delete_document(collection: str, filter_dict: str) -> Dict[str, Any]:
    try:
        payload = {"collection": collection, "filter": json.loads(filter_dict)}
        return call_django_api("collections/delete/", method="POST", data=payload)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def list_collections_via_django() -> Dict[str, Any]:
    """Return the list of collections via Django API."""
    return call_django_api("collections/", method="GET")


@mcp.tool()
def get_collection_info_via_django(collection: str) -> Dict[str, Any]:
    return call_django_api(f"collections/{collection}/info/", method="GET")


# ================= STEP 6: Natural-language command parser =================
@mcp.tool()
def smart_command(command: str) -> Dict[str, Any]:
    """
    Natural language handler (improved).
    Recognized intents (examples):
      - "who owns Honda Shine"
      - "who owns Honda Shine 125"
      - "which employee is from Frappe department"
      - "list employees"
      - "show engineers from Thane with salary above 60000"
      - "add new engineer named Rohan in Pune with salary 85000"
    """
    try:
        cmd = (command or "").strip().lower()

        # ---------- 1) list all collections ----------
        if ("list" in cmd or "show" in cmd) and "collection" in cmd:
            return mcp.call_tool("list_collections_via_django")

        # ---------- 2) list employees ----------
        if "list" in cmd and "employee" in cmd:
            res = mcp.call_tool("query_collection", collection="employees")
            docs = res.get("documents", [])
            return {"status": "success", "table": format_as_table(docs)}

        # ---------- 3) who owns <vehicle> ----------
        m = re.search(r"who (?:owns|has|own) (?:a |an |the )?(.+)", cmd)
        if m:
            vehicle_text = m.group(1).strip()
            # sanitize short trailing punctuation
            vehicle_text = re.sub(r"[^\w\s\-]", "", vehicle_text)
            # build a Mongo-style filter searching nested vehicle type fields
            vehicle_filter = _build_vehicle_regex_filter(vehicle_text)
            # query via django
            res = mcp.call_tool("query_collection", collection="employees", filter_dict=json.dumps(vehicle_filter), limit=200)
            if "error" in res:
                return {"error": res["error"]}
            docs = res.get("documents", [])
            if not docs:
                return {"status": "success", "message": f"No employees found owning '{vehicle_text}'", "table": "No records found."}
            return {"status": "success", "vehicle": vehicle_text, "table": format_as_table(docs)}

        # ---------- 4) which employee is from <department> / <dept> ----------
        m2 = re.search(r"(?:which|who).*\bfrom\b\s+([a-zA-Z0-9_\- ]+)(?:\s+department)?", cmd)
        if m2 and ("department" in cmd or "dept" in cmd or "which" in cmd or "who" in cmd):
            dept = m2.group(1).strip().title()
            f = {"department": dept}
            res = mcp.call_tool("query_collection", collection="employees", filter_dict=json.dumps(f), limit=200)
            if "error" in res:
                return {"error": res["error"]}
            docs = res.get("documents", [])
            if not docs:
                return {"status": "success", "message": f"No employees found in department '{dept}'", "table": "No records found."}
            return {"status": "success", "department": dept, "table": format_as_table(docs)}

        # ---------- 5) natural filtering: show engineers from Thane with salary above X ----------
        if "show" in cmd or "find" in cmd or "filter" in cmd:
            f = {}
            dep = re.search(r"(engineer|sales|finance|hr|marketing|frappe)", cmd)
            if dep:
                f["department"] = dep.group(1).capitalize()
            city = re.search(r"from\s+([a-zA-Z]+)", cmd)
            if city:
                f["city"] = city.group(1).capitalize()
            sal = re.search(r"(?:above|greater than|over)\s*(\d+)", cmd)
            if sal:
                f["salary"] = {"$gt": int(sal.group(1))}
            res = mcp.call_tool("query_collection", collection="employees", filter_dict=json.dumps(f), limit=200)
            if "error" in res:
                return {"error": res["error"]}
            docs = res.get("documents", [])
            return {"filter": f, "status": "success", "table": format_as_table(docs)}

        # ---------- 6) add / insert new employee ----------
        if "add" in cmd or "insert" in cmd or "create" in cmd:
            name_match = re.search(r"named\s+([a-zA-Z\s]+)", cmd)
            city_match = re.search(r"in\s+([a-zA-Z]+)", cmd)
            dept_match = re.search(r"(engineer|sales|finance|hr|marketing|frappe)", cmd)
            sal_match = re.search(r"salary\s*(\d+)", cmd)
            if not name_match or not dept_match or not city_match:
                return {"error": "Missing required details (name, department, city)."}
            name = name_match.group(1).strip().title()
            city = city_match.group(1).capitalize()
            dept = dept_match.group(1).capitalize()
            salary = int(sal_match.group(1)) if sal_match else 50000
            doc = {
                "name": name,
                "department": dept,
                "salary": salary,
                "city": city,
                "joinDate": pd.Timestamp.now().isoformat()
            }
            return mcp.call_tool("insert_document", collection="employees", document=json.dumps(doc))

        # ---------- 7) delete / remove ----------
        if "remove" in cmd or "delete" in cmd:
            name_match = re.search(r"(?:named|employee)\s+([a-zA-Z\s]+)", cmd)
            dept_match = re.search(r"from\s+(?:the\s+)?([a-zA-Z]+)", cmd)
            if not name_match:
                return {"error": "Missing employee name."}
            name = name_match.group(1).strip().title()
            f = {"name": name}
            if dept_match:
                f["department"] = dept_match.group(1).capitalize()
            return mcp.call_tool("delete_document", collection="employees", filter_dict=json.dumps(f))

        return {"message": "Command not recognized. Try: 'who owns Honda Shine', 'list employees', 'show engineers from Thane above 60000', 'add new engineer named Rohan in Pune with salary 85000'."}

    except Exception as e:
        return {"error": str(e)}


# ================= STEP 7: Health & helper tools =================
@mcp.tool()
def django_health_check() -> Dict[str, Any]:
    try:
        res = call_django_api("collections/", method="GET")
        if "error" in res:
            return {"status": "unhealthy", "error": res["error"]}
        return {"status": "healthy", "collections": res.get("collections", [])}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@mcp.tool()
def create_plot(data_source: str, x_field: str, y_field: str, chart_type: str = "line") -> Dict[str, Any]:
    """Generate charts from Django API results (keeps previous plot behavior)."""
    try:
        data = {"collection": data_source, "limit": 500}
        result = call_django_api("collections/query/", method="POST", data=data)
        docs = result.get("documents", [])
        df = pd.DataFrame(docs)
        if df.empty:
            return {"error": "No data found"}
        filename = f"plot_{uuid.uuid4().hex[:8]}.png"
        path = os.path.join(OUTPUT_DIR, filename)
        plt.figure(figsize=(10, 6))
        df.plot(x=x_field, y=y_field, kind=chart_type.lower(), ax=plt.gca())
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        return {"file_path": path, "status": "success"}
    except Exception as e:
        return {"error": str(e)}


# ================= STEP 8: Run App =================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", default="http", help="Transport type (http or stdio)")
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP")
    args = parser.parse_args()

    print(f"🚀 Starting MCP server (bi-universal) on {args.host}:{args.port}", file=sys.stderr)
    mcp.run(transport="http", host=args.host, port=args.port)