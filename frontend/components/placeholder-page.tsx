import { CircleDashed, Network, Waypoints } from "lucide-react";

import { SectionCard } from "@/components/section-card";
import { StatusChip } from "@/components/status-chip";

type PlaceholderPageProps = {
  title: string;
  description: string;
  endpoint: string;
  highlights: string[];
};

export function PlaceholderPage({
  title,
  description,
  endpoint,
  highlights,
}: PlaceholderPageProps) {
  return (
    <div className="space-y-6">
      <SectionCard
        eyebrow="Module placeholder"
        title={title}
        description={description}
      >
        <div className="flex flex-wrap gap-3">
          <StatusChip tone="warning">
            <CircleDashed className="mr-2 h-3.5 w-3.5" />
            Scaffold ready
          </StatusChip>
          <StatusChip tone="neutral">
            <Network className="mr-2 h-3.5 w-3.5" />
            Planned endpoint: {endpoint}
          </StatusChip>
        </div>
      </SectionCard>

      <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <SectionCard
          eyebrow="Planned capabilities"
          title="What this page will support next"
          description="The visual shell is ready so we can add real workflows without reshaping the layout."
        >
          <div className="space-y-3">
            {highlights.map((highlight, index) => (
              <div
                key={highlight}
                className="rounded-2xl border border-black/10 bg-white/75 px-4 py-4"
              >
                <p className="text-xs uppercase tracking-[0.22em] text-[color:var(--muted)]">
                  Capability 0{index + 1}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-800">{highlight}</p>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Workflow note"
          title="Grounding remains the product rule"
          description="Each future screen is scoped to a single research task so retrieval, source metadata, and generated outputs stay explainable."
        >
          <div className="rounded-3xl border border-dashed border-black/10 bg-white/65 p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl border border-black/10 bg-[color:var(--accent-soft)] p-3 text-[color:var(--accent)]">
                <Waypoints className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900">Endpoint contract</p>
                <p className="text-sm text-[color:var(--muted)]">{endpoint}</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-[color:var(--muted)]">
              This scaffold intentionally keeps UI concerns, API contracts, and future workflow logic separated
              so Phase 2 and beyond can land incrementally.
            </p>
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
