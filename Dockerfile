# ---- Stage 1: build the React SPA ----
FROM node:22-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python control plane serving the built SPA ----
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY findings ./findings
COPY scripts ./scripts
COPY policy.yaml ./policy.yaml
COPY --from=frontend /fe/dist ./frontend/dist

EXPOSE 8000
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
