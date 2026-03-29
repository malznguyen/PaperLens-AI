const fallbackApiBaseUrl = "http://localhost:8000";

export type SearchPapersRequest = {
  query: string;
  max_results?: number;
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

export type SearchPapersResponse = {
  query: string;
  count: number;
  results: PaperSearchResult[];
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

  if (!response.ok) {
    let message = "Unable to search papers right now.";

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

  return (await response.json()) as SearchPapersResponse;
}
