# CTF Expense Manager Dockerfile for Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 ctfuser && chown -R ctfuser:ctfuser /app
USER ctfuser

# Expose port
EXPOSE 8080

# Use gunicorn for production
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 300 server:app


