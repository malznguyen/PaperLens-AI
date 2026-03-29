import { FileSearch, Link2 } from "lucide-react";

import { SearchExperience } from "@/components/search-experience";
import { SectionCard } from "@/components/section-card";
import { StatusChip } from "@/components/status-chip";

const searchHighlights = [
  {
    label: "Normalized records",
    detail: "Titles, authors, abstracts, categories, and source links returned in a stable format.",
  },
  {
    label: "Error handling",
    detail: "Loading, empty, and upstream error states are surfaced without breaking the workflow.",
  },
  {
    label: "Pipeline-ready output",
    detail: "Paper metadata flows directly into ingestion, indexing, and comparison stages.",
  },
];

export default function SearchPage() {
  return (
    <div className="space-y-6">
      <SectionCard
        eyebrow="Paper discovery"
        title="Search arXiv by topic and inspect normalized paper metadata."
        description="Enter a research topic, review results with full metadata, then ingest and index papers for downstream analysis."
      >
        <div className="flex flex-wrap gap-3">
          <StatusChip tone="positive">
            <FileSearch className="mr-2 h-3.5 w-3.5" />
            arXiv integration live
          </StatusChip>
          <StatusChip tone="neutral">
            <Link2 className="mr-2 h-3.5 w-3.5" />
            PDF and source links included
          </StatusChip>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {searchHighlights.map((highlight) => (
            <div
              key={highlight.label}
              className="rounded-2xl border border-black/10 bg-white/75 px-4 py-4"
            >
              <p className="text-xs uppercase tracking-[0.22em] text-[color:var(--muted)]">
                {highlight.label}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-800">{highlight.detail}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      <SearchExperience />
    </div>
  );
}
