import { type Page, type Route } from "@playwright/test";

export type RecordedApiCall = {
  path: string;
  body: unknown;
};

const searchResponse = {
  query: "vision transformer medical imaging",
  count: 1,
  results: [
    {
      id: "2401.12345",
      title: "Vision Transformers for Medical Imaging",
      authors: ["Alice Smith", "Bob Jones"],
      abstract:
        "Grounded benchmark study showing transformer trade-offs in medical image analysis.",
      published_at: "2024-01-10T12:00:00Z",
      updated_at: "2024-01-15T09:30:00Z",
      categories: ["cs.CV", "cs.LG"],
      pdf_url: "https://arxiv.org/pdf/2401.12345.pdf",
      source_url: "https://arxiv.org/abs/2401.12345",
      primary_category: "cs.CV",
    },
  ],
};

const ingestResponse = {
  paper_id: "2401.12345",
  status: "completed",
  pdf_path: "backend/data/raw_pdfs/2401.12345.pdf",
  parsed_path: "backend/data/parsed/2401.12345.json",
  page_count: 12,
  word_count: 4321,
  message: "Paper ingested and parsed successfully.",
};

const indexResponse = {
  paper_id: "2401.12345",
  status: "completed",
  chunk_count: 42,
  collection_name: "paper_chunks",
  message: "Paper indexed successfully.",
};

const citations = [
  {
    label: "S1",
    paper_id: "2401.12345",
    paper_title: "Vision Transformers for Medical Imaging",
    page_number: 2,
    chunk_id: "2401.12345-p2-c1",
    source_url: "https://arxiv.org/abs/2401.12345",
  },
  {
    label: "S2",
    paper_id: "2402.67890",
    paper_title: "Efficient Hybrid Medical Imaging Models",
    page_number: 5,
    chunk_id: "2402.67890-p5-c1",
    source_url: "https://arxiv.org/abs/2402.67890",
  },
];

const retrievedChunks = [
  {
    label: "S1",
    chunk_id: "2401.12345-p2-c1",
    paper_id: "2401.12345",
    paper_title: "Vision Transformers for Medical Imaging",
    page_number: 2,
    chunk_index: 0,
    page_chunk_index: 0,
    source_url: "https://arxiv.org/abs/2401.12345",
    pdf_path: "backend/data/raw_pdfs/2401.12345.pdf",
    text: "Grounded evidence: limited labeled data makes performance unstable.",
    word_count: 9,
    start_word_index: 0,
    end_word_index: 9,
    similarity_score: 0.91,
  },
  {
    label: "S2",
    chunk_id: "2402.67890-p5-c1",
    paper_id: "2402.67890",
    paper_title: "Efficient Hybrid Medical Imaging Models",
    page_number: 5,
    chunk_index: 0,
    page_chunk_index: 0,
    source_url: "https://arxiv.org/abs/2402.67890",
    pdf_path: "backend/data/raw_pdfs/2402.67890.pdf",
    text: "Grounded evidence: hybrid encoders reduce memory pressure in practice.",
    word_count: 10,
    start_word_index: 0,
    end_word_index: 10,
    similarity_score: 0.88,
  },
];

const chatResponse = {
  status: "completed",
  question: "What limitations are reported for these models?",
  answer:
    "Small-data performance remains fragile, and training can be memory-intensive.\n\nSources:\n[S1] Vision Transformers for Medical Imaging (2401.12345), p. 2\n[S2] Efficient Hybrid Medical Imaging Models (2402.67890), p. 5",
  citations,
  retrieved_chunks: retrievedChunks,
  meta: {
    retrieval_ms: 9,
    reranking_ms: 2,
    generation_ms: 21,
    total_ms: 34,
    retrieved_chunk_count: 2,
    citation_count: 2,
    status: "completed",
  },
  message: "Answer generated successfully.",
};

const compareResponse = {
  status: "completed",
  summary:
    "Grounded comparison summary. One paper emphasizes transformer-only modeling, while the other uses a hybrid design to reduce compute pressure.",
  comparison_table: [
    {
      paper_id: "2401.12345",
      paper_title: "Vision Transformers for Medical Imaging",
      objective: "Evaluate transformer-only classification on retinal images.",
      methodology: "Pure transformer encoder.",
      dataset: "EyePACS",
      strengths: "Strong feature abstraction.",
      limitations: "Sensitive to limited data.",
      key_contribution: "Transformer-only medical imaging benchmark.",
    },
    {
      paper_id: "2402.67890",
      paper_title: "Efficient Hybrid Medical Imaging Models",
      objective: "Improve efficiency for clinical image classification.",
      methodology: "Hybrid CNN-transformer encoder.",
      dataset: "ChestX-ray14",
      strengths: "Lower memory footprint.",
      limitations: "More architectural complexity.",
      key_contribution: "Hybrid encoder for practical deployment.",
    },
  ],
  citations,
  retrieved_chunks: retrievedChunks,
  meta: {
    retrieval_ms: 11,
    reranking_ms: 3,
    generation_ms: 24,
    total_ms: 41,
    retrieved_chunk_count: 2,
    citation_count: 2,
    status: "completed",
  },
  message: "Comparison generated successfully.",
};

const synthesisResponse = {
  status: "completed",
  topic: "Vision transformers in medical imaging",
  overview:
    "Transformer backbones are increasingly paired with hybrid designs to balance capacity and data efficiency.",
  themes: [
    "Transformer-based feature extraction",
    "Hybrid CNN-transformer modeling",
  ],
  trends: [
    "Evidence packages stay page-linked for auditing.",
    "Efficiency remains a recurring design target.",
  ],
  open_challenges: ["Small labeled datasets remain a bottleneck."],
  research_gaps: ["Cross-dataset generalization is inconsistently reported."],
  future_directions: ["Evaluate architectures across broader clinical imaging tasks."],
  citations,
  retrieved_chunks: retrievedChunks,
  meta: {
    retrieval_ms: 10,
    reranking_ms: 2,
    generation_ms: 22,
    total_ms: 36,
    retrieved_chunk_count: 2,
    citation_count: 2,
    status: "completed",
  },
  message: "Topic synthesis generated successfully.",
};

export async function installMockApi(page: Page): Promise<RecordedApiCall[]> {
  const recordedCalls: RecordedApiCall[] = [];

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());
    const body = request.postDataJSON?.() ?? null;

    if (request.method() === "POST") {
      recordedCalls.push({ path: pathname, body });
    }

    await fulfillMockRoute(route, pathname);
  });

  return recordedCalls;
}

async function fulfillMockRoute(route: Route, pathname: string): Promise<void> {
  switch (pathname) {
    case "/api/search-papers":
      await route.fulfill({ status: 200, json: searchResponse });
      return;
    case "/api/ingest":
      await route.fulfill({ status: 200, json: ingestResponse });
      return;
    case "/api/index-paper":
      await route.fulfill({ status: 200, json: indexResponse });
      return;
    case "/api/chat":
      await route.fulfill({ status: 200, json: chatResponse });
      return;
    case "/api/compare":
      await route.fulfill({ status: 200, json: compareResponse });
      return;
    case "/api/summarize-topic":
      await route.fulfill({ status: 200, json: synthesisResponse });
      return;
    default:
      await route.fulfill({
        status: 404,
        json: { detail: `Unhandled mocked route: ${pathname}` },
      });
  }
}
