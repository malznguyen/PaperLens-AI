"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import type { PaperIngestState } from "@/components/ingest-button";
import { SearchBar } from "@/components/search-bar";
import { SearchResults } from "@/components/search-results";
import { SectionCard } from "@/components/section-card";
import { ingestPaper, searchPapers, type PaperSearchResult } from "@/lib/api";

const DEFAULT_MAX_RESULTS = 10;

export function SearchExperience() {
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(DEFAULT_MAX_RESULTS);
  const [results, setResults] = useState<PaperSearchResult[]>([]);
  const [activeQuery, setActiveQuery] = useState<string | null>(null);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  const [inputError, setInputError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [ingestStates, setIngestStates] = useState<Record<string, PaperIngestState>>({});

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (isLoading) {
      return;
    }

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setInputError("Enter a topic before searching.");
      return;
    }

    setInputError(null);
    setSearchError(null);
    setPendingQuery(trimmedQuery);
    setHasSearched(true);
    setIsLoading(true);

    try {
      const response = await searchPapers({
        query: trimmedQuery,
        max_results: maxResults,
      });

      setActiveQuery(response.query);
      setResults(response.results);
    } catch (error) {
      setSearchError(
        error instanceof Error ? error.message : "Unable to search papers right now.",
      );
    } finally {
      setPendingQuery(null);
      setIsLoading(false);
    }
  }

  function handleQueryChange(nextQuery: string) {
    setQuery(nextQuery);
    if (inputError) {
      setInputError(null);
    }
  }

  async function handleIngestPaper(paper: PaperSearchResult): Promise<void> {
    if (!paper.pdf_url) {
      setIngestStates((currentStates) => ({
        ...currentStates,
        [paper.id]: {
          status: "failed",
          message: "This paper does not currently expose a PDF URL.",
        },
      }));
      return;
    }

    setIngestStates((currentStates) => ({
      ...currentStates,
      [paper.id]: {
        status: "ingesting",
        message: "Downloading the PDF and extracting text.",
      },
    }));

    try {
      const response = await ingestPaper({
        ...paper,
        pdf_url: paper.pdf_url,
      });

      setIngestStates((currentStates) => ({
        ...currentStates,
        [paper.id]: {
          status: response.status,
          message: response.message,
          pageCount: response.page_count,
          wordCount: response.word_count,
        },
      }));
    } catch (error) {
      setIngestStates((currentStates) => ({
        ...currentStates,
        [paper.id]: {
          status: "failed",
          message:
            error instanceof Error
              ? error.message
              : "Unable to ingest this paper right now.",
        },
      }));
    }
  }

  return (
    <section className="grid gap-4 xl:grid-cols-[0.92fr_1.08fr]">
      <SectionCard
        eyebrow="Search controls"
        title="Run a topic search against arXiv."
        description="Enter a research topic, choose how many papers to pull back, and review normalized metadata before moving to later workflow phases."
      >
        <SearchBar
          query={query}
          maxResults={maxResults}
          isLoading={isLoading}
          errorMessage={inputError}
          onQueryChange={handleQueryChange}
          onMaxResultsChange={setMaxResults}
          onSubmit={handleSubmit}
        />
      </SectionCard>

      <SectionCard
        eyebrow="Search results"
        title="Review papers in a source-first list."
        description="Results keep arXiv provenance visible so the workflow stays grounded from discovery onward."
      >
        <SearchResults
          results={results}
          activeQuery={activeQuery}
          pendingQuery={pendingQuery}
          errorMessage={searchError}
          hasSearched={hasSearched}
          isLoading={isLoading}
          ingestStates={ingestStates}
          onIngestPaper={handleIngestPaper}
        />
      </SectionCard>
    </section>
  );
}
