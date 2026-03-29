"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { BookMarked, LoaderCircle, Sparkles } from "lucide-react";

import { CitationList } from "@/components/citation-list";
import { MetaMetricsCard } from "@/components/meta-metrics-card";
import { RetrievedChunkCard } from "@/components/retrieved-chunk-card";
import { SectionCard } from "@/components/section-card";
import { StatusChip } from "@/components/status-chip";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { summarizeTopic, type TopicSynthesisResponse } from "@/lib/api";
import { parsePaperIds } from "@/lib/paper-ids";

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to generate a grounded topic synthesis right now.";
}

export function TopicSynthesisExperience() {
  const [topic, setTopic] = useState("");
  const [paperIdsInput, setPaperIdsInput] = useState("");
  const [response, setResponse] = useState<TopicSynthesisResponse | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [inputError, setInputError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (isLoading) {
      return;
    }

    const paperIds = parsePaperIds(paperIdsInput);
    const trimmedTopic = topic.trim();
    if (!trimmedTopic && paperIds.length === 0) {
      setInputError("Enter a topic, one or more indexed paper IDs, or both.");
      return;
    }

    setInputError(null);
    setRequestError(null);
    setHasSubmitted(true);
    setIsLoading(true);

    try {
      const nextResponse = await summarizeTopic({
        topic: trimmedTopic || undefined,
        paper_ids: paperIds.length > 0 ? paperIds : undefined,
      });
      setResponse(nextResponse);
    } catch (error) {
      setRequestError(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <section className="grid gap-4 xl:grid-cols-[0.92fr_1.08fr]">
        <SectionCard
          eyebrow="Synthesis controls"
          title="Generate a grounded topic overview across indexed evidence."
          description="You can target a topic across all indexed papers, restrict the synthesis to selected paper IDs, or combine both for a tighter literature overview."
        >
          <form onSubmit={handleSubmit} className="space-y-5">
            <label className="block">
              <span className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                Topic (optional if paper IDs are provided)
              </span>
              <div className="mt-2 rounded-[1.8rem] border border-black/10 bg-white/85 p-4 shadow-panel">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl border border-black/10 bg-[color:var(--accent-soft)] p-3 text-[color:var(--accent)]">
                    <BookMarked className="h-5 w-5" />
                  </div>
                  <textarea
                    name="topic"
                    value={topic}
                    onChange={(event) => {
                      setTopic(event.target.value);
                      if (inputError) {
                        setInputError(null);
                      }
                    }}
                    placeholder="vision transformers for medical image classification"
                    className="min-h-[120px] w-full resize-y border-0 bg-transparent text-base leading-7 text-slate-900 outline-none placeholder:text-slate-400"
                  />
                </div>
              </div>
            </label>

            <label className="block">
              <span className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                Restrict to paper IDs (optional)
              </span>
              <input
                name="paperIds"
                value={paperIdsInput}
                onChange={(event) => {
                  setPaperIdsInput(event.target.value);
                  if (inputError) {
                    setInputError(null);
                  }
                }}
                placeholder="2401.12345, 2402.67890"
                className="mt-2 w-full rounded-2xl border border-black/10 bg-white/80 px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
                autoComplete="off"
              />
            </label>

            {inputError ? (
              <p className="text-sm text-[#8a4b3a]">{inputError}</p>
            ) : (
              <p className="text-sm leading-6 text-[color:var(--muted)]">
                Research gaps and future directions are only surfaced when the retrieved evidence actually supports them.
              </p>
            )}

            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div className="rounded-2xl border border-dashed border-[color:var(--accent)]/35 bg-[color:var(--accent-soft)] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--accent)]">
                  Literature review mode
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-800">
                  The synthesis keeps themes, trends, challenges, and evidence together so you can reuse it in coursework reporting without losing traceability.
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
                    Synthesizing topic
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Generate topic synthesis
                  </>
                )}
              </button>
            </div>
          </form>
        </SectionCard>

        <SectionCard
          eyebrow="Literature overview"
          title="Read the overview, trends, and grounded follow-on ideas."
          description="This output is designed for literature-review style work: concise overview first, then structured lists for recurring themes and supported gaps."
        >
          {!hasSubmitted ? (
            <EmptyState
              title="No synthesis yet"
              description="Enter a topic, selected paper IDs, or both to generate a grounded literature overview."
            />
          ) : null}

          {hasSubmitted && isLoading && !response ? (
            <LoadingState
              title="Retrieving topic evidence"
              description="Pulling relevant chunks, keeping provenance visible, and preparing the synthesis prompt."
            />
          ) : null}

          {requestError && !response ? (
            <ErrorState
              title="Topic synthesis unavailable"
              description={requestError}
            />
          ) : null}

          {response ? (
            <div className="space-y-4">
              {requestError ? (
                <ErrorState
                  compact
                  title="Could not refresh the latest synthesis"
                  description={`${requestError} Showing the last successful synthesis instead.`}
                />
              ) : null}

              {isLoading ? (
                <LoadingState
                  compact
                  title="Refreshing synthesis"
                  description="Keeping the previous grounded synthesis visible while the next request completes."
                />
              ) : null}

              <div className="rounded-[1.6rem] border border-black/10 bg-white/78 p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                      Topic overview
                    </p>
                    <h3 className="mt-2 text-2xl text-slate-900">{response.topic}</h3>
                  </div>

                  <StatusChip tone={response.status === "completed" ? "positive" : "warning"}>
                    {response.status}
                  </StatusChip>
                </div>

                <p className="mt-4 whitespace-pre-line text-sm leading-7 text-slate-800">
                  {response.overview ??
                    "The model could not finish the literature overview, but the retrieved evidence package is still available below."}
                </p>
                <p className="mt-3 text-sm text-[color:var(--muted)]">{response.message}</p>
              </div>

              <MetaMetricsCard meta={response.meta} />

              <div className="grid gap-3 lg:grid-cols-2">
                <ListPanel title="Themes" items={response.themes} />
                <ListPanel title="Trends" items={response.trends} />
                <ListPanel title="Open challenges" items={response.open_challenges} />
                <ListPanel title="Research gaps" items={response.research_gaps} />
                <ListPanel title="Future directions" items={response.future_directions} className="lg:col-span-2" />
              </div>

              <CitationList citations={response.citations} />
            </div>
          ) : null}
        </SectionCard>
      </section>

      {response ? (
        <SectionCard
          eyebrow="Evidence panel"
          title="Inspect the exact chunks behind the synthesis."
          description="The synthesis response exposes the retrieved chunk package so claims about trends, challenges, or gaps can be traced back to specific paper pages."
        >
          <details
            className="rounded-[1.6rem] border border-black/10 bg-white/78 p-5"
            open
          >
            <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                  Retrieved evidence
                </p>
                <h3 className="text-2xl text-slate-900">
                  {response.retrieved_chunks.length} chunks in the synthesis package
                </h3>
              </div>

              <div className="flex flex-wrap gap-2">
                <StatusChip tone="neutral">{response.retrieved_chunks.length} chunks</StatusChip>
                <StatusChip tone="neutral">{response.citations.length} citation refs</StatusChip>
              </div>
            </summary>

            <div className="mt-5 space-y-3">
              {response.retrieved_chunks.length > 0 ? (
                response.retrieved_chunks.map((chunk) => (
                  <RetrievedChunkCard key={chunk.chunk_id} chunk={chunk} />
                ))
              ) : (
                <EmptyState
                  compact
                  title="No retrieved chunks returned"
                  description="The synthesis response did not include any retrieved evidence."
                />
              )}
            </div>
          </details>
        </SectionCard>
      ) : null}
    </div>
  );
}

type ListPanelProps = {
  title: string;
  items: string[];
  className?: string;
};

function ListPanel({ title, items, className }: ListPanelProps) {
  return (
    <div className={`rounded-[1.6rem] border border-black/10 bg-white/78 p-5 ${className ?? ""}`}>
      <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">{title}</p>

      {items.length > 0 ? (
        <div className="mt-4 space-y-3">
          {items.map((item) => (
            <div
              key={`${title}-${item}`}
              className="rounded-2xl border border-black/10 bg-[#f6f0e7] px-4 py-4"
            >
              <p className="text-sm leading-6 text-slate-800">{item}</p>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          compact
          title={`No ${title.toLowerCase()} returned`}
          description="The retrieved evidence did not support a grounded item in this category."
        />
      )}
    </div>
  );
}
