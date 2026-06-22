"use client";

import { useState } from "react";
import Link from "next/link";
import { apiPost } from "@/lib/api";
import { MarkdownContent } from "@/components/MarkdownContent";

type LearningPathSource = {
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

type LearningPathResponse = {
  goal: string;
  learning_path: string;
  collection_name: string;

  detected_domains: string[];
  search_domains: string[];
  rewritten_query: string | null;
  domain_filter_used: boolean;
  fallback_used: boolean;
  retrieval_attempts: number;
  router_notes: string[];

  duration_weeks: number;
  hours_per_week: number;
  current_level: string;
  target_level: string;

  source_count: number;
  sources: LearningPathSource[];

  elapsed_seconds: number;
  elapsed_ms: number;
};

type LearningPathRequest = {
  goal: string;
  duration_weeks: number;
  hours_per_week: number;
  current_level: string;
  target_level: string;
  domains?: string[] | null;
  auto_detect_domains: boolean;
  limit: number;
};

function formatPages(source: LearningPathSource): string {
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

export default function LearningPathPage() {
  const [goal, setGoal] = useState("");
  const [durationWeeks, setDurationWeeks] = useState(8);
  const [hoursPerWeek, setHoursPerWeek] = useState(5);
  const [currentLevel, setCurrentLevel] = useState("intermediate");
  const [targetLevel, setTargetLevel] = useState("advanced");
  const [domainsInput, setDomainsInput] = useState("");
  const [limit, setLimit] = useState(8);
  const [autoDetectDomains, setAutoDetectDomains] = useState(true);

  const [result, setResult] = useState<LearningPathResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function parseDomains(value: string): string[] | null {
    const domains = value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    return domains.length > 0 ? domains : null;
  }

  async function submitLearningPath() {
    if (!goal.trim()) {
      setError("Goal is required.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload: LearningPathRequest = {
      goal,
      duration_weeks: durationWeeks,
      hours_per_week: hoursPerWeek,
      current_level: currentLevel,
      target_level: targetLevel,
      domains: parseDomains(domainsInput),
      auto_detect_domains: autoDetectDomains,
      limit,
    };

    try {
      const data = await apiPost<LearningPathResponse, LearningPathRequest>(
        "/learning-path",
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

          <h1 className="mt-4 text-3xl font-bold">Learning Path</h1>
          <p className="mt-3 max-w-3xl text-neutral-400">
            Generate a source-backed learning plan from your indexed ebook
            library. Useful for structured study, upskilling, and portfolio
            planning.
          </p>
        </div>

        <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <label className="block text-sm font-medium text-neutral-300">
            Learning Goal
          </label>

          <textarea
            value={goal}
            onChange={(event) => setGoal(event.target.value)}
            rows={5}
            placeholder="Example: I want to become strong in AI security engineering using cybersecurity, backend, cloud, and AI/ML concepts."
            className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
          />

          <div className="mt-4 grid gap-4 md:grid-cols-4">
            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Duration Weeks
              </label>
              <input
                type="number"
                min={1}
                max={52}
                value={durationWeeks}
                onChange={(event) =>
                  setDurationWeeks(Number(event.target.value))
                }
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Hours / Week
              </label>
              <input
                type="number"
                min={1}
                max={80}
                value={hoursPerWeek}
                onChange={(event) =>
                  setHoursPerWeek(Number(event.target.value))
                }
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Current Level
              </label>
              <select
                value={currentLevel}
                onChange={(event) => setCurrentLevel(event.target.value)}
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Target Level
              </label>
              <select
                value={targetLevel}
                onChange={(event) => setTargetLevel(event.target.value)}
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none focus:border-neutral-400"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-3">
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

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-neutral-300">
                Domains Override
              </label>
              <input
                value={domainsInput}
                onChange={(event) => setDomainsInput(event.target.value)}
                placeholder="cybersecurity, ai_ml, backend_development, cloud_computing"
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
            onClick={submitLearningPath}
            disabled={loading}
            className="mt-5 rounded-xl bg-white px-5 py-2 font-medium text-black disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate Learning Path"}
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
                <span>{result.duration_weeks} weeks</span>
                <span>•</span>
                <span>{result.hours_per_week} hrs/week</span>
              </div>

              <h2 className="text-xl font-semibold">Generated Learning Path</h2>
              <div className="mt-4">
                <MarkdownContent content={result.learning_path} />
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