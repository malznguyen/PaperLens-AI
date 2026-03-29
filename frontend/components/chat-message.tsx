import { MessageSquareQuote, TriangleAlert } from "lucide-react";

import { StatusChip } from "@/components/status-chip";
import type { ResearchChatResponse } from "@/lib/api";

type ChatMessageProps = {
  response: ResearchChatResponse;
};

export function ChatMessage({ response }: ChatMessageProps) {
  const isPartial = response.status === "partial";

  return (
    <div className="space-y-4">
      <div
        className={[
          "rounded-[1.6rem] border px-5 py-4",
          isPartial
            ? "border-[color:var(--warning)]/25 bg-[color:var(--warning)]/10"
            : "border-[color:var(--success)]/20 bg-[color:var(--success)]/10",
        ].join(" ")}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className={[
                "rounded-2xl border p-2.5",
                isPartial
                  ? "border-[color:var(--warning)]/25 bg-white/75 text-[color:var(--warning)]"
                  : "border-[color:var(--success)]/20 bg-white/75 text-[color:var(--success)]",
              ].join(" ")}
            >
              {isPartial ? (
                <TriangleAlert className="h-5 w-5" />
              ) : (
                <MessageSquareQuote className="h-5 w-5" />
              )}
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                {isPartial ? "Partial result" : "Grounded answer"}
              </p>
              <h3 className="text-2xl text-slate-900">
                {isPartial ? "Evidence retrieved, generation incomplete" : "Answer assembled from retrieved evidence"}
              </h3>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <StatusChip tone={isPartial ? "warning" : "positive"}>
              {response.status}
            </StatusChip>
            <StatusChip tone="neutral">{response.citations.length} citations</StatusChip>
            <StatusChip tone="neutral">{response.retrieved_chunks.length} chunks</StatusChip>
          </div>
        </div>

        <p className="mt-3 text-sm leading-6 text-slate-800">{response.message}</p>
      </div>

      <div className="rounded-[1.6rem] border border-black/10 bg-white/76 p-5">
        <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
          Question
        </p>
        <p className="mt-2 text-base leading-7 text-slate-900">{response.question}</p>
      </div>

      <div className="rounded-[1.6rem] border border-black/10 bg-white/82 p-5">
        <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
          Answer
        </p>
        {response.answer ? (
          <div className="mt-4 whitespace-pre-line text-sm leading-7 text-slate-800">
            {response.answer}
          </div>
        ) : (
          <p className="mt-4 text-sm leading-6 text-[color:var(--muted)]">
            Answer generation did not complete, but the retrieved evidence and citation candidates remain available below.
          </p>
        )}
      </div>
    </div>
  );
}
