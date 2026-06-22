"use client";

import { useState } from "react";
import Link from "next/link";
import { apiPost } from "@/lib/api";
import { MarkdownContent } from "@/components/MarkdownContent";

type AgenticRagSource = {
  source_number: number;
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
};

type AgenticRagResponse = {
  question: string;
  answer: string;
  collection_name: string;

  intent: string;
  retrieval_strategy: string;
  detected_domains: string[];
  search_domains: string[];
  rewritten_query: string | null;
  domain_filter_used: boolean;
  fallback_used: boolean;
  retrieval_attempts: number;
  router_notes: string[];

  source_count: number;
  sources: AgenticRagSource[];

  elapsed_seconds: number;
  elapsed_ms: number;
};

type AgenticRagRequest = {
  question: string;
  limit: number;
  domains?: string[] | null;
  auto_detect_domains: boolean;
};

function formatPages(source: AgenticRagSource): string {
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

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}

export default function AgenticRagPage() {
  const [question, setQuestion] = useState("");
  const [domainsInput, setDomainsInput] = useState("");
  const [limit, setLimit] = useState(8);
  const [autoDetectDomains, setAutoDetectDomains] = useState(true);

  const [result, setResult] = useState<AgenticRagResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function parseDomains(value: string): string[] | null {
    const domains = value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    return domains.length > 0 ? domains : null;
  }

  async function submitQuestion() {
    if (!question.trim()) {
      setError("Question is required.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: AgenticRagRequest = {
      question,
      limit,
      domains: parseDomains(domainsInput),
      auto_detect_domains: autoDetectDomains,
    };

    try {
      const data = await apiPost<AgenticRagResponse, AgenticRagRequest>(
        "/agentic-rag-chat",
        payload
      );

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
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

          <h1 className="mt-4 text-3xl font-bold">Agentic RAG</h1>
          <p className="mt-3 max-w-3xl text-neutral-400">
            Ask questions using intent classification, domain-aware retrieval,
            query rewriting, fallback retrieval, and source-backed generation.
          </p>
        </div>

        <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <label className="block text-sm font-medium text-neutral-300">
            Question
          </label>

          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={5}
            placeholder="Example: How do I design a secure FastAPI backend with PostgreSQL, Redis, Docker, and authentication?"
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
                max={20}
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
            onClick={submitQuestion}
            disabled={loading}
            className="mt-5 rounded-xl bg-white px-5 py-2 font-medium text-black disabled:opacity-50"
          >
            {loading ? "Thinking..." : "Ask Agentic RAG"}
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
                <span>Sources: {result.source_count}</span>
                <span>•</span>
                <span>{result.elapsed_seconds}s</span>
                <span>•</span>
                <span>Attempts: {result.retrieval_attempts}</span>
                <span>•</span>
                <span>Fallback: {result.fallback_used ? "yes" : "no"}</span>
              </div>

              <h2 className="text-xl font-semibold">Answer</h2>
              <div className="mt-4">
                <MarkdownContent content={result.answer} />
              </div>
            </section>

            <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
              <h2 className="text-xl font-semibold">Router Metadata</h2>

              <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    Intent
                  </p>
                  <p className="mt-2 font-medium capitalize">
                    {formatLabel(result.intent)}
                  </p>
                </div>

                <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    Retrieval Strategy
                  </p>
                  <p className="mt-2 font-medium capitalize">
                    {formatLabel(result.retrieval_strategy)}
                  </p>
                </div>

                <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    Domain Filter
                  </p>
                  <p className="mt-2 font-medium">
                    {result.domain_filter_used ? "Used" : "Not used"}
                  </p>
                </div>

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

                <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    Rewritten Query
                  </p>
                  <p className="mt-2 text-sm text-neutral-300">
                    {result.rewritten_query || "Not used"}
                  </p>
                </div>
              </div>

              {result.router_notes.length > 0 && (
                <div className="mt-5">
                  <p className="text-sm font-medium text-neutral-300">
                    Router Notes
                  </p>

                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-neutral-400">
                    {result.router_notes.map((note, index) => (
                      <li key={`${note}-${index}`}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </section>

            <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
              <h2 className="text-xl font-semibold">Sources</h2>

              <div className="mt-4 space-y-4">
                {result.sources.map((source) => (
                  <div
                    key={`${source.source_number}-${source.chunk_index}`}
                    className="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                  >
                    <div className="flex flex-wrap gap-2 text-xs text-neutral-500">
                      <span>Source {source.source_number}</span>
                      <span>•</span>
                      <span>Score: {source.score.toFixed(4)}</span>
                      <span>•</span>
                      <span>Pages: {formatPages(source)}</span>
                      <span>•</span>
                      <span>Chunk: {source.chunk_index ?? "N/A"}</span>
                    </div>

                    <h3 className="mt-2 font-medium">
                      {source.title || "Unknown title"}
                    </h3>

                    <p className="mt-1 text-sm text-neutral-500">
                      {source.filename || "Unknown file"}
                    </p>

                    <p className="mt-2 text-xs text-neutral-500">
                      Domains: {(source.domains || []).join(", ") || "N/A"}
                    </p>

                    <p className="mt-3 text-sm leading-6 text-neutral-300">
                      {source.chunk_preview}
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