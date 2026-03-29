import { Database, FileText, Layers } from "lucide-react";

import { SectionCard } from "@/components/section-card";

const workspaceInfo = [
  {
    label: "Paper ingestion",
    detail:
      "Use the Search page to find papers, then click Ingest to download and parse their PDFs into structured text.",
    icon: FileText,
  },
  {
    label: "Local indexing",
    detail:
      "After ingestion, click Index to chunk the parsed text, generate embeddings, and store them in Chroma for retrieval.",
    icon: Database,
  },
  {
    label: "Downstream workflows",
    detail:
      "Once papers are indexed, use Chat for grounded Q&A, Compare for structured side-by-side analysis, or Synthesis for literature overviews.",
    icon: Layers,
  },
];

export default function WorkspacePage() {
  return (
    <div className="space-y-6">
      <SectionCard
        eyebrow="Paper workspace"
        title="Manage your ingested and indexed papers."
        description="This workspace shows how papers move through the pipeline. Use the Search page to ingest and index papers, then use their IDs across Chat, Compare, and Synthesis."
      >
        <div className="grid gap-4 md:grid-cols-3">
          {workspaceInfo.map((item) => {
            const Icon = item.icon;

            return (
              <div
                key={item.label}
                className="rounded-2xl border border-black/10 bg-white/75 px-4 py-4"
              >
                <div className="mb-3 flex items-center gap-3">
                  <div className="rounded-xl border border-black/10 bg-[color:var(--accent-soft)] p-2 text-[color:var(--accent)]">
                    <Icon className="h-4 w-4" />
                  </div>
                  <p className="text-xs uppercase tracking-[0.22em] text-[color:var(--muted)]">
                    {item.label}
                  </p>
                </div>
                <p className="text-sm leading-6 text-slate-800">{item.detail}</p>
              </div>
            );
          })}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Ingestion pipeline"
        title="How papers flow through PaperLens AI."
        description="Each step preserves provenance so downstream answers stay grounded in real paper content."
      >
        <div className="space-y-3">
          {[
            { step: "1", label: "Search", detail: "Discover papers on arXiv by topic" },
            { step: "2", label: "Ingest", detail: "Download PDF and extract page-level text" },
            { step: "3", label: "Index", detail: "Chunk, embed (BGE), and store in Chroma" },
            { step: "4", label: "Analyze", detail: "Chat, compare, or synthesize with citations" },
          ].map((item) => (
            <div
              key={item.step}
              className="flex items-center gap-4 rounded-2xl border border-black/10 bg-white/75 px-4 py-3"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#13212d] text-xs font-medium text-white">
                {item.step}
              </span>
              <div>
                <p className="text-sm font-medium text-slate-900">{item.label}</p>
                <p className="text-sm text-[color:var(--muted)]">{item.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
