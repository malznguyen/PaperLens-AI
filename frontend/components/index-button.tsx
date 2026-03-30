import { Database, LoaderCircle, RotateCcw } from "lucide-react";

import { StatusChip } from "@/components/status-chip";

export type PaperIndexState = {
  status: "idle" | "indexing" | "indexed" | "cached" | "failed";
  message?: string;
  chunkCount?: number;
  collectionName?: string;
};

type IndexButtonProps = {
  paperTitle: string;
  state?: PaperIndexState;
  onIndex: () => void;
  showStatus?: boolean;
};

export function IndexButton({
  paperTitle,
  state,
  onIndex,
  showStatus = true,
}: IndexButtonProps) {
  const status = state?.status ?? "idle";
  const isIndexing = status === "indexing";
  const buttonLabel = getButtonLabel(status);
  const tone = getTone(status);
  const statusLabel = getStatusLabel(status);

  return (
    <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto">
      <button
        type="button"
        onClick={onIndex}
        disabled={isIndexing}
        aria-label={`Index ${paperTitle}`}
        className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-black/10 bg-[color:var(--accent-soft)] px-4 py-2 text-sm font-medium text-[color:var(--accent)] transition hover:bg-[color:var(--accent-soft)]/80 disabled:cursor-not-allowed disabled:opacity-70 sm:w-auto"
      >
        {status === "failed" ? (
          <RotateCcw className="h-4 w-4" />
        ) : isIndexing ? (
          <LoaderCircle className="h-4 w-4 animate-spin" />
        ) : (
          <Database className="h-4 w-4" />
        )}
        {buttonLabel}
      </button>

      {showStatus && statusLabel ? <StatusChip tone={tone}>{statusLabel}</StatusChip> : null}
    </div>
  );
}

function getButtonLabel(status: PaperIndexState["status"]): string {
  if (status === "indexing") {
    return "Indexing...";
  }

  if (status === "failed") {
    return "Retry index";
  }

  return "Index";
}

function getStatusLabel(status: PaperIndexState["status"]): string | null {
  if (status === "idle") {
    return null;
  }

  if (status === "indexing") {
    return "Indexing";
  }

  if (status === "indexed") {
    return "Indexed";
  }

  if (status === "cached") {
    return "Cached";
  }

  return "Failed";
}

function getTone(status: PaperIndexState["status"]): "neutral" | "positive" | "warning" {
  if (status === "indexed" || status === "cached") {
    return "positive";
  }

  if (status === "indexing" || status === "failed") {
    return "warning";
  }

  return "neutral";
}
