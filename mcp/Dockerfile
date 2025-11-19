# Dockerfile-MCP - FOR MCP SERVER
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application
COPY bi_universal.py .

# Create output directory
RUN mkdir -p /app/bi_outputs

# Environment variables
ENV DATABASE_TYPE=mongodb
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run MCP server
CMD ["python3", "bi_universal.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]