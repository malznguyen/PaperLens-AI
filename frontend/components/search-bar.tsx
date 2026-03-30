import type { FormEventHandler } from "react";
import { LoaderCircle, Search } from "lucide-react";

const maxResultOptions = [5, 10, 15, 25];

type SearchBarProps = {
  query: string;
  maxResults: number;
  isLoading: boolean;
  errorMessage: string | null;
  onQueryChange: (value: string) => void;
  onMaxResultsChange: (value: number) => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
};

export function SearchBar({
  query,
  maxResults,
  isLoading,
  errorMessage,
  onQueryChange,
  onMaxResultsChange,
  onSubmit,
}: SearchBarProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <label
          htmlFor="paper-search-query"
          className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]"
        >
          Topic query
        </label>
        <div className="mt-2 flex items-center gap-2.5 rounded-[1.6rem] border border-[color:var(--line)] bg-white/88 px-4 py-4 shadow-panel sm:gap-3">
          <div className="shrink-0 rounded-2xl border border-[color:var(--line)] bg-[color:var(--accent-soft)] p-3 text-[color:var(--accent)]">
            <Search className="h-5 w-5" />
          </div>
          <input
            id="paper-search-query"
            name="query"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="vision transformer medical image classification"
            className="min-w-0 w-full border-0 bg-transparent text-base text-slate-900 outline-none placeholder:text-slate-400"
            autoComplete="off"
          />
        </div>
        {errorMessage ? (
          <p className="mt-2 text-sm text-[#8a4b3a]">{errorMessage}</p>
        ) : (
          <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">
            Try queries like &quot;retrieval augmented generation hallucination
            evaluation&quot; or &quot;graph neural networks drug discovery&quot;.
          </p>
        )}
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <label className="flex flex-col gap-2 text-sm text-[color:var(--muted)]">
          <span className="text-xs uppercase tracking-[0.24em]">Max results</span>
          <select
            name="maxResults"
            value={maxResults}
            onChange={(event) => onMaxResultsChange(Number(event.target.value))}
            className="w-full rounded-2xl border border-[color:var(--line)] bg-white/84 px-4 py-3 text-sm text-slate-900 outline-none sm:w-auto"
          >
            {maxResultOptions.map((option) => (
              <option key={option} value={option}>
                {option} papers
              </option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#13212d] px-5 py-3 text-sm font-medium text-white transition hover:bg-[#1b3040] disabled:cursor-not-allowed disabled:bg-slate-500 sm:w-auto"
        >
          {isLoading ? (
            <>
              <LoaderCircle className="h-4 w-4 animate-spin" />
              Searching
            </>
          ) : (
            <>
              <Search className="h-4 w-4" />
              Search arXiv
            </>
          )}
        </button>
      </div>

      <div className="rounded-[1.45rem] border border-dashed border-[color:var(--accent)]/30 bg-[color:var(--accent-soft)]/88 p-4">
        <p className="text-[11px] uppercase tracking-[0.24em] text-[color:var(--accent)]">
          Next steps
        </p>
        <p className="mt-2 text-sm leading-6 text-slate-800">
          Review the titles first, then ingest and index only the strongest candidates. The same
          paper IDs can move directly into Chat, Compare, or Synthesis.
        </p>
      </div>
    </form>
  );
}
