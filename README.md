# PaperLens AI

PaperLens AI is a workflow-first scientific research assistant that discovers, ingests, indexes, and analyzes academic papers with full citation traceability. Every generated answer, comparison, and synthesis is grounded in retrieved evidence from real paper content -- nothing is invented.

## Key features

- **arXiv search** -- topic-based paper discovery with normalized metadata
- **PDF ingestion** -- download and parse papers into structured page-level text
- **Local indexing** -- chunk, embed (BGE), and store in Chroma for semantic retrieval
- **Grounded research chat** -- retrieval-augmented Q&A with page-level citations
- **Structured comparison** -- side-by-side table comparing 2-5 papers across methodology, datasets, strengths, limitations, and contributions
- **Topic synthesis** -- literature-review style overview with themes, trends, gaps, and future directions
- **Full provenance** -- every workflow exposes the retrieved chunks, citation labels, and timing metrics so outputs can be audited

## Architecture

```text
+-----------------------+         +---------------------------+
|   Next.js Frontend    |  HTTP   |     FastAPI Backend        |
|   (React 19 + TW)     | ------> |                           |
+-----------------------+         |  Routes (thin validation)  |
                                  |    |                       |
                                  |  Services (business logic) |
                                  |    |                       |
                                  |  Workflows (orchestration) |
                                  |    |                       |
                                  |  Repositories (Chroma, FS) |
                                  +---------------------------+
                                           |
                                  +---------------------------+
                                  |   Local Data Layer         |
                                  |   raw_pdfs/ parsed/ cache/ |
                                  |   chroma/ (vector DB)      |
                                  +---------------------------+
                                           |
                                  +---------------------------+
                                  |   External Services        |
                                  |   arXiv API, OpenRouter    |
                                  +---------------------------+
```

**Workflow pipeline:** Search --> Ingest --> Index --> Chat / Compare / Synthesis

Each workflow follows retrieve --> rerank --> generate --> cite, and every response includes the evidence package so the UI can show what the model actually saw.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11, Pydantic |
| Embeddings | sentence-transformers (BGE-small-en-v1.5) |
| Reranking | cross-encoder/ms-marco-MiniLM-L6-v2 |
| Vector DB | Chroma (local, persistent) |
| LLM | OpenRouter API (configurable model) |
| PDF parsing | PyMuPDF (fitz) |
| Testing | pytest (backend), TypeScript strict mode, Next.js production build, Playwright smoke tests |

## Setup and run

### Prerequisites

- Python 3.11+
- Node.js 20+
- An OpenRouter API key (free tier works)

### 1. Clone and configure

```bash
git clone <repo-url>
cd paperlens_ai
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Runtime data stays under `backend/data/` by default. The committed `.gitkeep` files keep the folder structure, but downloaded PDFs, parsed JSON, cache files, and Chroma indexes are generated locally and ignored by Git.

### 2. Start the backend

```bash
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate          # Windows cmd / PowerShell
# source .venv/bin/activate     # macOS / Linux / Git Bash

pip install -r backend/requirements.txt
cd backend
python -m uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`. Verify with:

```bash
curl http://localhost:8000/api/health
```

### 3. Start the frontend

Open a separate terminal at the repo root:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`.

### 4. Alternative: Docker Compose

```bash
docker compose up --build
```

