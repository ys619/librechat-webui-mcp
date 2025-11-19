# Dockerfile.django - For Django REST API
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for MySQL/PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY . /app

# Create static/media directories
RUN mkdir -p /app/staticfiles /app/media

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBUG=True

# Expose port
EXPOSE 8001

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]