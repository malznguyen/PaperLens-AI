# PaperLens AI -- Demo Script

Estimated time: 3-5 minutes. This script walks through the full workflow from search to synthesis.

## Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- `.env` configured with a valid `OPENROUTER_API_KEY`
- First run will download embedding and reranker models (~100 MB one-time)

## Step 1: Search (30 seconds)

1. Open `http://localhost:3000` in a browser
2. Click **Search** in the sidebar
3. Type `attention mechanism transformer` in the search box
4. Set max results to **5**
5. Click **Search arXiv**

**What to say:** "PaperLens starts with arXiv discovery. We search for a topic and get normalized metadata -- title, authors, abstract, categories, and a direct link to the paper source."

## Step 2: Ingest (45 seconds)

1. Click **Ingest** on the first 3 papers in the results
2. Wait for each to show a green "completed" or "cached" status
3. Point out the page count and word count returned for each

**What to say:** "Ingestion downloads the PDF and parses it page-by-page using PyMuPDF. We get a structured document with page-level text, which preserves provenance for later retrieval."

## Step 3: Index (45 seconds)

1. Click **Index** on each of the 3 ingested papers
2. Wait for each to show "indexed" or "cached" status
3. Note the chunk count returned (typically 30-80 chunks per paper)

**What to say:** "Indexing chunks the parsed text, generates BGE embeddings locally, and stores everything in Chroma. Each chunk keeps its paper ID, page number, and word boundaries so citations trace back to exact locations."

## Step 4: Chat (60 seconds)

1. Click **Chat** in the sidebar
2. In the Paper IDs field, paste the 3 paper IDs from step 3 (comma-separated)
3. Ask: `What are the main attention mechanisms proposed in these papers and how do they differ?`
4. Click **Send question**
5. Point out:
   - The grounded answer with `[S1]`, `[S2]` citation labels
   - The citation list showing paper title, page number, and source link
   - The evidence panel with the actual retrieved chunks
   - The workflow metrics (retrieval, reranking, generation timing)

**What to say:** "The chat workflow retrieves relevant chunks, reranks them with a cross-encoder, and asks the LLM to answer only from the provided evidence. Every citation label maps to a specific chunk with a page number, so you can verify any claim."

## Step 5: Compare (60 seconds)

1. Click **Compare** in the sidebar
2. Paste the same 3 paper IDs
3. Keep the default comparison prompt or customize it
4. Click **Compare indexed papers**
5. Point out:
   - The narrative summary at the top
   - The structured comparison table (objective, methodology, dataset, strengths, limitations, key contribution)
   - Citation badges on each table row showing which sources informed each paper's row
   - The citation list and evidence panel below

**What to say:** "Comparison retrieves evidence per-paper separately so no single paper dominates. The table is structured but grounded -- if a field isn't supported by evidence, it says so explicitly instead of guessing."

## Step 6: Synthesis (45 seconds)

1. Scroll down or switch to the synthesis tab on the Compare page
2. Enter topic: `attention mechanisms in transformer architectures`
3. Optionally paste the same paper IDs to restrict scope
4. Click **Generate topic synthesis**
5. Point out:
   - Overview paragraph
   - Structured lists: themes, trends, open challenges, research gaps, future directions
   - Citations grounding each section

**What to say:** "Topic synthesis generates a literature-review style overview. Themes and gaps are only surfaced when the retrieved evidence actually supports them. This is designed for coursework reporting, not open-ended generation."

## Fallback demo path

If OpenRouter generation fails (rate limit, timeout, or model unavailable):

1. **Show search + ingest + index** -- these are fully local and don't need the LLM
2. **Show a chat request** -- even if generation fails, the response returns `status: "partial"` with the retrieved chunks and citations visible
3. **Point out the evidence panel** -- explain that the retrieval and reranking pipeline works independently of generation
4. **Show the metrics card** -- retrieval and reranking timings still populate; generation shows the timeout

**What to say:** "The system is designed for graceful degradation. If the LLM is unavailable, retrieval still completes and the evidence package is fully visible. The UI shows a partial status so the user knows what happened."

## Key points to emphasize

- **Grounding first:** every answer traces back to specific paper pages
- **No hallucination by design:** the prompt instructs the model to refuse if evidence is insufficient
- **Visible provenance:** citations, chunks, page numbers, and source URLs are always exposed
- **Workflow-first:** structured stages (search, ingest, index, chat, compare, synthesis) instead of a generic chatbot
- **Local-first:** embeddings and vector search run locally; only LLM generation calls an external API
- **Evaluation built in:** every workflow returns timing metrics and evidence counts for analysis
