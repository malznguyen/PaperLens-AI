import { HeroPanel } from "@/components/hero-panel";
import { SectionCard } from "@/components/section-card";
import { StatusChip } from "@/components/status-chip";
import { WorkflowCard } from "@/components/workflow-card";

const workflowSteps = [
  {
    title: "Discover",
    description: "Search arXiv topics, inspect abstracts, and shortlist promising papers for the workspace.",
  },
  {
    title: "Ingest",
    description: "Cache PDFs, parse sections, and prepare clean chunks for embeddings and retrieval.",
  },
  {
    title: "Analyze",
    description: "Ask grounded questions and inspect evidence with source-aware traceability.",
  },
  {
    title: "Compare",
    description: "Lay multiple papers side by side to study methods, strengths, limitations, and gaps.",
  },
];

const ingestionBacklog = [
  { label: "Search connector", state: "Ready for Phase 2" },
  { label: "PDF caching pipeline", state: "Planned" },
  { label: "Chroma indexing job", state: "Planned" },
];

const recentSessions = [
  {
    title: "Transformer interpretability landscape",
    note: "Placeholder session shell for future saved runs and retrieval traces.",
  },
  {
    title: "Biomedical RAG evaluation methods",
    note: "Reserved area for compare outputs, citations, and ingestion history.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-6">
      <HeroPanel />

      <section className="grid gap-4 xl:grid-cols-[1.7fr_1fr]">
        <SectionCard
          eyebrow="Workflow overview"
          title="PaperLens AI is built around a research workflow, not an open-ended chatbot."
          description="Each stage is structured so future outputs can stay grounded in paper metadata and retrieved evidence."
        >
          <div className="grid gap-4 md:grid-cols-2">
            {workflowSteps.map((step, index) => (
              <WorkflowCard
                key={step.title}
                step={index + 1}
                title={step.title}
                description={step.description}
              />
            ))}
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Status panel"
          title="Foundation progress"
          description="Phase 1 keeps the shell visible while the retrieval pipeline is still being wired."
        >
          <div className="space-y-3">
            {ingestionBacklog.map((item) => (
              <div
                key={item.label}
                className="flex items-center justify-between rounded-2xl border border-black/10 bg-white/70 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-slate-900">{item.label}</p>
                  <p className="text-xs text-[color:var(--muted)]">Workflow module placeholder</p>
                </div>
                <StatusChip tone={item.state === "Ready for Phase 2" ? "positive" : "neutral"}>
                  {item.state}
                </StatusChip>
              </div>
            ))}
          </div>
        </SectionCard>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <SectionCard
          eyebrow="Recent sessions"
          title="Workspace memory is staged for future research threads."
          description="This panel will later store search traces, compare snapshots, and citation-aware summaries."
        >
          <div className="space-y-3">
            {recentSessions.map((session, index) => (
              <div
                key={session.title}
                className="rounded-2xl border border-black/10 bg-white/75 px-4 py-4"
              >
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-lg text-slate-900">{session.title}</h3>
                  <span className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                    Session 0{index + 1}
                  </span>
                </div>
                <p className="text-sm leading-6 text-[color:var(--muted)]">{session.note}</p>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Traceability"
          title="Source provenance will stay visible throughout the product."
          description="Paper metadata, retrieved chunks, and citation snippets each have a dedicated home in the UI contract."
        >
          <div className="space-y-4">
            <div className="rounded-2xl border border-dashed border-[color:var(--accent)]/35 bg-[color:var(--accent-soft)] p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--accent)]">
                Planned evidence model
              </p>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-800">
                <li>Paper title, abstract, and source link</li>
                <li>Chunk-level evidence with page or section metadata</li>
                <li>Grounded compare and summary outputs with citations</li>
              </ul>
            </div>
            <div className="rounded-2xl border border-black/10 bg-white/70 p-4">
              <p className="text-sm font-medium text-slate-900">API contract preview</p>
              <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">
                The frontend already targets dedicated routes for search, ingest, chat, and comparison so
                later phases can land without reorganizing the UI shell.
              </p>
            </div>
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
