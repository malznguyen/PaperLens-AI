import type { FormEventHandler } from "react";
import { LoaderCircle, MessageSquareText, SendHorizontal } from "lucide-react";

const topKOptions = [4, 6, 8, 10];

type ChatInputProps = {
  question: string;
  paperIdsInput: string;
  topK: number;
  isLoading: boolean;
  errorMessage: string | null;
  onQuestionChange: (value: string) => void;
  onPaperIdsChange: (value: string) => void;
  onTopKChange: (value: number) => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
};

export function ChatInput({
  question,
  paperIdsInput,
  topK,
  isLoading,
  errorMessage,
  onQuestionChange,
  onPaperIdsChange,
  onTopKChange,
  onSubmit,
}: ChatInputProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <label
          htmlFor="research-chat-question"
          className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]"
        >
          Research question
        </label>
        <div className="mt-2 rounded-[1.8rem] border border-black/10 bg-white/85 p-4 shadow-panel">
          <div className="flex items-start gap-3">
            <div className="rounded-2xl border border-black/10 bg-[color:var(--accent-soft)] p-3 text-[color:var(--accent)]">
              <MessageSquareText className="h-5 w-5" />
            </div>
            <textarea
              id="research-chat-question"
              name="question"
              value={question}
              onChange={(event) => onQuestionChange(event.target.value)}
              placeholder="What limitations do the indexed papers report for vision transformers in medical image classification?"
              className="min-h-[168px] w-full resize-y border-0 bg-transparent text-base leading-7 text-slate-900 outline-none placeholder:text-slate-400"
            />
          </div>
        </div>
        {errorMessage ? (
          <p className="mt-2 text-sm text-[#8a4b3a]">{errorMessage}</p>
        ) : (
          <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">
            Keep the question specific and evidence-seeking so retrieval can pull a tighter context pack.
          </p>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
        <label className="flex flex-col gap-2 text-sm text-[color:var(--muted)]">
          <span className="text-xs uppercase tracking-[0.24em]">
            Restrict to paper IDs (optional)
          </span>
          <input
            name="paperIds"
            value={paperIdsInput}
            onChange={(event) => onPaperIdsChange(event.target.value)}
            placeholder="2401.12345, 2402.67890"
            className="rounded-2xl border border-black/10 bg-white/80 px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
            autoComplete="off"
          />
        </label>

        <label className="flex flex-col gap-2 text-sm text-[color:var(--muted)]">
          <span className="text-xs uppercase tracking-[0.24em]">Top chunks</span>
          <select
            name="topK"
            value={topK}
            onChange={(event) => onTopKChange(Number(event.target.value))}
            className="rounded-2xl border border-black/10 bg-white/80 px-4 py-3 text-sm text-slate-900 outline-none"
          >
            {topKOptions.map((option) => (
              <option key={option} value={option}>
                Top {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="rounded-2xl border border-dashed border-[color:var(--accent)]/35 bg-[color:var(--accent-soft)] p-4">
          <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--accent)]">
            Grounding rule
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-800">
            Papers must already be indexed from the Search page. The answer layer only sees retrieved evidence, not the whole corpus.
          </p>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[#13212d] px-5 py-3 text-sm font-medium text-white transition hover:bg-[#1b3040] disabled:cursor-not-allowed disabled:bg-slate-500"
        >
          {isLoading ? (
            <>
              <LoaderCircle className="h-4 w-4 animate-spin" />
              Retrieving evidence
            </>
          ) : (
            <>
              <SendHorizontal className="h-4 w-4" />
              Ask grounded question
            </>
          )}
        </button>
      </div>
    </form>
  );
}
