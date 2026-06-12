# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime

RUN groupadd --system translator \
    && useradd --system --gid translator --home-dir /app translator

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/

RUN chown -R translator:translator /app
USER translator

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.getenv('PORT', '8000') + '/health')"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
