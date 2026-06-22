"use client";

import { useState } from "react";
import Link from "next/link";
import { apiPost } from "@/lib/api";
import { MarkdownContent } from "@/components/MarkdownContent";

type CodeReviewSource = {
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

type CodeReviewResponse = {
  language: string;
  code_context: string;
  code_review: string;
  collection_name: string;

  review_focus: string[];

  detected_domains: string[];
  search_domains: string[];
  rewritten_query: string | null;
  domain_filter_used: boolean;
  fallback_used: boolean;
  retrieval_attempts: number;
  router_notes: string[];

  source_count: number;
  sources: CodeReviewSource[];

  elapsed_seconds: number;
  elapsed_ms: number;
};

type CodeReviewRequest = {
  code: string;
  language: string;
  code_context: string;
  review_focus: string[];
  domains?: string[] | null;
  auto_detect_domains: boolean;
  limit: number;
  max_code_chars: number;
};

function formatPages(source: CodeReviewSource): string {
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

function parseCommaSeparated(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseDomains(value: string): string[] | null {
  const domains = parseCommaSeparated(value);
  return domains.length > 0 ? domains : null;
}

export default function CodeReviewPage() {
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [codeContext, setCodeContext] = useState(
    "Review this code for correctness, security, reliability, performance, maintainability, and testing."
  );
  const [reviewFocusInput, setReviewFocusInput] = useState(
    "correctness, security, reliability, performance, maintainability, testing"
  );
  const [domainsInput, setDomainsInput] = useState("");
  const [limit, setLimit] = useState(5);
  const [maxCodeChars, setMaxCodeChars] = useState(12000);
  const [autoDetectDomains, setAutoDetectDomains] = useState(true);

  const [result, setResult] = useState<CodeReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submitCodeReview() {
    if (!code.trim()) {
      setError("Code is required.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: CodeReviewRequest = {
      code,
      language,
      code_context: codeContext,
      review_focus: parseCommaSeparated(reviewFocusInput),
      domains: parseDomains(domainsInput),
      auto_detect_domains: autoDetectDomains,
      limit,
      max_code_chars: maxCodeChars,
    };

    try {
      const data = await apiPost<CodeReviewResponse, CodeReviewRequest>(
        "/code-review",
        payload
      );

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  function loadSampleCode() {
    setLanguage("python");
    setCodeContext(
      "FastAPI login API using SQLite. Review for security, reliability, maintainability, and testing issues."
    );
    setDomainsInput("backend_development, cybersecurity, databases");
    setCode(`from fastapi import FastAPI, Request
import sqlite3

app = FastAPI()


@app.post("/login")
async def login(request: Request):
    data = await request.json()

    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)

    user = cursor.fetchone()

    if user:
        return {
            "status": "success",
            "message": "Login successful",
            "user": user,
            "password": password,
        }

    return {
        "status": "failed",
        "message": "Invalid credentials",
    }`);
  }

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-6xl">
        <div className="mb-8">
          <Link href="/" className="text-sm text-neutral-400 hover:text-white">
            ← Back to dashboard
          </Link>

          <h1 className="mt-4 text-3xl font-bold">Code Review</h1>
          <p className="mt-3 max-w-3xl text-neutral-400">
            Paste code and review it using your ebook-backed knowledge base.
            Useful for backend code, RAG pipeline code, SOC automation scripts,
            XSOAR/XSIAM helpers, and portfolio project files.
          </p>
        </div>

        <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="block text-sm font-medium text-neutral-300">
              Code
            </label>

            <button
              onClick={loadSampleCode}
              type="button"
              className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs text-neutral-300 hover:border-neutral-500 hover:text-white"
            >
              Load Sample Buggy FastAPI Code
            </button>
          </div>

          <textarea
            value={code}
            onChange={(event) => setCode(event.target.value)}
            rows={18}
            placeholder="Paste code here..."
            spellCheck={false}
            className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 font-mono text-sm text-neutral-100 outline-none focus:border-neutral-400"
          />

          <div className="mt-4 grid gap-4 md:grid-cols-4">
            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Language
              </label>
              <input
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
                placeholder="python"
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Limit
              </label>
              <input
                type="number"
                min={3}
                max={20}
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Max Code Chars
              </label>
              <input
                type="number"
                min={1000}
                max={50000}
                value={maxCodeChars}
                onChange={(event) =>
                  setMaxCodeChars(Number(event.target.value))
                }
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Auto Domains
              </label>
              <label className="mt-5 flex items-center gap-2 text-sm text-neutral-300">
                <input
                  type="checkbox"
                  checked={autoDetectDomains}
                  onChange={(event) =>
                    setAutoDetectDomains(event.target.checked)
                  }
                />
                Enabled
              </label>
            </div>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-neutral-300">
              Code Context
            </label>
            <textarea
              value={codeContext}
              onChange={(event) => setCodeContext(event.target.value)}
              rows={3}
              placeholder="Explain what this code is supposed to do."
              className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
            />
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Review Focus
              </label>
              <input
                value={reviewFocusInput}
                onChange={(event) => setReviewFocusInput(event.target.value)}
                placeholder="correctness, security, reliability"
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
              <p className="mt-1 text-xs text-neutral-500">
                Comma-separated review areas.
              </p>
            </div>

            <div>
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

          <button
            onClick={submitCodeReview}
            disabled={loading}
            className="mt-5 rounded-xl bg-white px-5 py-2 font-medium text-black disabled:opacity-50"
          >
            {loading ? "Reviewing..." : "Review Code"}
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
                <span>Language: {result.language}</span>
              </div>

              <h2 className="text-xl font-semibold">Code Review</h2>
              <div className="mt-4">
                <MarkdownContent content={result.code_review} />
              </div>
            </section>

            <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
              <h2 className="text-xl font-semibold">Routing Metadata</h2>

              <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
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
                    Retrieval Attempts
                  </p>
                  <p className="mt-2 font-medium">
                    {result.retrieval_attempts}
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
                    Fallback
                  </p>
                  <p className="mt-2 font-medium">
                    {result.fallback_used ? "Used" : "Not used"}
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