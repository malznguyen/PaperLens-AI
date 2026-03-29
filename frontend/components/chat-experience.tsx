"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import { ChatInput } from "@/components/chat-input";
import { ChatMessage } from "@/components/chat-message";
import { CitationList } from "@/components/citation-list";
import { RetrievedChunkCard } from "@/components/retrieved-chunk-card";
import { MetaMetricsCard } from "@/components/meta-metrics-card";
import { SectionCard } from "@/components/section-card";
import { StatusChip } from "@/components/status-chip";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import {
  researchChat,
  type ResearchChatResponse,
} from "@/lib/api";
import { parsePaperIds } from "@/lib/paper-ids";

const DEFAULT_TOP_K = 6;

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to generate a grounded answer right now.";
}

export function ChatExperience() {
  const [question, setQuestion] = useState("");
  const [paperIdsInput, setPaperIdsInput] = useState("");
  const [topK, setTopK] = useState(DEFAULT_TOP_K);
  const [response, setResponse] = useState<ResearchChatResponse | null>(null);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [inputError, setInputError] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (isLoading) {
      return;
    }

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setInputError("Enter a research question before sending.");
      return;
    }

    setInputError(null);
    setRequestError(null);
    setPendingQuestion(trimmedQuestion);
    setHasSubmitted(true);
    setIsLoading(true);

    try {
      const paperIds = parsePaperIds(paperIdsInput);
      const nextResponse = await researchChat({
        question: trimmedQuestion,
        paper_ids: paperIds.length > 0 ? paperIds : undefined,
        top_k: topK,
      });

      setResponse(nextResponse);
    } catch (error) {
      setRequestError(getErrorMessage(error));
    } finally {
      setPendingQuestion(null);
      setIsLoading(false);
    }
  }

  function handleQuestionChange(value: string) {
    setQuestion(value);
    if (inputError) {
      setInputError(null);
    }
  }

  const shouldShowFullError = Boolean(requestError && !response);

  return (
    <div className="space-y-4">
      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <SectionCard
          eyebrow="Question controls"
          title="Focus the question and retrieval window."
          description="Ask about methods, limitations, datasets, comparisons, or findings. You can optionally scope retrieval to a small set of already indexed paper IDs."
        >
          <ChatInput
            question={question}
            paperIdsInput={paperIdsInput}
            topK={topK}
            isLoading={isLoading}
            errorMessage={inputError}
            onQuestionChange={handleQuestionChange}
            onPaperIdsChange={setPaperIdsInput}
            onTopKChange={setTopK}
            onSubmit={handleSubmit}
          />
        </SectionCard>

        <SectionCard
          eyebrow="Grounded answer"
          title="Review the answer and source traceability."
          description="The model is asked to answer only from the retrieved chunks, and the UI keeps the provenance package visible instead of hiding the retrieval layer."
        >
          {!hasSubmitted ? (
            <EmptyState
              title="Ask a question over indexed papers"
              description="Once you send a question, the grounded answer, citation list, and evidence package will appear here."
            />
          ) : null}

          {hasSubmitted && isLoading && !response ? (
            <LoadingState
              title="Retrieving evidence and assembling context"
              description="Searching indexed chunks, preserving provenance, and preparing a grounded answer request."
            />
          ) : null}

          {shouldShowFullError ? (
            <ErrorState
              title="Research chat unavailable"
              description={requestError ?? "Unable to generate a grounded answer right now."}
            />
          ) : null}

          {response ? (
            <div className="space-y-4">
              {requestError ? (
                <ErrorState
                  compact
                  title="Could not refresh the latest answer"
                  description={`${requestError} Showing the last successful response instead.`}
                />
              ) : null}

              {isLoading && pendingQuestion ? (
                <LoadingState
                  compact
                  title={`Refreshing for "${pendingQuestion}"`}
                  description="Keeping the last successful grounded response visible while the next request completes."
                />
              ) : null}

              <ChatMessage response={response} />
              <MetaMetricsCard meta={response.meta} />
              <CitationList citations={response.citations} />
            </div>
          ) : null}
        </SectionCard>
      </section>

      {response ? (
        <SectionCard
          eyebrow="Evidence panel"
          title="Inspect the exact chunks used for grounding."
          description="This panel shows the retrieved chunk package sent into answer generation, with page numbers, chunk IDs, and source URLs preserved."
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
                  {response.retrieved_chunks.length} chunks in the grounded context package
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
                  description="The chat response did not include a context package for this request."
                />
              )}
            </div>
          </details>
        </SectionCard>
      ) : null}
    </div>
  );
}
