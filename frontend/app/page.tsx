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

const pipelineModules = [
  { label: "arXiv search", state: "Live", ready: true },
  { label: "PDF ingestion", state: "Live", ready: true },
  { label: "Chroma indexing", state: "Live", ready: true },
  { label: "Grounded chat", state: "Live", ready: true },
  { label: "Structured compare", state: "Live", ready: true },
  { label: "Topic synthesis", state: "Live", ready: true },
];

const quickStart = [
  {
    step: "1",
    title: "Search for papers",
    note: 'Go to Search, enter a topic like "attention mechanism transformer", and review results.',
  },
  {
    step: "2",
    title: "Ingest and index",
    note: "Click Ingest then Index on 2-3 papers to build your local evidence base.",
  },
  {
    step: "3",
    title: "Chat, compare, or synthesize",
    note: "Use the paper IDs in Chat, Compare, or Synthesis to get grounded, citable answers.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-6">
      <HeroPanel />

      <section className="grid gap-4 xl:grid-cols-[1.7fr_1fr]">
        <SectionCard
          eyebrow="Workflow overview"
          title="Four stages from discovery to analysis."
          description="Each stage is structured so outputs stay grounded in paper metadata and retrieved evidence."
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
          eyebrow="Pipeline status"
          title="All workflow modules are live"
          description="Search, ingest, index, chat, compare, and synthesis are operational."
        >
          <div className="space-y-3">
            {pipelineModules.map((item) => (
              <div
                key={item.label}
                className="flex items-center justify-between gap-3 rounded-[1.45rem] border border-[color:var(--line)] bg-white/80 px-4 py-3"
              >
                <p className="text-sm font-medium text-slate-900">{item.label}</p>
                <StatusChip tone={item.ready ? "positive" : "neutral"}>
                  {item.state}
                </StatusChip>
              </div>
            ))}
          </div>
        </SectionCard>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <SectionCard
          eyebrow="Quick start"
          title="Three steps to a grounded research answer."
          description="Follow this path to go from topic search to a citable, evidence-backed response."
        >
          <div className="space-y-3">
            {quickStart.map((item) => (
              <div
                key={item.step}
                className="rounded-[1.45rem] border border-[color:var(--line)] bg-white/82 px-4 py-4"
              >
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-lg text-slate-900">{item.title}</h3>
                  <span className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                    Step {item.step}
                  </span>
                </div>
                <p className="text-sm leading-6 text-[color:var(--muted)]">{item.note}</p>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Traceability"
          title="Source provenance is visible throughout the product."
          description="Paper metadata, retrieved chunks, and citation snippets each have a dedicated home in the UI."
        >
          <div className="space-y-4">
            <div className="rounded-[1.45rem] border border-dashed border-[color:var(--accent)]/30 bg-[color:var(--accent-soft)]/88 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--accent)]">
                Evidence model
              </p>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-800">
                <li>Paper title, abstract, and arXiv source link</li>
                <li>Chunk-level evidence with page number and word boundaries</li>
                <li>Citation labels (S1, S2, ...) mapping to specific chunks</li>
                <li>Workflow metrics: retrieval, reranking, and generation timing</li>
              </ul>
            </div>
            <div className="rounded-[1.45rem] border border-[color:var(--line)] bg-white/80 p-4">
              <p className="text-sm font-medium text-slate-900">Grounding guarantee</p>
              <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">
                The model is instructed to answer only from retrieved evidence. If a field is not
                supported, it says &ldquo;Not stated in retrieved evidence&rdquo; instead of guessing.
              </p>
            </div>
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
