const fallbackApiBaseUrl = "http://localhost:8000";

export type SearchPapersRequest = {
  query: string;
  max_results?: number;
};

export type IndexPaperRequest = {
  paper_id: string;
};

export type ResearchChatRequest = {
  question: string;
  paper_ids?: string[];
  top_k?: number;
};

export type PaperSearchResult = {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  published_at: string;
  updated_at: string;
  categories: string[];
  pdf_url: string | null;
  source_url: string;
  primary_category: string | null;
};

export type IngestPaperRequest = {
  id: string;
  title: string;
  pdf_url: string | null;
  source_url: string;
  authors?: string[];
  abstract?: string;
  published_at?: string;
  updated_at?: string;
  categories?: string[];
  primary_category?: string | null;
};

export type SearchPapersResponse = {
  query: string;
  count: number;
  results: PaperSearchResult[];
};

export type IngestPaperResponse = {
  paper_id: string;
  status: "completed" | "cached";
  pdf_path: string;
  parsed_path: string;
  page_count: number;
  word_count: number;
  message: string;
};

export type IndexPaperResponse = {
  paper_id: string;
  status: "completed" | "cached";
  chunk_count: number;
  collection_name: string;
  message: string;
};

export type ChatCitation = {
  label: string;
  paper_id: string;
  paper_title: string;
  page_number: number;
  chunk_id: string;
  source_url: string;
};

export type RetrievedChunk = {
  label?: string | null;
  chunk_id: string;
  paper_id: string;
  paper_title: string;
  page_number: number;
  chunk_index: number;
  page_chunk_index: number;
  source_url: string;
  pdf_path: string;
  text: string;
  word_count: number;
  start_word_index: number;
  end_word_index: number;
  similarity_score?: number | null;
};

export type ResearchChatResponse = {
  status: "completed" | "partial";
  question: string;
  answer: string | null;
  citations: ChatCitation[];
  retrieved_chunks: RetrievedChunk[];
  message: string;
};

type ApiErrorResponse = {
  detail?: string;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? fallbackApiBaseUrl;

export const apiRoutes = {
  health: "/api/health",
  searchPapers: "/api/search-papers",
  ingest: "/api/ingest",
  indexPaper: "/api/index-paper",
  chat: "/api/chat",
  compare: "/api/compare",
} as const;

export function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export async function searchPapers(
  payload: SearchPapersRequest,
): Promise<SearchPapersResponse> {
  const response = await fetch(buildApiUrl(apiRoutes.searchPapers), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  await ensureSuccessfulResponse(response, "Unable to search papers right now.");
  return (await response.json()) as SearchPapersResponse;
}

export async function ingestPaper(
  payload: IngestPaperRequest,
): Promise<IngestPaperResponse> {
  const response = await fetch(buildApiUrl(apiRoutes.ingest), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  await ensureSuccessfulResponse(response, "Unable to ingest this paper right now.");
  return (await response.json()) as IngestPaperResponse;
}

export async function indexPaper(
  payload: IndexPaperRequest,
): Promise<IndexPaperResponse> {
  const response = await fetch(buildApiUrl(apiRoutes.indexPaper), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  await ensureSuccessfulResponse(response, "Unable to index this paper right now.");
  return (await response.json()) as IndexPaperResponse;
}

export async function researchChat(
  payload: ResearchChatRequest,
): Promise<ResearchChatResponse> {
  const response = await fetch(buildApiUrl(apiRoutes.chat), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  await ensureSuccessfulResponse(
    response,
    "Unable to generate a grounded answer right now.",
  );
  return (await response.json()) as ResearchChatResponse;
}

async function ensureSuccessfulResponse(
  response: Response,
  fallbackMessage: string,
): Promise<void> {
  if (!response.ok) {
    let message = fallbackMessage;

    try {
      const errorPayload = (await response.json()) as ApiErrorResponse;
      if (typeof errorPayload.detail === "string" && errorPayload.detail.trim()) {
        message = errorPayload.detail;
      }
    } catch {
      // Fall back to a generic message when the error body is unavailable.
    }

    throw new ApiError(message, response.status);
  }
}
