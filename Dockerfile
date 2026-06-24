# Backend
FROM python:3.12-slim AS backend
WORKDIR /app/backend
COPY backend/requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt
COPY backend/app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci && npm cache clean --force
COPY frontend/ .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
