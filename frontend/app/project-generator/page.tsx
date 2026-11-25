"use client";

import { PageFrame, PageHeader } from "@/components/PageHeader";
import { SourceCard } from "@/components/SourceCard";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { MarkdownContent } from "@/components/MarkdownContent";

type ProjectSource = {
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

type ProjectGeneratorResponse = {
  goal: string;
  project_plan: string;
  collection_name: string;

  target_role: string;
  project_level: string;
  duration_weeks: number;

  detected_domains: string[];
  search_domains: string[];
  rewritten_query: string | null;
  domain_filter_used: boolean;
  fallback_used: boolean;
  retrieval_attempts: number;
  router_notes: string[];

  source_count: number;
  sources: ProjectSource[];

  elapsed_seconds: number;
  elapsed_ms: number;
};

type ProjectGeneratorRequest = {
  goal: string;
  target_role: string;
  project_level: string;
  duration_weeks: number;
  domains?: string[] | null;
  auto_detect_domains: boolean;
  limit: number;
};

export default function ProjectGeneratorPage() {
  const [goal, setGoal] = useState("");
  const [targetRole, setTargetRole] = useState("AI Security Engineer");
  const [projectLevel, setProjectLevel] = useState("advanced");
  const [durationWeeks, setDurationWeeks] = useState(8);
  const [domainsInput, setDomainsInput] = useState("");
  const [limit, setLimit] = useState(8);
  const [autoDetectDomains, setAutoDetectDomains] = useState(true);

  const [result, setResult] = useState<ProjectGeneratorResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function parseDomains(value: string): string[] | null {
    const domains = value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    return domains.length > 0 ? domains : null;
  }

  async function submitProjectGenerator() {
    if (!goal.trim()) {
      setError("Project goal is required.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: ProjectGeneratorRequest = {
      goal,
      target_role: targetRole,
      project_level: projectLevel,
      duration_weeks: durationWeeks,
      domains: parseDomains(domainsInput),
      auto_detect_domains: autoDetectDomains,
      limit,
    };

    try {
      const data = await apiPost<
        ProjectGeneratorResponse,
        ProjectGeneratorRequest
      >("/project-generator", payload);

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
        title="Project Generator"
        eyebrow="Portfolio"
        description="Turn an ebook-backed project goal into a plan with an architecture, milestones, and sources."
      />

      <form
        className="workspace-panel"
        onSubmit={(event) => {
          event.preventDefault();
          void submitProjectGenerator();
        }}
      >
        <Field label="Project goal">
          <textarea
            value={goal}
            onChange={(event) => setGoal(event.target.value)}
            rows={5}
            placeholder="Example: Design a portfolio project that combines cybersecurity, AI/ML, backend engineering, cloud, and DevOps."
            className="workspace-field"
          />
        </Field>

        <div className="mt-4 grid gap-4 md:grid-cols-4">
          <div className="md:col-span-2">
            <Field label="Target role">
              <input
                value={targetRole}
                onChange={(event) => setTargetRole(event.target.value)}
                placeholder="AI Security Engineer"
                className="workspace-field"
              />
            </Field>
          </div>

          <div>
            <Field label="Project level">
              <select
                value={projectLevel}
                onChange={(event) => setProjectLevel(event.target.value)}
                className="workspace-field"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </Field>
          </div>

          <div>
            <Field label="Duration in weeks">
              <input
                type="number"
                min={1}
                max={52}
                value={durationWeeks}
                onChange={(event) =>
                  setDurationWeeks(Number(event.target.value))
                }
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
                placeholder="cybersecurity, ai_ml, backend_development, cloud_computing, devops"
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
          {loading ? "Generating..." : "Generate Project Plan"}
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
              <span>{result.target_role}</span>
              <span>•</span>
              <span>{result.project_level}</span>
              <span>•</span>
              <span>{result.duration_weeks} weeks</span>
            </div>

            <h2 className="text-xl font-semibold">Generated Project Plan</h2>
            <div className="mt-4">
              <MarkdownContent content={result.project_plan} />
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
