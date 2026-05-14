# syntax=docker/dockerfile:1.7

# ---------- Stage 1: frontend build ----------
FROM node:20-alpine AS web-builder
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

# ---------- Stage 2: python runtime ----------
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/app /app/apps/api/app
COPY apps/api/fixtures /app/apps/api/fixtures

WORKDIR /app/apps/api
RUN pip install --no-cache-dir -e .

COPY --from=web-builder /web/dist /app/static

ENV STATIC_DIR=/app/static \
    CACHE_DB_PATH=/data/cache.sqlite
RUN mkdir -p /data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
