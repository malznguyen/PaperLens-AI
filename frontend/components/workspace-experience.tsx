"use client";

import Link from "next/link";
import { startTransition, useEffect, useState } from "react";
import {
  Check,
  Copy,
  Database,
  ExternalLink,
  FileText,
  GitCompareArrows,
  LibraryBig,
  LoaderCircle,
  MessagesSquare,
  RefreshCw,
  Search,
} from "lucide-react";

import { SectionCard } from "@/components/section-card";
import { StatusChip } from "@/components/status-chip";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import {
  fetchWorkspace,
  indexPaper,
  type WorkspacePaper,
  type WorkspaceResponse,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const numberFormatter = new Intl.NumberFormat("en-US");

type WorkspaceIndexMutationState = {
  status: "idle" | "indexing" | "success" | "error";
  message?: string;
};

export function WorkspaceExperience() {
  const [workspace, setWorkspace] = useState<WorkspaceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [indexStates, setIndexStates] = useState<
    Record<string, WorkspaceIndexMutationState>
  >({});

  useEffect(() => {
    void loadWorkspace();
  }, []);

  async function loadWorkspace(options?: { preserveData?: boolean }) {
    const preserveData = options?.preserveData ?? false;

    if (preserveData && workspace) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    setErrorMessage(null);

    try {
      const nextWorkspace = await fetchWorkspace();
      startTransition(() => {
        setWorkspace(nextWorkspace);
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to load the current workspace state right now.",
      );
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }

  async function handleIndexPaper(paper: WorkspacePaper) {
    setIndexStates((currentStates) => ({
      ...currentStates,
      [paper.paper_id]: {
        status: "indexing",
        message: "Refreshing the local vector index for this paper.",
      },
    }));

    try {
      const response = await indexPaper({ paper_id: paper.paper_id });
      setIndexStates((currentStates) => ({
        ...currentStates,
        [paper.paper_id]: {
          status: "success",
          message: response.message,
        },
      }));
      await loadWorkspace({ preserveData: true });
    } catch (error) {
      setIndexStates((currentStates) => ({
        ...currentStates,
        [paper.paper_id]: {
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "Unable to index this paper right now.",
        },
      }));
    }
  }

  async function handleCopyIndexedIds() {
    const indexedIds = workspace?.papers
      .filter((paper) => paper.status.indexed)
      .map((paper) => paper.paper_id) ?? [];

    if (indexedIds.length === 0 || !navigator.clipboard) {
      return;
    }

    try {
      await navigator.clipboard.writeText(indexedIds.join(", "));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="space-y-6">
      <SectionCard
        eyebrow="Paper workspace"
        title="Inspect the live state of your local paper corpus."
        description="This view reads parsed JSON artifacts, indexing cache records, and Chroma metadata so the workspace reflects the papers you already ingested and indexed."
      >
        {isLoading && !workspace ? (
          <LoadingState
            title="Loading workspace state"
            description="Inspecting parsed artifacts, local index cache records, and vector metadata."
          />
        ) : null}

        {!isLoading && !workspace && errorMessage ? (
          <ErrorState
            title="Workspace unavailable"
            description={errorMessage}
          />
        ) : null}

        {workspace ? (
          <div className="space-y-4">
            {errorMessage ? (
              <ErrorState
                compact
                title="Could not refresh the latest workspace snapshot"
                description={`${errorMessage} Showing the last successful workspace state instead.`}
              />
            ) : null}

            {isRefreshing ? (
              <LoadingState
                compact
                title="Refreshing workspace"
                description="Keeping the current corpus snapshot visible while local state is reloaded."
              />
            ) : null}

            <div className="grid gap-4 2xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.88fr)]">
              <div className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-4">
                <SummaryCard
                  label="Tracked papers"
                  value={workspace.summary.total_paper_count}
                  detail="All papers discovered from local artifacts"
                  icon={<LibraryBig className="h-4 w-4" />}
                />
                <SummaryCard
                  label="Ingested"
                  value={workspace.summary.ingested_paper_count}
                  detail="Parsed PDFs available on disk"
                  icon={<FileText className="h-4 w-4" />}
                />
                <SummaryCard
                  label="Indexed"
                  value={workspace.summary.indexed_paper_count}
                  detail="Ready for retrieval workflows"
                  icon={<Database className="h-4 w-4" />}
                />
                <SummaryCard
                  label="Corpus chunks"
                  value={workspace.summary.total_chunk_count}
                  detail="Total local retrieval units"
                  icon={<RefreshCw className="h-4 w-4" />}
                />
              </div>

              <div className="rounded-[1.6rem] border border-[color:var(--line)] bg-[#f6f0e7] p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.24em] text-[color:var(--muted)]">
                      What next
                    </p>
                    <h3 className="mt-2 max-w-lg text-[1.7rem] leading-tight text-slate-900">
                      {getNextStepHeadline(workspace)}
                    </h3>
                  </div>

                  <button
                    type="button"
                    onClick={() => void loadWorkspace({ preserveData: true })}
                    disabled={isRefreshing}
                    className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-white/90 px-4 py-2 text-sm font-medium text-slate-800 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {isRefreshing ? (
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                    Refresh snapshot
                  </button>
                </div>

                <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-700">
                  {getNextStepDescription(workspace)}
                </p>

                <div className="mt-5 flex flex-wrap gap-2">
                  <QuickActionLink href="/search" icon={<Search className="h-4 w-4" />}>
                    Search papers
                  </QuickActionLink>
                  <QuickActionLink href="/chat" icon={<MessagesSquare className="h-4 w-4" />}>
                    Chat with corpus
                  </QuickActionLink>
                  <QuickActionLink
                    href="/compare"
                    icon={<GitCompareArrows className="h-4 w-4" />}
                  >
                    Compare papers
                  </QuickActionLink>
                  <button
                    type="button"
                    onClick={() => void handleCopyIndexedIds()}
                    disabled={workspace.summary.indexed_paper_count === 0}
                    className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-[color:var(--accent-soft)] px-4 py-2 text-sm font-medium text-[color:var(--accent)] transition hover:bg-[color:var(--accent-soft)]/80 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    {copied ? "Indexed IDs copied" : "Copy indexed IDs"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </SectionCard>

      <SectionCard
        eyebrow="Corpus catalog"
        title="Review papers, status, and local metadata."
        description="Each record surfaces the paper ID, ingestion/indexing status, corpus size metrics, and direct workflow actions without turning the page into a static explainer."
      >
        {isLoading && !workspace ? (
          <LoadingState
            title="Building the corpus catalog"
            description="Loading local paper records and preparing the workspace table."
          />
        ) : null}

        {!workspace && !isLoading && errorMessage ? (
          <ErrorState
            title="Corpus catalog unavailable"
            description={errorMessage}
          />
        ) : null}

        {workspace && workspace.papers.length === 0 ? (
          <EmptyState
            title="No local papers yet"
            description="Search for papers first, then ingest and index them to populate this workspace with real corpus state."
          />
        ) : null}

        {workspace && workspace.papers.length > 0 ? (
          <div className="overflow-hidden rounded-[1.6rem] border border-[color:var(--line)] bg-white/82 shadow-panel">
            <div className="hidden grid-cols-[minmax(0,1.8fr)_minmax(220px,0.78fr)_minmax(180px,0.7fr)_minmax(240px,0.9fr)] gap-4 border-b border-[color:var(--line)] px-5 py-4 text-[11px] uppercase tracking-[0.24em] text-[color:var(--muted)] 2xl:grid">
              <span>Paper</span>
              <span>Status</span>
              <span>Corpus metrics</span>
              <span>Actions</span>
            </div>

            <div className="divide-y divide-black/10">
              {workspace.papers.map((paper) => (
                <WorkspacePaperRow
                  key={paper.paper_id}
                  paper={paper}
                  state={indexStates[paper.paper_id]}
                  onIndex={handleIndexPaper}
                />
              ))}
            </div>
          </div>
        ) : null}
      </SectionCard>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: number;
  detail: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-[1.45rem] border border-[color:var(--line)] bg-white/84 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] uppercase tracking-[0.22em] text-[color:var(--muted)]">
          {label}
        </p>
        <div className="rounded-xl border border-[color:var(--line)] bg-[color:var(--accent-soft)] p-2 text-[color:var(--accent)]">
          {icon}
        </div>
      </div>
      <p className="mt-3 text-[2rem] text-slate-900">{numberFormatter.format(value)}</p>
      <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">{detail}</p>
    </div>
  );
}

function QuickActionLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-white/90 px-4 py-2 text-sm font-medium text-slate-800 transition hover:bg-white"
    >
      {icon}
      {children}
    </Link>
  );
}

function WorkspacePaperRow({
  paper,
  state,
  onIndex,
}: {
  paper: WorkspacePaper;
  state?: WorkspaceIndexMutationState;
  onIndex: (paper: WorkspacePaper) => void;
}) {
  const isIndexing = state?.status === "indexing";
  const shouldShowIndexAction = paper.status.ingested;
  const mutationTone =
    state?.status === "error"
      ? "text-[#8a4b3a]"
      : state?.status === "success"
        ? "text-[color:var(--success)]"
        : "text-[color:var(--muted)]";

  return (
    <article className="grid gap-5 px-5 py-5 2xl:grid-cols-[minmax(0,1.8fr)_minmax(220px,0.78fr)_minmax(180px,0.7fr)_minmax(240px,0.9fr)] 2xl:items-start">
      <div className="min-w-0 space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-[color:var(--line)] bg-[#f6f0e7] px-2.5 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-700">
            {paper.primary_category ?? "local record"}
          </span>
          <span className="text-[11px] uppercase tracking-[0.18em] text-[color:var(--muted)]">
            {paper.paper_id}
          </span>
        </div>

        <h3 className="text-[1.6rem] leading-[1.14] text-slate-900">{paper.title}</h3>
        <p className="max-w-4xl text-sm leading-6 text-[color:var(--muted-strong)]">
          {paper.authors.length > 0 ? paper.authors.join(", ") : "Authors unavailable"}
        </p>

        <div className="flex flex-wrap gap-2">
          {paper.categories.map((category) => (
            <span
              key={`${paper.paper_id}-${category}`}
              className={cn(
                "rounded-full border px-2.5 py-1 text-[11px] uppercase tracking-[0.14em]",
                category === paper.primary_category
                  ? "border-[color:var(--accent)]/20 bg-[color:var(--accent-soft)] text-[color:var(--accent)]"
                  : "border-[color:var(--line)] bg-white/80 text-slate-700",
              )}
            >
              {category}
            </span>
          ))}
        </div>
      </div>

      <div className="space-y-3 rounded-[1.35rem] border border-[color:var(--line)] bg-[#fbf7f1] p-4 2xl:rounded-none 2xl:border-0 2xl:bg-transparent 2xl:p-0">
        <p className="text-[11px] uppercase tracking-[0.22em] text-[color:var(--muted)] 2xl:hidden">
          Status
        </p>
        <div className="flex flex-wrap gap-2">
          <StatusChip tone={paper.status.ingested ? "positive" : "warning"}>
            {paper.status.ingested ? "Ingested" : "Missing parsed artifact"}
          </StatusChip>
          <StatusChip tone={paper.status.indexed ? "positive" : "neutral"}>
            {paper.status.indexed ? "Indexed" : "Not indexed"}
          </StatusChip>
        </div>
        <p className="text-sm leading-6 text-[color:var(--muted)]">
          {paper.collection_name
            ? `Collection: ${paper.collection_name}`
            : "No index collection recorded yet."}
        </p>
      </div>

      <div className="space-y-3 rounded-[1.35rem] border border-[color:var(--line)] bg-[#fbf7f1] p-4 2xl:rounded-none 2xl:border-0 2xl:bg-transparent 2xl:p-0">
        <p className="text-[11px] uppercase tracking-[0.22em] text-[color:var(--muted)] 2xl:hidden">
          Corpus metrics
        </p>
        <div className="grid gap-2 sm:grid-cols-3 2xl:grid-cols-1">
          <MetricLine label="Pages" value={paper.page_count} />
          <MetricLine label="Words" value={paper.word_count} />
          <MetricLine label="Chunks" value={paper.chunk_count} />
        </div>
      </div>

      <div className="space-y-3 rounded-[1.35rem] border border-[color:var(--line)] bg-[#fbf7f1] p-4 2xl:rounded-none 2xl:border-0 2xl:bg-transparent 2xl:p-0">
        <p className="text-[11px] uppercase tracking-[0.22em] text-[color:var(--muted)] 2xl:hidden">
          Actions
        </p>
        <div className="flex flex-wrap gap-2">
          {shouldShowIndexAction ? (
            <button
              type="button"
              onClick={() => onIndex(paper)}
              disabled={isIndexing}
              className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-[color:var(--accent-soft)] px-4 py-2 text-sm font-medium text-[color:var(--accent)] transition hover:bg-[color:var(--accent-soft)]/80 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isIndexing ? (
                <LoaderCircle className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {paper.status.indexed ? "Refresh index" : "Index now"}
            </button>
          ) : null}

          {paper.source_url ? (
            <a
              href={paper.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-white/90 px-4 py-2 text-sm font-medium text-slate-800 transition hover:bg-white"
            >
              <ExternalLink className="h-4 w-4" />
              Source
            </a>
          ) : null}
        </div>

        <p className={cn("text-sm leading-6", mutationTone)}>
          {state?.message ?? getWorkspaceStatusMessage(paper)}
        </p>
      </div>
    </article>
  );
}

function MetricLine({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm leading-6 text-slate-800">
      <span className="text-[color:var(--muted)]">{label}</span>
      <span className="font-medium">{numberFormatter.format(value)}</span>
    </div>
  );
}

function getNextStepHeadline(workspace: WorkspaceResponse): string {
  if (workspace.summary.total_paper_count === 0) {
    return "Start by adding papers to the local corpus.";
  }

  const papersNeedingIndex = workspace.papers.filter(
    (paper) => paper.status.ingested && !paper.status.indexed,
  ).length;

  if (papersNeedingIndex > 0) {
    return papersNeedingIndex === 1
      ? "1 ingested paper still needs indexing."
      : `${papersNeedingIndex} ingested papers still need indexing.`;
  }

  if (workspace.summary.indexed_paper_count > 0) {
    return "The corpus is ready for grounded chat and comparison.";
  }

  return "Review local records and continue the workflow.";
}

function getNextStepDescription(workspace: WorkspaceResponse): string {
  if (workspace.summary.total_paper_count === 0) {
    return "Use Search to discover papers, then ingest and index them so this workspace becomes the live inventory for downstream workflows.";
  }

  const papersNeedingIndex = workspace.papers.filter(
    (paper) => paper.status.ingested && !paper.status.indexed,
  );

  if (papersNeedingIndex.length > 0) {
    return `Index ${papersNeedingIndex.length} remaining paper${papersNeedingIndex.length === 1 ? "" : "s"} from this page or continue from Search. Once indexed, the same paper IDs can flow into chat and comparison.`;
  }

  if (workspace.summary.indexed_paper_count > 0) {
    return "Open Chat to ask grounded questions over the current corpus, or move to Compare when you want a structured side-by-side view across multiple indexed papers.";
  }

  return "Search for more papers or refresh the snapshot after running ingest and index operations elsewhere in the app.";
}

function getWorkspaceStatusMessage(paper: WorkspacePaper): string {
  if (paper.status.ingested && paper.status.indexed) {
    return `Parsed locally and indexed into ${paper.chunk_count} chunk${paper.chunk_count === 1 ? "" : "s"}.`;
  }

  if (paper.status.ingested) {
    return "Parsed artifact is available locally, but this paper has not been indexed yet.";
  }

  if (paper.status.indexed) {
    return "Indexed metadata exists for this paper even though the parsed artifact was not found in the current workspace scan.";
  }

  return "This paper does not currently have local ingest or index artifacts.";
}
