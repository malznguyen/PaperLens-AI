import { CalendarDays, ExternalLink, FileText } from "lucide-react";

import { IndexButton, type PaperIndexState } from "@/components/index-button";
import { IngestButton, type PaperIngestState } from "@/components/ingest-button";
import { StatusChip } from "@/components/status-chip";
import type { PaperSearchResult } from "@/lib/api";
import { cn } from "@/lib/utils";

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
});
const numberFormatter = new Intl.NumberFormat("en-US");

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
  ingestState?: PaperIngestState;
  indexState?: PaperIndexState;
  onIngest: (paper: PaperSearchResult) => void;
  onIndex: (paper: PaperSearchResult) => void;
};

export function PaperCard({
  paper,
  ingestState,
  indexState,
  onIngest,
  onIndex,
}: PaperCardProps) {
  const abstractSnippet = truncateText(paper.abstract, 360);
  const ingestMessage = formatIngestMessage(ingestState, Boolean(paper.pdf_url));
  const indexMessage = formatIndexMessage(indexState);
  const shouldShowIndexAction =
    ingestState?.status === "completed" ||
    ingestState?.status === "cached" ||
    indexState?.status === "indexing" ||
    indexState?.status === "indexed" ||
    indexState?.status === "cached" ||
    indexState?.status === "failed";
  const detailMessages = [ingestMessage, indexMessage].filter(
    (message): message is string => Boolean(message),
  );
  const statusItems = getPaperStatusItems(ingestState, indexState, Boolean(paper.pdf_url));

  return (
    <article className="rounded-[1.75rem] border border-[color:var(--line)] bg-white/84 p-5 shadow-panel sm:p-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center rounded-full border border-[color:var(--line)] bg-[#f6f0e7] px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-slate-700">
          {paper.primary_category ?? "arXiv record"}
        </span>
        <span className="text-[11px] uppercase tracking-[0.18em] text-[color:var(--muted)]">
          {paper.id}
        </span>
      </div>

      <div className="mt-4 space-y-3">
        <div className="min-w-0">
          <h3 className="mt-2 max-w-4xl text-pretty text-[1.38rem] leading-[1.12] text-slate-900 sm:text-[1.55rem] md:text-[1.8rem]">
            {paper.title}
          </h3>
          <p className="mt-3 max-w-4xl text-[13px] leading-6 text-[color:var(--muted-strong)] sm:text-sm">
            {paper.authors.length > 0 ? paper.authors.join(", ") : "Authors unavailable"}
          </p>
        </div>
        <p className="max-w-5xl text-sm leading-7 text-slate-700">{abstractSnippet}</p>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-end">
        <div className="space-y-4 min-w-0">
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-[#f6f0e7] px-3 py-1.5 text-[11px] uppercase tracking-[0.16em] text-slate-700">
              <CalendarDays className="h-3.5 w-3.5" />
              Published {formatDateLabel(paper.published_at)}
            </span>
            <span className="inline-flex items-center rounded-full border border-[color:var(--line)] bg-white/84 px-3 py-1.5 text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted)]">
              Updated {formatDateLabel(paper.updated_at)}
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {paper.categories.map((category) => (
              <span
                key={`${paper.id}-${category}`}
                className={cn(
                  "rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.14em]",
                  category === paper.primary_category
                    ? "border-[color:var(--accent)]/20 bg-[color:var(--accent-soft)] text-[color:var(--accent)]"
                    : "border-[color:var(--line)] bg-white/80 text-slate-700",
                )}
              >
                {category}
              </span>
            ))}
          </div>

          {statusItems.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {statusItems.map((item) => (
                <StatusChip key={item.label} tone={item.tone}>
                  {item.label}
                </StatusChip>
              ))}
            </div>
          ) : null}

          {detailMessages.length > 0 ? (
            <div className="space-y-1.5">
              {detailMessages.map((message) => (
                <p key={message} className="text-sm leading-6 text-[color:var(--muted)]">
                  {message}
                </p>
              ))}
            </div>
          ) : null}
        </div>

        <div className="flex w-full flex-wrap items-center gap-2 xl:w-auto xl:justify-end">
          <div className="flex w-full flex-wrap gap-2 xl:w-auto xl:justify-end">
            <IngestButton
              hasPdfUrl={Boolean(paper.pdf_url)}
              paperTitle={paper.title}
              state={ingestState}
              onIngest={() => onIngest(paper)}
              showStatus={false}
            />
            {shouldShowIndexAction ? (
              <IndexButton
                paperTitle={paper.title}
                state={indexState}
                onIndex={() => onIndex(paper)}
                showStatus={false}
              />
            ) : null}
            {paper.pdf_url ? (
              <a
                href={paper.pdf_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-[color:var(--line)] bg-white/90 px-4 py-2 text-sm font-medium text-slate-800 transition hover:bg-white sm:w-auto"
              >
                <FileText className="h-4 w-4" />
                PDF
              </a>
            ) : null}
            <a
              href={paper.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-[color:var(--line)] bg-[color:var(--accent-soft)] px-4 py-2 text-sm font-medium text-[color:var(--accent)] transition hover:bg-[color:var(--accent-soft)]/80 sm:w-auto"
            >
              <ExternalLink className="h-4 w-4" />
              Source
            </a>
          </div>
        </div>
      </div>
    </article>
  );
}

function getPaperStatusItems(
  ingestState: PaperIngestState | undefined,
  indexState: PaperIndexState | undefined,
  hasPdfUrl: boolean,
): Array<{
  label: string;
  tone: "neutral" | "positive" | "warning";
}> {
  const items: Array<{
    label: string;
    tone: "neutral" | "positive" | "warning";
  }> = [];

  if (!hasPdfUrl) {
    items.push({ label: "No PDF", tone: "warning" });
  }

  switch (ingestState?.status) {
    case "ingesting":
      items.push({ label: "Ingesting", tone: "warning" });
      break;
    case "completed":
      items.push({ label: "Parsed locally", tone: "positive" });
      break;
    case "cached":
      items.push({ label: "Cached locally", tone: "positive" });
      break;
    case "failed":
      items.push({ label: "Ingest failed", tone: "warning" });
      break;
    default:
      break;
  }

  switch (indexState?.status) {
    case "indexing":
      items.push({ label: "Indexing", tone: "warning" });
      break;
    case "indexed":
      items.push({ label: "Indexed", tone: "positive" });
      break;
    case "cached":
      items.push({ label: "Index cached", tone: "positive" });
      break;
    case "failed":
      items.push({ label: "Index failed", tone: "warning" });
      break;
    default:
      break;
  }

  return items;
}

function formatIngestMessage(
  ingestState: PaperIngestState | undefined,
  hasPdfUrl: boolean,
): string | null {
  if (!hasPdfUrl) {
    return "PDF link unavailable for this record.";
  }

  if (!ingestState || ingestState.status === "idle") {
    return null;
  }

  if (ingestState.status === "ingesting") {
    return ingestState.message ?? "Downloading the PDF and extracting text.";
  }

  const stats =
    typeof ingestState.pageCount === "number" && typeof ingestState.wordCount === "number"
      ? `${ingestState.pageCount} pages | ${numberFormatter.format(ingestState.wordCount)} words`
      : null;

  if (stats && ingestState.message) {
    return `${ingestState.message} ${stats}.`;
  }

  if (stats) {
    return stats;
  }

  return ingestState.message ?? null;
}

function formatIndexMessage(indexState: PaperIndexState | undefined): string | null {
  if (!indexState || indexState.status === "idle") {
    return null;
  }

  if (indexState.status === "indexing") {
    return indexState.message ?? "Chunking parsed pages and building local embeddings.";
  }

  if (indexState.status === "failed") {
    return indexState.message ?? "Unable to index this paper right now.";
  }

  const chunkLabel =
    typeof indexState.chunkCount === "number"
      ? `${numberFormatter.format(indexState.chunkCount)} chunks`
      : "paper chunks";

  if (indexState.status === "indexed") {
    if (indexState.collectionName) {
      return `Indexed ${chunkLabel} into ${indexState.collectionName}.`;
    }

    return `Indexed ${chunkLabel} for retrieval.`;
  }

  return `Local index already up to date with ${chunkLabel}.`;
}
