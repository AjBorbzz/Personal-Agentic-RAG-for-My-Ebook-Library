"use client";

import { PageFrame, PageHeader } from "@/components/PageHeader";
import { SourceCard } from "@/components/SourceCard";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { MarkdownContent } from "@/components/MarkdownContent";

type ArchitectureReviewSource = {
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

type ArchitectureReviewResponse = {
  system_description: string;
  architecture_review: string;
  collection_name: string;

  goals: string[];
  constraints: string[];
  review_focus: string[];
  target_scale: string;

  detected_domains: string[];
  search_domains: string[];
  rewritten_query: string | null;
  domain_filter_used: boolean;
  fallback_used: boolean;
  retrieval_attempts: number;
  router_notes: string[];

  source_count: number;
  sources: ArchitectureReviewSource[];

  elapsed_seconds: number;
  elapsed_ms: number;
};

type ArchitectureReviewRequest = {
  system_description: string;
  goals: string[];
  constraints: string[];
  review_focus: string[];
  target_scale: string;
  domains?: string[] | null;
  auto_detect_domains: boolean;
  limit: number;
};

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

export default function ArchitectureReviewPage() {
  const [systemDescription, setSystemDescription] = useState("");
  const [goalsInput, setGoalsInput] = useState("");
  const [constraintsInput, setConstraintsInput] = useState("");
  const [reviewFocusInput, setReviewFocusInput] = useState(
    "security, scalability, reliability, data model, API design, observability, deployment",
  );
  const [targetScale, setTargetScale] = useState(
    "single user local system with thousands of ebooks",
  );
  const [domainsInput, setDomainsInput] = useState("");
  const [limit, setLimit] = useState(8);
  const [autoDetectDomains, setAutoDetectDomains] = useState(true);

  const [result, setResult] = useState<ArchitectureReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submitArchitectureReview() {
    if (!systemDescription.trim()) {
      setError("System description is required.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: ArchitectureReviewRequest = {
      system_description: systemDescription,
      goals: parseCommaSeparated(goalsInput),
      constraints: parseCommaSeparated(constraintsInput),
      review_focus: parseCommaSeparated(reviewFocusInput),
      target_scale: targetScale,
      domains: parseDomains(domainsInput),
      auto_detect_domains: autoDetectDomains,
      limit,
    };

    try {
      const data = await apiPost<
        ArchitectureReviewResponse,
        ArchitectureReviewRequest
      >("/architecture-review", payload);

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
        title="Architecture Review"
        eyebrow="Portfolio"
        description="Review a system design against your indexed books for reliability, security, scalability, and deployment risks."
      />

      <form
        className="workspace-panel"
        onSubmit={(event) => {
          event.preventDefault();
          void submitArchitectureReview();
        }}
      >
        <Field label="System description">
          <textarea
            value={systemDescription}
            onChange={(event) => setSystemDescription(event.target.value)}
            rows={7}
            placeholder="Example: A FastAPI backend with PostgreSQL, Redis, Docker, Qdrant, Ollama, and agent endpoints for RAG, learning paths, project generation, architecture review, and code review."
            className="workspace-field"
          />
        </Field>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <Field label="Goals" hint="Comma-separated goals.">
              <textarea
                value={goalsInput}
                onChange={(event) => setGoalsInput(event.target.value)}
                rows={3}
                placeholder="Private ebook learning assistant, Portfolio-grade AI engineering project"
                className="workspace-field"
              />
            </Field>
          </div>

          <div>
            <Field label="Constraints" hint="Comma-separated constraints.">
              <textarea
                value={constraintsInput}
                onChange={(event) => setConstraintsInput(event.target.value)}
                rows={3}
                placeholder="Run locally, Avoid cloud cost, Preserve source citations"
                className="workspace-field"
              />
            </Field>
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <Field label="Review focus" hint="Comma-separated review areas.">
              <input
                value={reviewFocusInput}
                onChange={(event) => setReviewFocusInput(event.target.value)}
                placeholder="security, scalability, reliability"
                className="workspace-field"
              />
            </Field>
          </div>

          <div>
            <Field label="Target scale">
              <input
                value={targetScale}
                onChange={(event) => setTargetScale(event.target.value)}
                placeholder="single user local system with thousands of ebooks"
                className="workspace-field"
              />
            </Field>
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div>
            <Field label="Source limit">
              <input
                type="number"
                min={3}
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
                placeholder="backend_development, ai_ml, databases, devops, system_architecture, cybersecurity"
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
          {loading ? "Reviewing..." : "Review Architecture"}
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
              <span>Scale: {result.target_scale}</span>
            </div>

            <h2 className="text-xl font-semibold">Architecture Review</h2>
            <div className="mt-4">
              <MarkdownContent content={result.architecture_review} />
            </div>
          </section>

          <section className="workspace-panel">
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
                <p className="mt-2 font-medium">{result.retrieval_attempts}</p>
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
