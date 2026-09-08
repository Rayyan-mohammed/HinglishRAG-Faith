# CodeSwitch-Verify — live demo

A faithfulness-checked RAG demo for Hinglish government-scheme Q&A (PM-KISAN, Ayushman Bharat,
Post-Matric Scholarship, PM Awas Yojana). Ask a question in Hinglish, get an answer, and — if
verification is on — see each claim in the answer checked against the retrieved evidence and
tagged SUPPORTED / CONTRADICTED / UNVERIFIABLE with a confidence score.

This is the deployable version of the pipeline built in the main `HinglishRAG-Faith` project.

## Structure

- `backend/main.py` — FastAPI app: `POST /api/ask`, `GET /api/health`, serves `frontend/` as
  static files.
- `backend/pipeline_src/` — a **deliberate, self-contained copy** of the main project's
  `src/*.py` + `config/settings.py`. It's a copy, not an import, because Cloud Run's
  `--source ./web` deploy only sees what's under `web/`, not the main repo's `../src`.
  **If the main project's pipeline changes, mirror the change here too if the live demo should
  reflect it.**
- `frontend/` — React (Vite + Tailwind + Framer Motion) single-page UI. Built at deploy time by
  the Dockerfile's Node stage (`npm run build` → `frontend/dist/`) — the running container is
  Python-only, Node is never present at runtime. `frontend/dist/` isn't committed (gitignored),
  same reasoning as the FAISS index below.
- `data/schemes/*.csv` — copy of the scheme facts dataset, needed to build the FAISS index inside
  the container (the index itself isn't committed — it's built fresh on every container start).

## Running locally

Two processes: the FastAPI backend, and (for frontend changes) the Vite dev server.

**Backend:**
```
cd web
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here   # or set in a .env file
uvicorn main:app --app-dir backend --reload
```
Runs at `http://localhost:8000` — serves the API and, if you've already built the frontend once
(`cd frontend && npm run build`), the built UI too.

**Frontend, with hot reload while developing:**
```
cd web/frontend
npm install
npm run dev
```
Runs at `http://localhost:5173` with API calls proxied to the backend on port 8000 (see
`vite.config.js`) — keep the backend running in the other terminal.

To produce the build the backend serves in production: `cd web/frontend && npm run build`.

## Configuration

Requires one secret: `ANTHROPIC_API_KEY`. On Google Cloud Run, this is stored in Secret Manager
and wired in via `--set-secrets` at deploy time — never commit it. See `DEPLOY.md`.

## Rate limiting

`/api/ask` is public and unauthenticated, and it calls a paid API — `backend/main.py` has a
simple in-memory per-IP rate limit (10 requests/minute by default) as a basic cost guard. This is
not a substitute for real infrastructure (it resets on restart and doesn't survive multiple
container replicas — Cloud Run can spin up more than one under load), just a cheap safety net for
a demo project.

## Deployment

See `DEPLOY.md` in this directory for the exact steps to deploy this to Google Cloud Run.
