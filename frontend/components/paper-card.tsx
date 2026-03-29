import { CalendarDays, ExternalLink, FileText } from "lucide-react";

import type { PaperSearchResult } from "@/lib/api";

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
});

function formatDateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return dateFormatter.format(date);
}

function truncateText(value: string, maxLength: number): string {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength - 3).trimEnd()}...`;
}

type PaperCardProps = {
  paper: PaperSearchResult;
};

export function PaperCard({ paper }: PaperCardProps) {
  const abstractSnippet = truncateText(paper.abstract, 360);

  return (
    <article className="rounded-[1.6rem] border border-black/10 bg-white/78 p-5 shadow-panel">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
            {paper.primary_category ?? "arXiv record"}
          </p>
          <h3 className="mt-2 text-2xl leading-tight text-slate-900">{paper.title}</h3>
          <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">
            {paper.authors.length > 0 ? paper.authors.join(", ") : "Authors unavailable"}
          </p>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          {paper.pdf_url ? (
            <a
              href={paper.pdf_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white/90 px-4 py-2 text-sm font-medium text-slate-800 transition hover:bg-white"
            >
              <FileText className="h-4 w-4" />
              PDF
            </a>
          ) : null}
          <a
            href={paper.source_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-[color:var(--accent-soft)] px-4 py-2 text-sm font-medium text-[color:var(--accent)] transition hover:bg-[color:var(--accent-soft)]/80"
          >
            <ExternalLink className="h-4 w-4" />
            Source
          </a>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <span className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-[#f6f0e7] px-3 py-1.5 text-xs uppercase tracking-[0.18em] text-slate-700">
          <CalendarDays className="h-3.5 w-3.5" />
          Published {formatDateLabel(paper.published_at)}
        </span>
        <span className="inline-flex items-center rounded-full border border-black/10 bg-white/80 px-3 py-1.5 text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">
          Updated {formatDateLabel(paper.updated_at)}
        </span>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {paper.categories.map((category) => (
          <span
            key={`${paper.id}-${category}`}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium uppercase tracking-[0.18em] ${
              category === paper.primary_category
                ? "border-[color:var(--accent)]/20 bg-[color:var(--accent-soft)] text-[color:var(--accent)]"
                : "border-black/10 bg-white/80 text-slate-700"
            }`}
          >
            {category}
          </span>
        ))}
      </div>

      <p className="mt-4 text-sm leading-7 text-slate-700">{abstractSnippet}</p>
    </article>
  );
}
