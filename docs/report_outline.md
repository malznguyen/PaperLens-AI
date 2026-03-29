# PaperLens AI -- Report Outline

## 1. Introduction

- Motivation: academic paper analysis requires grounded, traceable answers rather than open-ended generation
- Problem statement: existing tools either lack citation provenance or treat paper analysis as a generic chatbot task
- PaperLens AI: a workflow-first research assistant where every output traces back to specific paper pages
- Scope: arXiv paper discovery, PDF ingestion, local indexing, grounded Q&A, structured comparison, and literature synthesis

## 2. Objectives

- Build a retrieval-augmented generation (RAG) pipeline grounded in real paper content
- Preserve page-level citation provenance throughout every workflow stage
- Support structured multi-paper comparison with per-paper evidence isolation
- Generate literature-review style synthesis with explicit evidence backing
- Expose retrieval metrics and evidence packages so outputs are auditable, not opaque
- Design for local-first operation with minimal external dependencies

## 3. System architecture

### 3.1 High-level design

- Two-tier architecture: Next.js frontend + FastAPI backend
- Local data layer: file system (PDFs, parsed text, cache) + Chroma vector database
- External services: arXiv Atom API (search), OpenRouter API (LLM generation)
- Layered backend: routes (validation) --> services (logic) --> workflows (orchestration) --> repositories (data access)

### 3.2 Data flow

- Search --> Ingest --> Index --> Chat / Compare / Synthesis
- Each workflow follows: retrieve --> rerank --> generate --> cite
- Evidence package (retrieved chunks + citations + metrics) included in every response

### 3.3 Technology choices

- BGE-small-en-v1.5 for local embedding (fast, no API dependency)
- Chroma for persistent vector storage (lightweight, no server setup)
- cross-encoder/ms-marco-MiniLM-L6-v2 for reranking (improved retrieval precision)
- PyMuPDF for PDF parsing (page-level text extraction with positional metadata)
- OpenRouter for LLM generation (model-agnostic, free tier available)

## 4. Implementation by assignment stage

### Stage 1: Foundation and search integration

- FastAPI backend foundation with modular routing and configuration management
- Next.js dashboard shell with responsive research workspace layout
- arXiv Atom API integration with metadata normalization
- Search UI with paper cards displaying provenance (authors, categories, source links)

### Stage 2: Paper ingestion and indexing pipeline

- PDF download with timeout handling and error recovery
- PyMuPDF page-level text extraction preserving page boundaries
- Chunking service with configurable chunk size and overlap
- BGE embedding generation and Chroma vector storage
- Index caching to avoid redundant re-processing

### Stage 3: Grounded research chat

- Semantic retrieval over indexed chunks with paper-ID scoping
- Cross-encoder reranking for improved relevance
- Citation-aware prompt construction with labeled sources (S1, S2, ...)
- Citation resolution: mapping model-generated labels back to specific chunks
- Answer composition with appended source references
- UI with grounded answer, citation list, evidence panel, and workflow metrics

### Stage 4: Compare and synthesis workflows

- Per-paper evidence retrieval for comparison (prevents single-paper dominance)
- Structured comparison table generation (objective, methodology, dataset, strengths, limitations, key contribution)
- Topic synthesis with themes, trends, challenges, gaps, and future directions
- Graceful degradation: partial responses with evidence when generation fails
- Evaluation service tracking retrieval, reranking, and generation latency

## 5. Prompt engineering strategy

### 5.1 Grounding constraints

- System prompts instruct the model to answer only from provided evidence
- Explicit refusal instruction when evidence is insufficient
- Citation labels (S1, S2, ...) required in model output for traceability

### 5.2 Structured output

- JSON schema enforcement for comparison tables and synthesis fields
- Field-level evidence normalization (missing fields default to "Not stated in retrieved evidence")
- Pydantic validation on generated payloads to catch malformed outputs

### 5.3 Context construction

- Retrieved chunks labeled and deduplicated before prompt injection
- Per-paper isolation in comparison to ensure balanced representation
- Token-aware context truncation to stay within model limits

## 6. Evaluation metrics

### 6.1 Workflow-level metrics

- Retrieval latency (ms)
- Reranking latency (ms)
- Generation latency (ms)
- Total end-to-end latency (ms)
- Retrieved chunk count
- Citation count (how many sources the model actually referenced)

### 6.2 Quality indicators

- Status field: "completed" vs "partial" vs "failed" per workflow
- Insufficient evidence flag: model's self-reported confidence
- Evidence coverage: ratio of cited chunks to retrieved chunks
- Missing field count in comparison tables (fields defaulting to "Not stated")

### 6.3 Grounding assessment

- All citations map to real chunks with verifiable page numbers
- No generated content without corresponding evidence in the retrieved package
- Evidence panel in UI allows manual spot-checking of any claim

## 7. Limitations

- PDF parsing quality varies with document layout complexity (tables, math, multi-column)
- Embedding model (BGE-small) trades accuracy for local inference speed
- LLM quality depends on OpenRouter model selection and free-tier availability
- No persistent sessions or user authentication
- Single-user design without concurrent access support
- arXiv-only paper source (no Semantic Scholar, DOI, or manual upload)
- Chunk boundaries may split relevant context across multiple chunks
- No streaming responses -- full generation must complete before display

## 8. Future work

- Streaming LLM responses for better perceived latency
- Multi-source paper discovery (Semantic Scholar, DOI resolver, manual PDF upload)
- Section-level parsing (abstract, methods, results, discussion extraction)
- Persistent workspace with saved sessions and search history
- Multi-turn conversation with context carry-over
- User-configurable comparison dimensions
- Export to PDF/Markdown for direct use in reports
- Larger embedding models with quantization for better accuracy
- Fine-tuned reranker for academic domain specificity
- Automated evaluation pipeline comparing retrieval quality across configurations
