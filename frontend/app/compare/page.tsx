import { BookMarked, GitCompareArrows, Network } from "lucide-react";

import { CompareExperience } from "@/components/compare-experience";
import { SectionCard } from "@/components/section-card";
import { StatusChip } from "@/components/status-chip";
import { TopicSynthesisExperience } from "@/components/topic-synthesis-experience";

const compareHighlights = [
  {
    label: "Per-paper evidence retrieval",
    detail: "The compare workflow pulls relevant chunks for each selected paper so one document cannot dominate the entire comparison.",
  },
  {
    label: "Structured synthesis output",
    detail: "Rows are normalized around objective, methodology, dataset, strengths, limitations, and contribution while keeping source traceability visible.",
  },
  {
    label: "Reporting-friendly metrics",
    detail: "Latency and evidence counts are returned with the response for demos, screenshots, and coursework evaluation notes.",
  },
];

export default function ComparePage() {
  return (
    <div className="space-y-6">
      <SectionCard
        eyebrow="Phase 6 live"
        title="Compare indexed papers and synthesize a grounded topic overview."
        description="This page extends the Phase 5 retrieval stack into higher-level research workflows: structured paper comparison, literature-overview synthesis, explicit citations, and lightweight evaluation metrics."
      >
        <div className="flex flex-wrap gap-3">
          <StatusChip tone="positive">
            <GitCompareArrows className="mr-2 h-3.5 w-3.5" />
            Multi-paper compare live
          </StatusChip>
          <StatusChip tone="neutral">
            <Network className="mr-2 h-3.5 w-3.5" />
            POST /api/compare
          </StatusChip>
          <StatusChip tone="neutral">
            <BookMarked className="mr-2 h-3.5 w-3.5" />
            POST /api/summarize-topic
          </StatusChip>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {compareHighlights.map((highlight) => (
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

      <CompareExperience />
      <TopicSynthesisExperience />
    </div>
  );
}
