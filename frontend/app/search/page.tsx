"use client";

import { useState } from "react";
import Link from "next/link";
import { apiPost } from "@/lib/api";

type SearchResult = {
  score: number;
  document_id: string | null;
  filename: string | null;
  title: string | null;
  author: string | null;
  file_type: string | null;
  primary_domain: string | null;
  domains: string[] | null;
  page_number: number | null;
  page_start: number | null;
  page_end: number | null;
  page_numbers: number[] | null;
  chunk_index: number | null;
  chunk_preview: string | null;
  text?: string | null;
  chunk_text?: string | null;
};

type SearchResponse = {
  query: string;
  collection_name: string;
  detected_domains: string[];
  search_domains: string[];
  domain_filter_used: boolean;
  result_count?: number;
  results: SearchResult[];
  elapsed_seconds: number;
  elapsed_ms: number;
};

type SearchRequest = {
  query: string;
  limit: number;
  domains?: string[] | null;
  auto_detect_domains: boolean;
};

function parseDomains(value: string): string[] | null {
  const domains = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  return domains.length > 0 ? domains : null;
}

function formatPages(source: SearchResult): string {
  if (source.page_start !== null && source.page_end !== null) {
    if (source.page_start === source.page_end) {
      return String(source.page_start);
    }

    return `${source.page_start}-${source.page_end}`;
  }

  if (source.page_number !== null) {
    return String(source.page_number);
  }

  return "N/A";
}

function getChunkText(result: SearchResult): string {
  return (
    result.chunk_preview ||
    result.chunk_text ||
    result.text ||
    "No chunk preview available."
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [domainsInput, setDomainsInput] = useState("");
  const [limit, setLimit] = useState(10);
  const [autoDetectDomains, setAutoDetectDomains] = useState(true);

  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submitSearch() {
    if (!query.trim()) {
      setError("Search query is required.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: SearchRequest = {
      query,
      limit,
      domains: parseDomains(domainsInput),
      auto_detect_domains: autoDetectDomains,
    };

    try {
      const data = await apiPost<SearchResponse, SearchRequest>(
        "/search",
        payload
      );

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown search error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-6xl">
        <div className="mb-8">
          <Link href="/" className="text-sm text-neutral-400 hover:text-white">
            ← Back to dashboard
          </Link>

          <h1 className="mt-4 text-3xl font-bold">Semantic Search</h1>
          <p className="mt-3 max-w-3xl text-neutral-400">
            Search indexed chunks directly from Qdrant. Use this page to debug
            retrieval quality before asking the RAG or agentic RAG endpoints.
          </p>
        </div>

        <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <label className="block text-sm font-medium text-neutral-300">
            Search Query
          </label>

          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            rows={4}
            placeholder="Example: secure FastAPI authentication with PostgreSQL"
            className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
          />

          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Limit
              </label>
              <input
                type="number"
                min={1}
                max={30}
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-neutral-300">
                Domains Override
              </label>
              <input
                value={domainsInput}
                onChange={(event) => setDomainsInput(event.target.value)}
                placeholder="backend_development, cybersecurity, databases"
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
              <p className="mt-1 text-xs text-neutral-500">
                Optional. Comma-separated domains.
              </p>
            </div>
          </div>

          <label className="mt-4 flex items-center gap-2 text-sm text-neutral-300">
            <input
              type="checkbox"
              checked={autoDetectDomains}
              onChange={(event) => setAutoDetectDomains(event.target.checked)}
            />
            Auto-detect domains
          </label>

          <button
            onClick={submitSearch}
            disabled={loading}
            className="mt-5 rounded-xl bg-white px-5 py-2 font-medium text-black disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {error && (
          <pre className="mt-6 overflow-auto rounded-xl border border-red-900 bg-red-950 p-4 text-sm text-red-200">
            {error}
          </pre>
        )}

        {result && (
          <div className="mt-8 space-y-6">
            <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
              <div className="mb-3 flex flex-wrap gap-2 text-xs text-neutral-400">
                <span>Collection: {result.collection_name}</span>
                <span>•</span>
                <span>
                  Results: {result.result_count ?? result.results.length}
                </span>
                <span>•</span>
                <span>{result.elapsed_seconds}s</span>
                <span>•</span>
                <span>
                  Domain filter: {result.domain_filter_used ? "yes" : "no"}
                </span>
              </div>

              <h2 className="text-xl font-semibold">Search Metadata</h2>

              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    Detected Domains
                  </p>
                  <p className="mt-2 text-sm">
                    {result.detected_domains.join(", ") || "N/A"}
                  </p>
                </div>

                <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    Search Domains
                  </p>
                  <p className="mt-2 text-sm">
                    {result.search_domains.join(", ") || "All"}
                  </p>
                </div>
              </div>
            </section>

            <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
              <h2 className="text-xl font-semibold">Retrieved Chunks</h2>

              <div className="mt-4 space-y-4">
                {result.results.map((item, index) => (
                  <div
                    key={`${item.document_id}-${item.chunk_index}-${index}`}
                    className="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                  >
                    <div className="flex flex-wrap gap-2 text-xs text-neutral-500">
                      <span>Rank {index + 1}</span>
                      <span>•</span>
                      <span>Score: {item.score.toFixed(4)}</span>
                      <span>•</span>
                      <span>Pages: {formatPages(item)}</span>
                      <span>•</span>
                      <span>Chunk: {item.chunk_index ?? "N/A"}</span>
                    </div>

                    <h3 className="mt-2 font-medium">
                      {item.title || "Unknown title"}
                    </h3>

                    <p className="mt-1 text-sm text-neutral-500">
                      {item.filename || "Unknown file"}
                    </p>

                    <p className="mt-2 text-xs text-neutral-500">
                      Primary domain: {item.primary_domain || "N/A"}
                    </p>

                    <p className="mt-1 text-xs text-neutral-500">
                      Domains: {(item.domains || []).join(", ") || "N/A"}
                    </p>

                    <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-neutral-300">
                      {getChunkText(item)}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </section>
    </main>
  );
}