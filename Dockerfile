# Backend
FROM python:3.12-slim AS backend
WORKDIR /app/backend
RUN groupadd -r campaignpulse && useradd -r -g campaignpulse campaignpulse
COPY backend/requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt
COPY backend/app/ ./app/
COPY backend/migrations/ ./migrations/
EXPOSE 8000
USER campaignpulse
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci && npm cache clean --force
COPY frontend/ .
RUN npm run build
EXPOSE 3000
USER node
CMD ["npm", "start"]
