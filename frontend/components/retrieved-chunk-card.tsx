import { ArrowUpRight, FileText } from "lucide-react";

import { StatusChip } from "@/components/status-chip";
import type { RetrievedChunk } from "@/lib/api";

type RetrievedChunkCardProps = {
  chunk: RetrievedChunk;
};

export function RetrievedChunkCard({ chunk }: RetrievedChunkCardProps) {
  return (
    <article className="rounded-[1.6rem] border border-black/10 bg-white/80 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.22em] text-[color:var(--muted)]">
            [{chunk.label ?? chunk.chunk_id}] {chunk.paper_id}
          </p>
          <h4 className="mt-2 text-xl text-slate-900">{chunk.paper_title}</h4>
          <p className="mt-1 text-sm text-[color:var(--muted)]">
            Page {chunk.page_number} - chunk {chunk.chunk_index + 1} - page slice {chunk.page_chunk_index + 1}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <StatusChip tone="neutral">{chunk.word_count} words</StatusChip>
          {typeof chunk.similarity_score === "number" ? (
            <StatusChip tone="neutral">
              similarity {chunk.similarity_score.toFixed(2)}
            </StatusChip>
          ) : null}
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-black/10 bg-[#f6f0e7] p-4">
        <p className="whitespace-pre-line text-sm leading-6 text-slate-800">{chunk.text}</p>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <a
          href={chunk.source_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 rounded-2xl border border-black/10 bg-white/85 px-4 py-2 text-sm text-slate-800 transition hover:border-[color:var(--accent)]/40 hover:text-[color:var(--accent)]"
        >
          <ArrowUpRight className="h-4 w-4" />
          Open paper source
        </a>

        <div className="inline-flex items-center gap-2 rounded-2xl border border-black/10 bg-white/70 px-4 py-2 text-sm text-[color:var(--muted)]">
          <FileText className="h-4 w-4" />
          {chunk.pdf_path}
        </div>
      </div>
    </article>
  );
}
