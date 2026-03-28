# --- Frontend (Vite) ---
FROM node:20-alpine AS frontend-build
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
# Same-origin API in production container
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

# --- Backend (FastAPI) ---
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN chmod +x /app/entrypoint.sh
COPY --from=frontend-build /src/frontend/dist ./static

ENV PYTHONUNBUFFERED=1
ENV STATIC_ROOT=/app/static
ENV PORT=8000

EXPOSE 8000
CMD ["/app/entrypoint.sh"]
