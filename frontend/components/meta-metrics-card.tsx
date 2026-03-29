import { Activity, Clock3, Radar } from "lucide-react";

import { StatusChip } from "@/components/status-chip";
import type { WorkflowMeta } from "@/lib/api";

type MetaMetricsCardProps = {
  meta?: WorkflowMeta | null;
};

function formatMs(value: number): string {
  return `${value} ms`;
}

export function MetaMetricsCard({ meta }: MetaMetricsCardProps) {
  if (!meta) {
    return null;
  }

  const statusTone =
    meta.status === "completed"
      ? "positive"
      : meta.status === "partial"
        ? "warning"
        : "neutral";

  return (
    <div className="rounded-[1.6rem] border border-black/10 bg-white/78 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
            Workflow metrics
          </p>
          <h3 className="mt-2 text-2xl text-slate-900">Latency and evidence counts</h3>
        </div>

        <div className="flex flex-wrap gap-2">
          <StatusChip tone={statusTone}>{meta.status}</StatusChip>
          <StatusChip tone="neutral">{meta.retrieved_chunk_count} chunks</StatusChip>
          <StatusChip tone="neutral">{meta.citation_count} citations</StatusChip>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile icon={Radar} label="Retrieval" value={formatMs(meta.retrieval_ms)} />
        <MetricTile icon={Activity} label="Reranking" value={formatMs(meta.reranking_ms)} />
        <MetricTile icon={Clock3} label="Generation" value={formatMs(meta.generation_ms)} />
        <MetricTile icon={Clock3} label="Total" value={formatMs(meta.total_ms)} />
      </div>
    </div>
  );
}

type MetricTileProps = {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
};

function MetricTile({ icon: Icon, label, value }: MetricTileProps) {
  return (
    <div className="rounded-2xl border border-black/10 bg-[#f6f0e7] px-4 py-4">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl border border-black/10 bg-white/80 p-2 text-[color:var(--accent)]">
          <Icon className="h-4 w-4" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-[color:var(--muted)]">
            {label}
          </p>
          <p className="mt-1 text-base text-slate-900">{value}</p>
        </div>
      </div>
    </div>
  );
}
