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

# Lambda Web Adapter -- lets AWS Lambda run this as a normal HTTP server (uvicorn) instead of
# needing the app rewritten to Lambda's native handler/event format. It proxies Lambda Function
# URL requests to the local port below. No-op outside Lambda (Cloud Run/plain Docker just ignore
# the extra binary sitting in /opt).
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY data/ data/
COPY --from=frontend-build /app/frontend/dist frontend/dist

# PORT: what our own CMD binds uvicorn to. AWS_LWA_PORT: what the Lambda Web Adapter forwards
# incoming requests to -- kept identical to PORT so there's no mismatch. HF_HOME redirects the
# bge-m3 model cache to /tmp, since everything outside /tmp is read-only at Lambda runtime (see
# INDEX_DIR in backend/main.py for the same reasoning applied to the FAISS index).
ENV PORT=8080
ENV AWS_LWA_PORT=8080
ENV HF_HOME=/tmp/hf_cache
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT}"]
