import { ArrowUpRight, Quote } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import type { ChatCitation } from "@/lib/api";

type CitationListProps = {
  citations: ChatCitation[];
};

export function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) {
    return (
      <EmptyState
        compact
        title="No citations attached"
        description="No citation labels were attached to this response. Try a narrower question or a tighter paper filter."
      />
    );
  }

  return (
    <div className="rounded-[1.6rem] border border-[color:var(--line)] bg-white/82 p-5">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl border border-[color:var(--line)] bg-[color:var(--accent-soft)] p-3 text-[color:var(--accent)]">
          <Quote className="h-5 w-5" />
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-[color:var(--muted)]">
            Citations
          </p>
          <h3 className="text-[1.45rem] text-slate-900">Trace the answer back to paper pages.</h3>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {citations.map((citation) => (
          <a
            key={citation.chunk_id}
            href={citation.source_url}
            target="_blank"
            rel="noreferrer"
            className="grid gap-3 rounded-[1.35rem] border border-[color:var(--line)] bg-[#f6f0e7] px-4 py-4 transition hover:border-[color:var(--accent)]/40 hover:bg-[#f2ebe0] md:grid-cols-[minmax(0,1fr)_auto] md:items-start"
          >
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-[color:var(--line)] bg-white/78 px-2.5 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-700">
                  {citation.label}
                </span>
                <p className="text-[11px] uppercase tracking-[0.18em] text-[color:var(--muted)]">
                  {citation.paper_id}
                </p>
              </div>
              <p className="mt-3 text-pretty text-base leading-6 text-slate-900">
                {citation.paper_title}
              </p>
              <p className="mt-2 break-all font-mono text-[12px] leading-6 text-[color:var(--muted)]">
                Page {citation.page_number} | chunk {citation.chunk_id}
              </p>
            </div>

            <div className="shrink-0 rounded-2xl border border-[color:var(--line)] bg-white/82 p-2 text-[color:var(--accent)]">
              <ArrowUpRight className="h-4 w-4" />
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
