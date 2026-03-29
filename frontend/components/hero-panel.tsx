import { ArrowRight, Database, SearchCheck, Workflow } from "lucide-react";
import Link from "next/link";

import { StatusChip } from "@/components/status-chip";

const metrics = [
  {
    label: "Paper source",
    value: "arXiv API",
    icon: SearchCheck,
  },
  {
    label: "Vector store",
    value: "Chroma",
    icon: Database,
  },
  {
    label: "Generation mode",
    value: "RAG pipeline",
    icon: Workflow,
  },
];

export function HeroPanel() {
  return (
    <section className="overflow-hidden rounded-[2rem] border border-black/10 bg-[color:var(--panel)] shadow-panel">
      <div className="grid gap-6 px-6 py-8 md:px-8 md:py-10 xl:grid-cols-[1.35fr_0.85fr]">
        <div>
          <StatusChip tone="neutral">Grounded research assistant</StatusChip>
          <h1 className="mt-5 max-w-3xl text-3xl leading-tight text-slate-950 md:text-4xl">
            Search, ingest, index, and analyze academic papers with full citation traceability.
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-[color:var(--muted)] md:text-base">
            PaperLens AI keeps discovery, ingestion, retrieval, and comparison in separate workflow
            stages so every generated answer stays grounded in real paper content.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/search"
              className="inline-flex items-center gap-2 rounded-full bg-[#13212d] px-5 py-3 text-sm font-medium text-white transition hover:bg-[#1c3143]"
            >
              Search papers
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/workspace"
              className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white/80 px-5 py-3 text-sm font-medium text-slate-900 transition hover:bg-white"
            >
              View paper workspace
            </Link>
          </div>
        </div>

        <div className="grid gap-3">
          {metrics.map((metric) => {
            const Icon = metric.icon;

            return (
              <div
                key={metric.label}
                className="rounded-3xl border border-black/10 bg-white/78 px-5 py-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-[color:var(--muted)]">
                      {metric.label}
                    </p>
                    <p className="mt-3 text-2xl text-slate-950">{metric.value}</p>
                  </div>
                  <div className="rounded-2xl border border-black/10 bg-[color:var(--accent-soft)] p-3 text-[color:var(--accent)]">
                    <Icon className="h-5 w-5" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
