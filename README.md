# PaperLens AI

PaperLens AI is a workflow-first scientific research assistant for discovering, ingesting, and analyzing academic papers. This Phase 1 scaffold establishes a clean FastAPI + Next.js foundation that is ready for arXiv search, PDF ingestion, retrieval, and grounded generation in later phases.

## Phase 1 deliverables

- FastAPI backend scaffold with modular routing and `GET /api/health`
- Next.js dashboard shell with responsive research workspace pages
- Tailwind CSS styling tuned for a professional academic UI
- Local-first data directories prepared for PDFs, parsed text, cache, and Chroma
- Docker Compose setup for frontend and backend development

## Repository structure

```text
paperlens-ai/
  frontend/
    app/
      chat/
      compare/
      search/
      workspace/
      globals.css
      layout.tsx
      page.tsx
    components/
    lib/
    hooks/
    types/
    public/
    package.json
    tsconfig.json
    next.config.ts
  backend/
    app/
      api/
        routes/
      core/
      services/
      workflows/
      models/
      schemas/
      repositories/
      utils/
      main.py
    data/
      raw_pdfs/
      parsed/
      cache/
      chroma/
    tests/
    requirements.txt
  docs/
    Agent.md
    System_overview.md
  .env.example
  .gitignore
  docker-compose.yml
  README.md
```

## Major files

### Backend

- `backend/app/main.py` creates the FastAPI application, applies CORS, and mounts the API router.
- `backend/app/core/config.py` centralizes environment settings and data directory management.
- `backend/app/api/router.py` composes the health, search, ingest, chat, and compare route groups.
- `backend/app/services/` holds route-independent placeholder logic so future business workflows stay outside the API layer.
- `backend/tests/test_health.py` verifies that the health endpoint responds successfully.

### Frontend

- `frontend/app/layout.tsx` loads the global shell and shared typography.
- `frontend/components/app-shell.tsx` provides the sidebar, top bar, and main workspace frame.
- `frontend/app/page.tsx` is the dashboard landing page with workflow cards, status panels, and future session placeholders.
- `frontend/app/search/page.tsx`, `frontend/app/workspace/page.tsx`, `frontend/app/chat/page.tsx`, and `frontend/app/compare/page.tsx` define the main product sections.
- `frontend/lib/api.ts` provides the backend base URL helper and API path constants.

### Project setup

- `.env.example` documents the core runtime configuration for both apps.
- `docker-compose.yml` starts the frontend and backend together for local development.
- `.gitignore` excludes generated app data, local environment files, and the local reference docs in `docs/`.

## Local development

### 1. Prepare environment variables

Copy `.env.example` to `.env` and add values as needed.

### 2. Run the backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload
```

Backend health check:

```bash
curl http://localhost:8000/api/health
```

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

### 4. Run with Docker Compose

```bash
docker compose up --build
```

This starts:

- frontend on `http://localhost:3000`
- backend on `http://localhost:8000`

## Available Phase 1 endpoints

- `GET /api/health`
- `POST /api/search-papers`
- `POST /api/ingest`
- `POST /api/chat`
- `POST /api/compare`

The non-health endpoints are placeholder contracts for the upcoming implementation phases.

## Notes for coursework submission

- The architecture keeps route handlers thin and moves logic into services so future workflows remain explainable.
- The UI is intentionally framed as a research workspace rather than a generic chatbot demo.
- `docs/Agent.md` and `docs/System_overview.md` are kept as local reference files and are ignored by `.gitignore` per your instruction not to push them.

## Phase 2: arXiv search integration

Recommended next work:

1. Implement an `arxiv_service.py` that queries and normalizes arXiv Atom results.
2. Replace the placeholder `/api/search-papers` response with real paper metadata models.
3. Connect the Search Papers page to the backend with a simple topic search form and results list.
4. Add error states, loading states, and basic backend tests around the search service.
