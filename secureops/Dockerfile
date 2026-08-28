# Multi-stage production Dockerfile for SecureOps Gateway

# Stage 1: Build & Dependencies
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final Runtime Image
FROM python:3.11-slim as runner

WORKDIR /app

# Create non-root app user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY test_documents /app/test_documents

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
