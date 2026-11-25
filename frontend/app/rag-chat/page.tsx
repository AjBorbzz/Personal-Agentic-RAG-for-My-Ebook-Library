"use client";

import { PageFrame, PageHeader } from "@/components/PageHeader";
import { SourceCard } from "@/components/SourceCard";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { MarkdownContent } from "@/components/MarkdownContent";

type RagSource = {
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

type RagChatResponse = {
  question: string;
  answer: string;
  collection_name: string;
  detected_domains: string[];
  search_domains: string[];
  domain_filter_used: boolean;
  source_count: number;
  sources: RagSource[];
  elapsed_seconds: number;
  elapsed_ms: number;
};

type RagChatRequest = {
  question: string;
  limit: number;
  domains?: string[] | null;
  auto_detect_domains: boolean;
};

export default function RagChatPage() {
  const [question, setQuestion] = useState("");
  const [domainsInput, setDomainsInput] = useState("");
  const [limit, setLimit] = useState(5);
  const [autoDetectDomains, setAutoDetectDomains] = useState(true);

  const [result, setResult] = useState<RagChatResponse | null>(null);
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

    const payload: RagChatRequest = {
      question,
      limit,
      domains: parseDomains(domainsInput),
      auto_detect_domains: autoDetectDomains,
    };

    try {
      const data = await apiPost<RagChatResponse, RagChatRequest>(
        "/rag-chat",
        payload,
      );

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageFrame>
      <PageHeader
        title="RAG Chat"
        eyebrow="Retrieval"
        description="Ask your indexed ebook library a question and review the passages behind the answer."
      />

      <form
        className="workspace-panel"
        onSubmit={(event) => {
          event.preventDefault();
          void submitQuestion();
        }}
      >
        <Field label="Question">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={5}
            placeholder="Example: How do I design a secure backend API?"
            className="workspace-field"
          />
        </Field>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div>
            <Field label="Source limit">
              <input
                type="number"
                min={1}
                max={20}
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
                placeholder="backend_development, cybersecurity"
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
          {loading ? "Thinking..." : "Ask"}
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
              <span>Sources: {result.source_count}</span>
              <span>•</span>
              <span>{result.elapsed_seconds}s</span>
              <span>•</span>
              <span>
                Domain filter: {result.domain_filter_used ? "yes" : "no"}
              </span>
            </div>

            <h2 className="text-xl font-semibold">Answer</h2>
            <div className="mt-4">
              <MarkdownContent content={result.answer} />
            </div>
          </section>

          <section className="workspace-panel">
            <h2 className="text-xl font-semibold">Routing Metadata</h2>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm text-neutral-400">Detected Domains</p>
                <p className="mt-1 text-sm">
                  {result.detected_domains.join(", ") || "N/A"}
                </p>
              </div>

              <div>
                <p className="text-sm text-neutral-400">Search Domains</p>
                <p className="mt-1 text-sm">
                  {result.search_domains.join(", ") || "All"}
                </p>
              </div>
            </div>
          </section>

          <section className="workspace-panel">
            <h2 className="text-xl font-semibold">Sources</h2>

            <div className="mt-4 space-y-4">
              {result.sources.map((source) => (
                <SourceCard
                  key={`${source.source_number}-${source.chunk_index}`}
                  source={source}
                />
              ))}
            </div>
          </section>
        </div>
      )}
    </PageFrame>
  );
}
