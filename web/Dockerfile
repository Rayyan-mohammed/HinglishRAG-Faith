# Stage 1: build the React frontend. Node is only needed at build time -- the running
# container is Python-only, so this doesn't add to runtime image size or cold-start.
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: the actual runtime image.
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY data/ data/
COPY --from=frontend-build /app/frontend/dist frontend/dist

# HF Spaces sets PORT (default 7860); bge-m3 downloads on first startup, not baked into the
# image, so the first request after a fresh deploy is slower than subsequent ones.
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT}"]
