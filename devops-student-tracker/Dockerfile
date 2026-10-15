# ==============================================================================
# DevOps Student Task Tracker - Production Dockerfile
# Base Image: Official Python 3.12 Slim
# ==============================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=local \
    PORT=5000

# Set working directory inside container
WORKDIR /app

# Install dependencies first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application assets and templates
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

# Create a secure non-root user and group
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash appuser && \
    chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose container port
EXPOSE 5000

# Health check using Python's standard library (avoids external curl dependency)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; res = urllib.request.urlopen('http://127.0.0.1:5000/health'); exit(0 if res.getcode() == 200 else 1)"

# Run using production Gunicorn WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
