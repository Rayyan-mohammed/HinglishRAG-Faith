"""FastAPI backend for the public CodeSwitch-Verify demo.

Reuses the same pipeline as demo/app.py (the Streamlit version in the main project) -- see
pipeline_src/, a deliberately self-contained copy of ../../src + ../../config/settings.py, kept
in sync manually. web/README.md explains why this is a copy, not an import."""

import sys
import time
from collections import defaultdict, deque
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline_src.pipeline import answer_question
from pipeline_src.retrieval import build_index

BACKEND_DIR = Path(__file__).resolve().parent
WEB_ROOT = BACKEND_DIR.parent
SCHEMES_DIR = WEB_ROOT / "data" / "schemes"
# /tmp specifically -- on AWS Lambda (and some other serverless container runtimes) everything
# outside /tmp is a read-only filesystem at runtime, even though it's writable at image build
# time. Using /tmp everywhere keeps this portable across Lambda, Cloud Run, and plain Docker.
INDEX_DIR = Path("/tmp/index")
FRONTEND_DIR = WEB_ROOT / "frontend" / "dist"

app = FastAPI(title="CodeSwitch-Verify")

_index = None
_passages = None

# Simple per-IP rate limit -- this endpoint is public, unauthenticated, and calls a paid API.
# Not a substitute for real infra, just a cheap guard against runaway cost from bots/scrapers.
RATE_LIMIT = 10  # requests
RATE_WINDOW_SECONDS = 60
_request_log = defaultdict(deque)


@app.on_event("startup")
def startup():
    global _index, _passages
    _index, _passages = build_index(schemes_dir=str(SCHEMES_DIR), index_dir=str(INDEX_DIR))


def _check_rate_limit(client_ip):
    now = time.time()
    log = _request_log[client_ip]
    while log and now - log[0] > RATE_WINDOW_SECONDS:
        log.popleft()
    if len(log) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests -- max {RATE_LIMIT} per {RATE_WINDOW_SECONDS}s. Try again shortly.",
        )
    log.append(now)


class AskRequest(BaseModel):
    question: str
    verify: bool = True


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
def ask(req: AskRequest, request: Request):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    _check_rate_limit(request.client.host)

    result = answer_question(req.question, _index, _passages, verify=req.verify)

    response = {
        "answer": result["answer"],
        "context_passages": [
            {"source": p["source"], "text": p["text"], "score": float(p["score"])}
            for p in result["context_passages"]
        ],
    }
    if req.verify:
        response["claims"] = [
            {
                "claim": c["claim"],
                "verdict": c["verdict"],
                "confidence": float(c["confidence"]),
            }
            for c in result["claims"]
        ]
    return response


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    print(f"WARNING: {FRONTEND_DIR} not found -- run `npm run build` in web/frontend first. "
          f"API endpoints (/api/*) still work without it.")
