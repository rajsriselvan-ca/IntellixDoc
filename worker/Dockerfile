FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest version
RUN pip install --upgrade pip setuptools wheel

# Copy backend requirements (from parent context)
COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir --default-timeout=100 -r /tmp/backend-requirements.txt

# Copy worker requirements
COPY worker/requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy backend code (needed for imports)
COPY backend /app/backend

# Copy worker code
COPY worker /app

# Create uploads and data directories
RUN mkdir -p uploads backend/data

# Set Python path
ENV PYTHONPATH=/app:/app/backend

CMD ["rq", "worker", "--url", "redis://redis:6379/0", "default"]

