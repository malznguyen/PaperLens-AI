import { Download, LoaderCircle, RotateCcw } from "lucide-react";

import { StatusChip } from "@/components/status-chip";

export type PaperIngestState = {
  status: "idle" | "ingesting" | "completed" | "cached" | "failed";
  message?: string;
  pageCount?: number;
  wordCount?: number;
};

type IngestButtonProps = {
  hasPdfUrl: boolean;
  paperTitle: string;
  state?: PaperIngestState;
  onIngest: () => void;
  showStatus?: boolean;
};

export function IngestButton({
  hasPdfUrl,
  paperTitle,
  state,
  onIngest,
  showStatus = true,
}: IngestButtonProps) {
  const status = state?.status ?? "idle";
  const isIngesting = status === "ingesting";
  const isDisabled = !hasPdfUrl || isIngesting;
  const buttonLabel = getButtonLabel(status, hasPdfUrl);
  const tone = getTone(status);
  const statusLabel = getStatusLabel(status);

  return (
    <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto">
      <button
        type="button"
        onClick={onIngest}
        disabled={isDisabled}
        aria-label={`Ingest ${paperTitle}`}
        className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-black/10 bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400 sm:w-auto"
      >
        {status === "failed" ? (
          <RotateCcw className="h-4 w-4" />
        ) : isIngesting ? (
          <LoaderCircle className="h-4 w-4 animate-spin" />
        ) : (
          <Download className="h-4 w-4" />
        )}
        {buttonLabel}
      </button>

      {showStatus && statusLabel ? <StatusChip tone={tone}>{statusLabel}</StatusChip> : null}
    </div>
  );
}

function getButtonLabel(status: PaperIngestState["status"], hasPdfUrl: boolean): string {
  if (!hasPdfUrl) {
    return "No PDF";
  }

  if (status === "ingesting") {
    return "Ingesting...";
  }

  if (status === "failed") {
    return "Retry ingest";
  }

  return "Ingest";
}

function getStatusLabel(status: PaperIngestState["status"]): string | null {
  if (status === "idle") {
    return null;
  }

  if (status === "ingesting") {
    return "Ingesting";
  }

  if (status === "completed") {
    return "Completed";
  }

  if (status === "cached") {
    return "Cached";
  }

  return "Failed";
}

function getTone(status: PaperIngestState["status"]): "neutral" | "positive" | "warning" {
  if (status === "completed" || status === "cached") {
    return "positive";
  }

  if (status === "ingesting" || status === "failed") {
    return "warning";
  }

  return "neutral";
}
