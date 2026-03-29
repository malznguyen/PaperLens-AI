import { BookText, MessageSquareQuote, ScanSearch } from "lucide-react";

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
        eyebrow="Phase 5 live"
        title="Ask grounded research questions over indexed papers."
        description="This chat flow retrieves supporting chunks from Chroma, keeps page-aware provenance visible, and asks the model to answer only from the retrieved evidence."
      >
        <div className="flex flex-wrap gap-3">
          <StatusChip tone="positive">
            <ScanSearch className="mr-2 h-3.5 w-3.5" />
            Chroma retrieval live
          </StatusChip>
          <StatusChip tone="neutral">
            <MessageSquareQuote className="mr-2 h-3.5 w-3.5" />
            POST /api/chat
          </StatusChip>
          <StatusChip tone="neutral">
            <BookText className="mr-2 h-3.5 w-3.5" />
            Page-level citations rendered
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