This starts both services together.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Runtime environment |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS origins |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Frontend API target |
| `ARXIV_BASE_URL` | `https://export.arxiv.org/api/query` | arXiv Atom endpoint |
| `OPENROUTER_API_KEY` | (required) | OpenRouter authentication |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter endpoint |
| `OPENROUTER_MODEL` | `openrouter/free` | LLM model identifier |
| `OPENROUTER_TIMEOUT_SECONDS` | `45` | Generation timeout |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model name |
| `RETRIEVAL_TOP_K_DEFAULT` | `6` | Default retrieval count |
| `RETRIEVAL_TOP_K_MAX` | `12` | Maximum retrieval count |
| `RERANKING_ENABLED` | `true` | Cross-encoder reranking toggle |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L6-v2` | Reranker model |
| `DATA_DIR` | `backend/data` | Root data directory (relative paths resolve from the repo root) |
| `CHROMA_DIR` | `backend/data/chroma` | Chroma persistence path (relative paths resolve from the repo root) |

## Typical user workflow

1. **Search** -- go to the Search page, enter a topic like "vision transformers", review results
2. **Ingest** -- click "Ingest" on 2-3 papers to download and parse their PDFs
3. **Index** -- click "Index" on each ingested paper to chunk, embed, and store in Chroma
4. **Chat** -- go to the Chat page, enter paper IDs, ask a grounded question
5. **Compare** -- go to the Compare page, enter 2-5 paper IDs, generate a structured comparison table
6. **Synthesis** -- on the Compare page, switch to synthesis mode, enter a topic to get a literature overview

Each step preserves provenance: paper IDs, page numbers, and chunk labels flow through the entire pipeline.

### Demo corpus setup

For a repeatable demo, search for `"attention mechanism transformer"` and ingest+index the first 3 papers. Then use those paper IDs across chat, compare, and synthesis. See `docs/demo_script.md` for the full walkthrough.

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | System health check |
| POST | `/api/search-papers` | arXiv topic search |
| POST | `/api/ingest` | Download PDF + parse text |
| POST | `/api/index-paper` | Chunk + embed + index to Chroma |
| POST | `/api/chat` | Grounded Q&A with citations |
| POST | `/api/compare` | Multi-paper structured comparison |
| POST | `/api/summarize-topic` | Literature synthesis |

## Testing

### Full validation

Run the whole validation suite from the repository root:

```bash
python scripts/run_all_tests.py
```

The runner executes, in order:

1. backend pytest suite
2. frontend typecheck
3. frontend production build
4. Playwright browser smoke tests

It stops on the first critical failure and prints clear step labels while it runs.

### Prerequisites for automated tests

- Backend dependencies installed from `backend/requirements.txt`
- Frontend dependencies installed with `npm install` inside `frontend`
- Playwright Chromium installed once with:

```bash
cd frontend
npx playwright install chromium
```

Automated tests are deterministic and do **not** require live arXiv or OpenRouter access.

### Backend-only commands

```bash
cd backend
python -m pytest -q
```

Run only the API route harness:

```bash
cd backend
python -m pytest -q tests/test_api_routes.py
```

### Frontend-only commands

```bash
cd frontend
npm run typecheck
npm run build
npm run smoke
```

The smoke suite starts the built Next.js app on an isolated local port and mocks backend responses for the main workflow screens.

For the full testing guide, see [docs/testing.md](docs/testing.md).

## Repository structure

```text
paperlens_ai/
  frontend/
    app/              # Next.js pages (dashboard, search, chat, compare)
    components/       # React components (experiences, UI atoms, cards)
    lib/              # API client, utilities, paper-id parsing
  backend/
    app/
      api/routes/     # FastAPI route handlers (thin validation)
      core/           # Config, logging
      services/       # Business logic (citation, evaluation, embedding, ...)
      workflows/      # Orchestration (chat, compare, synthesis, ingest, indexing)
      schemas/        # Pydantic request/response models
      repositories/   # Chroma vector DB interface
      utils/          # File, text, prompt, hash utilities
    data/             # Runtime-generated local storage (.gitkeep only committed)
    tests/            # pytest test suite
  docs/               # Architecture docs, demo script, report outline
  .env.example        # Environment variable template
  docker-compose.yml  # Local development setup
```

## Limitations

- No persistent user sessions or authentication -- all state is local to the running instance
- No database beyond Chroma -- paper metadata lives in the file system
- LLM quality depends on the OpenRouter model and free-tier rate limits
- PDF parsing may miss complex layouts, tables, or math-heavy content
- Embedding model is small (BGE-small) for fast local inference, not state-of-the-art accuracy
- No concurrent multi-user support -- designed as a single-user research tool
- arXiv search uses the public Atom API with its rate limits

## Future improvements

- Persistent paper workspace with saved sessions and search history
- Streaming LLM responses for better perceived latency
- Support for non-arXiv paper sources (Semantic Scholar, DOI lookup)
- Fine-grained section-level parsing (abstract, methods, results extraction)
- User-configurable comparison dimensions
- Export comparison tables and synthesis to PDF/Markdown
- Multi-turn conversation with context carry-over
- Improved citation resolution with in-text inline markers
