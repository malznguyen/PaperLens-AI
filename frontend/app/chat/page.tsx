import { BookText, ScanSearch } from "lucide-react";

import { ChatExperience } from "@/components/chat-experience";
import { SectionCard } from "@/components/section-card";
import { StatusChip } from "@/components/status-chip";

const chatHighlights = [
  {
    label: "Retrieval first",
    detail: "Questions search indexed Chroma chunks before any generation step is allowed to answer.",
  },
  {
    label: "Citation ready",
    detail: "Every answer comes back with paper title, paper ID, page number, and chunk-level provenance.",
  },
  {
    label: "Failure transparent",
    detail: "If generation fails, the UI still surfaces the retrieved evidence instead of hiding the grounding layer.",
  },
];

export default function ChatPage() {
  return (
    <div className="space-y-6">
      <SectionCard
        eyebrow="Grounded Q&A"
        title="Ask research questions over indexed papers."
        description="Questions retrieve supporting chunks from the vector store, and the model answers only from the retrieved evidence with page-level citations."
      >
        <div className="flex flex-wrap gap-3">
          <StatusChip tone="positive">
            <ScanSearch className="mr-2 h-3.5 w-3.5" />
            Retrieval-augmented generation
          </StatusChip>
          <StatusChip tone="positive">
            <BookText className="mr-2 h-3.5 w-3.5" />
            Page-level citations
          </StatusChip>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {chatHighlights.map((highlight) => (
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

      <ChatExperience />
    </div>
  );
}
