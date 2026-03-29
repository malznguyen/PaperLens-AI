"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { LoaderCircle, Scale, Sparkles } from "lucide-react";

import { CitationList } from "@/components/citation-list";
import { ComparisonTable } from "@/components/comparison-table";
import { MetaMetricsCard } from "@/components/meta-metrics-card";
import { RetrievedChunkCard } from "@/components/retrieved-chunk-card";
import { SectionCard } from "@/components/section-card";
import { StatusChip } from "@/components/status-chip";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { comparePapers, type ComparePapersResponse } from "@/lib/api";
import { parsePaperIds } from "@/lib/paper-ids";

const DEFAULT_COMPARE_PROMPT =
  "Compare these papers in terms of methodology, datasets, strengths, and limitations.";

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to generate a grounded comparison right now.";
}

export function CompareExperience() {
  const [question, setQuestion] = useState(DEFAULT_COMPARE_PROMPT);
  const [paperIdsInput, setPaperIdsInput] = useState("");
  const [response, setResponse] = useState<ComparePapersResponse | null>(null);
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
    if (paperIds.length < 2 || paperIds.length > 5) {
      setInputError("Enter 2 to 5 unique indexed paper IDs before comparing.");
      return;
    }

    setInputError(null);
    setRequestError(null);
    setHasSubmitted(true);
    setIsLoading(true);

    try {
      const trimmedQuestion = question.trim();
      const nextResponse = await comparePapers({
        paper_ids: paperIds,
        question: trimmedQuestion || undefined,
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
          eyebrow="Compare controls"
          title="Align 2 to 5 indexed papers against the same criteria."
          description="This workflow retrieves evidence per selected paper, keeps citations page-level, and asks the model to fill a structured comparison table without inventing missing fields."
        >
          <form onSubmit={handleSubmit} className="space-y-5">
            <label className="block">
              <span className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                Paper IDs
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
                placeholder="2401.12345, 2402.67890, 2403.11111"
                className="mt-2 w-full rounded-2xl border border-black/10 bg-white/80 px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
                autoComplete="off"
              />
            </label>

            <label className="block">
              <span className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                Comparison prompt
              </span>
              <div className="mt-2 rounded-[1.8rem] border border-black/10 bg-white/85 p-4 shadow-panel">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl border border-black/10 bg-[color:var(--accent-soft)] p-3 text-[color:var(--accent)]">
                    <Scale className="h-5 w-5" />
                  </div>
                  <textarea
                    name="question"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder={DEFAULT_COMPARE_PROMPT}
                    className="min-h-[156px] w-full resize-y border-0 bg-transparent text-base leading-7 text-slate-900 outline-none placeholder:text-slate-400"
                  />
                </div>
              </div>
            </label>

            {inputError ? (
              <p className="text-sm text-[#8a4b3a]">{inputError}</p>
            ) : (
              <p className="text-sm leading-6 text-[color:var(--muted)]">
                Comparison only runs over papers that are already indexed from the Search page.
              </p>
            )}

            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div className="rounded-2xl border border-dashed border-[color:var(--accent)]/35 bg-[color:var(--accent-soft)] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--accent)]">
                  Grounding rule
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-800">
                  If a paper is not indexed or the retrieved evidence does not support a field, the workflow says so explicitly instead of guessing.
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
                    Comparing papers
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Compare indexed papers
                  </>
                )}
              </button>
            </div>
          </form>
        </SectionCard>

        <SectionCard
          eyebrow="Structured output"
          title="Review the grounded summary and row-by-row comparison."
          description="The result keeps the narrative summary, comparison table, citations, and evidence package together so you can inspect what the model actually saw."
        >
          {!hasSubmitted ? (
            <EmptyState
              title="No comparison yet"
              description="Enter 2 to 5 indexed paper IDs and submit a prompt to generate the grounded comparison table."
            />
          ) : null}

          {hasSubmitted && isLoading && !response ? (
            <LoadingState
              title="Retrieving evidence for each paper"
              description="Gathering chunks per selected paper, preserving provenance, and preparing the comparison prompt."
            />
          ) : null}

          {requestError && !response ? (
            <ErrorState
              title="Comparison unavailable"
              description={requestError}
            />
          ) : null}

          {response ? (
            <div className="space-y-4">
              {requestError ? (
                <ErrorState
                  compact
                  title="Could not refresh the latest comparison"
                  description={`${requestError} Showing the last successful response instead.`}
                />
              ) : null}

              {isLoading ? (
                <LoadingState
                  compact
                  title="Refreshing comparison"
                  description="Keeping the previous grounded comparison visible while the next request completes."
                />
              ) : null}

              <div className="rounded-[1.6rem] border border-black/10 bg-white/78 p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-[color:var(--muted)]">
                      Comparison summary
                    </p>
                    <h3 className="mt-2 text-2xl text-slate-900">
                      Structured answer over selected papers
                    </h3>
                  </div>

                  <StatusChip tone={response.status === "completed" ? "positive" : "warning"}>
                    {response.status}
                  </StatusChip>
                </div>

                <p className="mt-4 whitespace-pre-line text-sm leading-7 text-slate-800">
                  {response.summary ??
                    "The model could not finish the structured comparison, but the retrieved evidence package is still available below."}
                </p>
                <p className="mt-3 text-sm text-[color:var(--muted)]">{response.message}</p>
              </div>

              <MetaMetricsCard meta={response.meta} />
              <ComparisonTable rows={response.comparison_table} />
              <CitationList citations={response.citations} />
            </div>
          ) : null}
        </SectionCard>
      </section>

      {response ? (
        <SectionCard
          eyebrow="Evidence panel"
          title="Inspect the retrieved chunks behind the comparison."
          description="Each chunk stays linked to its paper ID, page number, and source URL so the comparison can be audited instead of taken on faith."
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
                  {response.retrieved_chunks.length} chunks in the comparison package
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
                  description="The comparison response did not include any retrieved evidence."
                />
              )}
            </div>
          </details>
        </SectionCard>
      ) : null}
    </div>
  );
}
