"use client";

import { PageFrame, PageHeader } from "@/components/PageHeader";
import { SourceCard } from "@/components/SourceCard";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { useState } from "react";
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
        payload,
      );

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown search error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageFrame>
      <PageHeader
        title="Semantic Search"
        eyebrow="Retrieval"
        description="Find relevant passages in your indexed ebooks and inspect the ranked sources."
      />

      <form
        className="workspace-panel"
        onSubmit={(event) => {
          event.preventDefault();
          void submitSearch();
        }}
      >
        <Field label="Search query">
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            rows={4}
            placeholder="Example: secure FastAPI authentication with PostgreSQL"
            className="workspace-field"
          />
        </Field>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div>
            <Field label="Result limit">
              <input
                type="number"
                min={1}
                max={30}
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
                className="workspace-field"
              />
            </Field>
          </div>

          <div className="md:col-span-2">
            <Field
              label="Domain override"
              hint="Optional. Comma-separated domains."
            >
              <input
                value={domainsInput}
                onChange={(event) => setDomainsInput(event.target.value)}
                placeholder="backend_development, cybersecurity, databases"
                className="workspace-field"
              />
            </Field>
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
          type="submit"
          disabled={loading}
          className="workspace-button mt-5"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {loading && (
        <div className="mt-5">
          <StatusMessage tone="info">
            Working with your ebook library…
          </StatusMessage>
        </div>
      )}

      {error && (
        <div className="mt-5">
          <StatusMessage tone="error">{error}</StatusMessage>
        </div>
      )}

      {result && (
        <div className="mt-8 space-y-6">
          <section className="workspace-panel">
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

          <section className="workspace-panel">
            <h2 className="text-xl font-semibold">Retrieved Chunks</h2>

            <div className="mt-4 space-y-4">
              {result.results.length === 0 && (
                <StatusMessage tone="info">
                  No passages matched this query. Try different wording or a
                  broader domain.
                </StatusMessage>
              )}
              {result.results.map((item, index) => (
                <SourceCard
                  key={`${item.document_id}-${item.chunk_index}-${index}`}
                  source={item}
                  rank={index + 1}
                />
              ))}
            </div>
          </section>
        </div>
      )}
    </PageFrame>
  );
}
