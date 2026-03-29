import { LibraryBig } from "lucide-react";

import type { PaperIndexState } from "@/components/index-button";
import type { PaperIngestState } from "@/components/ingest-button";
import { PaperCard } from "@/components/paper-card";
import { StatusChip } from "@/components/status-chip";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import type { PaperSearchResult } from "@/lib/api";

type SearchResultsProps = {
  results: PaperSearchResult[];
  activeQuery: string | null;
  pendingQuery: string | null;
  errorMessage: string | null;
  hasSearched: boolean;
  isLoading: boolean;
  ingestStates: Record<string, PaperIngestState>;
  indexStates: Record<string, PaperIndexState>;
  onIngestPaper: (paper: PaperSearchResult) => void;
  onIndexPaper: (paper: PaperSearchResult) => void;
};

export function SearchResults({
  results,
  activeQuery,
  pendingQuery,
  errorMessage,
  hasSearched,
  isLoading,
  ingestStates,
  indexStates,
  onIngestPaper,
  onIndexPaper,
}: SearchResultsProps) {
  if (!hasSearched) {
    return (
      <EmptyState
        title="Start with a research topic"
        description="Run a topic search to pull paper metadata from arXiv. The first result set will appear here."
      />
    );
  }

  if (isLoading && results.length === 0) {
    return (
      <LoadingState
        title="Searching arXiv"
        description="Pulling titles, authors, abstracts, and category metadata for your topic."
      />
    );
  }

  if (errorMessage && results.length === 0) {
    return (
      <ErrorState
        title="Search temporarily unavailable"
        description={errorMessage}
      />
    );
  }

  if (results.length === 0) {
    return (
      <EmptyState
        title="No papers matched that topic"
        description={`No results came back for "${activeQuery ?? "this search"}". Try broader keywords or a shorter phrase.`}
      />
    );
  }

  const resultLabel = results.length === 1 ? "paper" : "papers";

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-black/10 bg-[#f6f0e7] p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
              Active result set
            </p>
            <div className="mt-2 flex items-center gap-3">
              <div className="rounded-2xl border border-black/10 bg-white/75 p-2 text-[color:var(--accent)]">
                <LibraryBig className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-xl text-slate-900">
                  {results.length} {resultLabel} for &quot;{activeQuery}&quot;
                </h3>
                <p className="text-sm text-[color:var(--muted)]">
                  Normalized from the arXiv Atom feed. Ready to ingest and index.
                </p>
              </div>
            </div>
          </div>

          <StatusChip tone="positive">Metadata ready</StatusChip>
        </div>
      </div>

      {errorMessage ? (
        <ErrorState
          compact
          title="Could not refresh the latest search"
          description={`${errorMessage} Showing the last successful results instead.`}
        />
      ) : null}

      {isLoading && pendingQuery ? (
        <LoadingState
          compact
          title={`Refreshing for "${pendingQuery}"`}
          description="Keeping the last successful result set visible while the new search completes."
        />
      ) : null}

      <div className="space-y-3">
        {results.map((paper) => (
          <PaperCard
            key={`${paper.id}-${paper.updated_at}`}
            paper={paper}
            ingestState={ingestStates[paper.id]}
            indexState={indexStates[paper.id]}
            onIngest={onIngestPaper}
            onIndex={onIndexPaper}
          />
        ))}
      </div>
    </div>
  );
}
