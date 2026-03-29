# Testing Guide

PaperLens AI now ships with a practical validation harness for backend APIs, frontend smoke coverage, and a single-command pre-demo check.

## What is covered

### Backend API integration coverage

The backend pytest suite covers all main routes:

- `GET /api/health`
- `POST /api/search-papers`
- `POST /api/ingest`
- `POST /api/index-paper`
- `POST /api/chat`
- `POST /api/compare`
- `POST /api/summarize-topic`

Coverage includes:

- success-path response shapes
- route-to-service error mapping
- invalid request validation for each major route
- cached ingest and indexing behavior
- deterministic ingest and index artifact handling
- grounded workflow fallbacks for chat, compare, and synthesis
- retrieval failure wrapping and reranker fallback behavior

### Frontend smoke coverage

The Playwright smoke suite validates the real Next.js UI with mocked API responses:

- dashboard page loads
- search page renders and submits a mocked search
- ingest and index actions update the search result card
- chat page renders and displays grounded answer output
- citation and evidence panels render from mocked responses
- compare page renders structured comparison output
- topic synthesis renders overview, lists, citations, and evidence

### Full validation runner

The repository-level runner executes:

1. backend tests
2. frontend typecheck
3. frontend build
4. browser smoke tests

The script fails fast on the first critical error and prints readable step headers.

## What is mocked

Automated tests do not depend on live third-party services.

### Backend mocks

- arXiv HTTP calls are mocked in search tests
- PDF download/parsing inputs are mocked or generated from deterministic fixture PDFs
- OpenRouter generation is stubbed in workflow and route tests
- Chroma, embeddings, reranking, and workflow services are replaced with local test doubles where appropriate

### Frontend mocks

- Playwright intercepts all backend API routes used by the UI smoke flow
- Search, ingest, index, chat, compare, and synthesis responses are served from deterministic local mock payloads

## What is not covered

The automated harness intentionally does not try to prove everything.

- Live arXiv integration against the public API
- Live OpenRouter generation quality or rate-limit behavior
- Full backend + frontend network integration in a single browser test
- Visual regression testing
- Performance/load testing

Those are better handled as optional manual demo checks, not default pre-submission validation.

## How to run everything

From the repository root:

```bash
python scripts/run_all_tests.py
```

Expected step output looks like:

- `Running backend tests...`
- `Running frontend typecheck...`
- `Running frontend build...`
- `Running browser smoke tests...`
- `All checks passed.`

## How to run only API tests

Run the full backend suite:

```bash
cd backend
python -m pytest -q
```

Run only the route integration harness:

```bash
cd backend
python -m pytest -q tests/test_api_routes.py
```

## How to run only UI/smoke tests

Build the frontend, then run Playwright:

```bash
cd frontend
npm run build
npm run smoke
```

The smoke suite starts the built Next.js app locally on port `3100`.

## Prerequisites

- Python environment with `backend/requirements.txt` installed
- Node.js dependencies installed in `frontend`
- Playwright Chromium installed once:

```bash
cd frontend
npx playwright install chromium
```

## Notes for local development

- The top-level runner automatically prefers the repository `.venv` or `venv` Python interpreter when present.
- Browser smoke tests use mocked backend responses, so they can run even when the FastAPI server is not started.
- Backend tests are the source of truth for API behavior; frontend smoke tests are intentionally lightweight and focus on wiring and render confidence.
