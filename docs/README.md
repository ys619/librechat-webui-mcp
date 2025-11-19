# MCP React + FastAPI Dashboard

## Quick dev run (local)

1. Start your local services (mongo, ollama, bi-universal MCP) via your docker-compose as you already do.

2. Start backend:
   ```bash
   cd backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install fastapi uvicorn requests pydantic
   uvicorn app:app --reload --port 9000
