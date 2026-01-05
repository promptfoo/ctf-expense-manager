# CTF Expense Manager Dockerfile for Cloud Run
FROM python:3.14-slim

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files (README needed for pyproject.toml metadata)
COPY pyproject.toml README.md ./

# Copy source code (needed for installation)
COPY src/ ./src/

# Install package and dependencies
RUN uv pip install --system --no-cache .

# Copy config
COPY config.yaml ./

# Create non-root user
RUN useradd -m -u 1000 ctfuser && chown -R ctfuser:ctfuser /app
USER ctfuser

# Expose port
EXPOSE 8080

# Use gunicorn for production with module path
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 300 "ctf_expense_manager.server:app"
