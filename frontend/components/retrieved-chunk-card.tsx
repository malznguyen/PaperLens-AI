import { ArrowUpRight, FileText } from "lucide-react";

import { StatusChip } from "@/components/status-chip";
import type { RetrievedChunk } from "@/lib/api";

type RetrievedChunkCardProps = {
  chunk: RetrievedChunk;
};

export function RetrievedChunkCard({ chunk }: RetrievedChunkCardProps) {
  return (
    <article className="rounded-[1.6rem] border border-[color:var(--line)] bg-white/84 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.22em] text-[color:var(--muted)]">
            [{chunk.label ?? chunk.chunk_id}] {chunk.paper_id}
          </p>
          <h4 className="mt-2 max-w-4xl text-pretty text-[1.18rem] leading-tight text-slate-900 sm:text-[1.3rem]">
            {chunk.paper_title}
          </h4>
          <p className="mt-1 text-sm text-[color:var(--muted)]">
            Page {chunk.page_number} | chunk {chunk.chunk_index + 1} | page slice{" "}
            {chunk.page_chunk_index + 1}
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

      <div className="mt-4 rounded-2xl border border-[color:var(--line)] bg-[#f6f0e7] p-4">
        <p className="whitespace-pre-line text-sm leading-6 text-slate-800">{chunk.text}</p>
      </div>

      <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <a
          href={chunk.source_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-[color:var(--line)] bg-white/85 px-4 py-2 text-sm text-slate-800 transition hover:border-[color:var(--accent)]/40 hover:text-[color:var(--accent)] md:w-auto"
        >
          <ArrowUpRight className="h-4 w-4" />
          Open paper source
        </a>

        <div className="flex min-w-0 w-full items-start gap-2 rounded-2xl border border-[color:var(--line)] bg-white/76 px-4 py-2.5 text-xs text-[color:var(--muted)] md:max-w-[52%]">
          <FileText className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="break-all font-mono leading-5">{chunk.pdf_path}</span>
        </div>
      </div>
    </article>
  );
}
