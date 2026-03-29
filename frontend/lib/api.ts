const fallbackApiBaseUrl = "http://localhost:8000";

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
