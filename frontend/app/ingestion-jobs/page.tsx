"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { apiGet, apiPatch } from "@/lib/api";

type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

type IngestionJob = {
  job_id: string;
  document_id: string | null;

  status: JobStatus | string;
  current_step: string | null;
  progress_percent: number;

  original_filename: string | null;
  stored_filename: string | null;
  upload_path: string | null;
  file_type: string | null;

  content_hash: string | null;

  source_type: string | null;
  tool_name: string | null;
  tool_version: string | null;
  version_major: number | null;
  version_minor: number | null;
  publication_year: number | null;

  is_active: boolean;
  is_deprecated: boolean;
  index_after_ingest: boolean;

  attempt_count: number;
  max_attempts: number;

  notes: string | null;
  result: Record<string, unknown> | null;
  error_message: string | null;

  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
};

type JobActionResponse = {
  job_id: string;
  status: string;
  message: string;
};

const ACTIVE_STATUSES = new Set(["queued", "running"]);

function buildJobsPath(filters: {
  status: string;
  toolName: string;
  limit: number;
}) {
  const params = new URLSearchParams();

  if (filters.status !== "all") {
    params.set("status", filters.status);
  }

  if (filters.toolName.trim()) {
    params.set("tool_name", filters.toolName.trim());
  }

  params.set("limit", String(filters.limit));

  return `/ingestion-jobs?${params.toString()}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "N/A";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    queued:
      "border-blue-800 bg-blue-950 text-blue-300",
    running:
      "border-purple-800 bg-purple-950 text-purple-300",
    completed:
      "border-green-800 bg-green-950 text-green-300",
    failed:
      "border-red-800 bg-red-950 text-red-300",
    cancelled:
      "border-neutral-700 bg-neutral-900 text-neutral-300",
  };

  const style =
    styles[status] ??
    "border-neutral-700 bg-neutral-900 text-neutral-300";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      {status}
    </span>
  );
}

function ProgressBar({
  progress,
}: {
  progress: number;
}) {
  const safeProgress = Math.max(
    0,
    Math.min(progress, 100)
  );

  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-neutral-400">
        <span>Progress</span>
        <span>{safeProgress}%</span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-neutral-800">
        <div
          className="h-full bg-neutral-200 transition-all duration-300"
          style={{ width: `${safeProgress}%` }}
        />
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-4">
      <p className="text-sm text-neutral-500">
        {label}
      </p>

      <p className="mt-2 text-2xl font-semibold text-white">
        {value}
      </p>
    </div>
  );
}

export default function IngestionJobsPage() {
  const [jobs, setJobs] = useState<IngestionJob[]>([]);

  const [statusFilter, setStatusFilter] =
    useState("all");

  const [toolName, setToolName] = useState("");
  const [limit, setLimit] = useState(50);

  const [autoRefresh, setAutoRefresh] =
    useState(true);

  const [loading, setLoading] = useState(false);
  const [actionJobId, setActionJobId] =
    useState<string | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const requestInProgress = useRef(false);

  const loadJobs = useCallback(
    async (showLoading = true) => {
      if (requestInProgress.current) {
        return;
      }

      requestInProgress.current = true;

      if (showLoading) {
        setLoading(true);
      }

      try {
        const path = buildJobsPath({
          status: statusFilter,
          toolName,
          limit,
        });

        const data =
          await apiGet<IngestionJob[]>(path);

        setJobs(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load ingestion jobs."
        );
      } finally {
        requestInProgress.current = false;

        if (showLoading) {
          setLoading(false);
        }
      }
    },
    [statusFilter, toolName, limit]
  );

  async function cancelJob(jobId: string) {
    const confirmed = window.confirm(
      "Cancel this queued ingestion job?"
    );

    if (!confirmed) {
      return;
    }

    setActionJobId(jobId);
    setError(null);

    try {
      await apiPatch<
        JobActionResponse,
        Record<string, never>
      >(
        `/ingestion-jobs/${jobId}/cancel`,
        {}
      );

      await loadJobs(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to cancel job."
      );
    } finally {
      setActionJobId(null);
    }
  }

  async function retryJob(jobId: string) {
    const confirmed = window.confirm(
      "Return this job to the ingestion queue?"
    );

    if (!confirmed) {
      return;
    }

    setActionJobId(jobId);
    setError(null);

    try {
      await apiPatch<
        JobActionResponse,
        Record<string, never>
      >(
        `/ingestion-jobs/${jobId}/retry`,
        {}
      );

      await loadJobs(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to retry job."
      );
    } finally {
      setActionJobId(null);
    }
  }

  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);

  useEffect(() => {
    if (!autoRefresh) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadJobs(false);
    }, 3000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [autoRefresh, loadJobs]);

  const counts = useMemo(() => {
    return jobs.reduce(
      (accumulator, job) => {
        accumulator.total += 1;

        if (job.status === "queued") {
          accumulator.queued += 1;
        }

        if (job.status === "running") {
          accumulator.running += 1;
        }

        if (job.status === "completed") {
          accumulator.completed += 1;
        }

        if (job.status === "failed") {
          accumulator.failed += 1;
        }

        return accumulator;
      },
      {
        total: 0,
        queued: 0,
        running: 0,
        completed: 0,
        failed: 0,
      }
    );
  }, [jobs]);

  const hasActiveJobs = jobs.some((job) =>
    ACTIVE_STATUSES.has(job.status)
  );

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-10 text-neutral-100">
      <section className="mx-auto max-w-7xl">
        <div>
          <Link
            href="/"
            className="text-sm text-neutral-400 hover:text-white"
          >
            ← Back to dashboard
          </Link>

          <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold">
                Ingestion Jobs
              </h1>

              <p className="mt-3 max-w-3xl text-neutral-400">
                Monitor background ebook ingestion,
                indexing progress, retries, failures,
                and completed jobs.
              </p>
            </div>

            <Link
              href="/ingest"
              className="rounded-xl bg-white px-4 py-2 text-sm font-medium text-black"
            >
              Upload Document
            </Link>
          </div>
        </div>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <SummaryCard
            label="Visible Jobs"
            value={counts.total}
          />

          <SummaryCard
            label="Queued"
            value={counts.queued}
          />

          <SummaryCard
            label="Running"
            value={counts.running}
          />

          <SummaryCard
            label="Completed"
            value={counts.completed}
          />

          <SummaryCard
            label="Failed"
            value={counts.failed}
          />
        </section>

        <section className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-5">
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Status
              </label>

              <select
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(event.target.value)
                }
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm outline-none focus:border-neutral-400"
              >
                <option value="all">All</option>
                <option value="queued">Queued</option>
                <option value="running">Running</option>
                <option value="completed">
                  Completed
                </option>
                <option value="failed">Failed</option>
                <option value="cancelled">
                  Cancelled
                </option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Tool Name
              </label>

              <input
                value={toolName}
                onChange={(event) =>
                  setToolName(event.target.value)
                }
                placeholder="django, fastapi, personal-rag"
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm outline-none focus:border-neutral-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Limit
              </label>

              <input
                type="number"
                min={1}
                max={200}
                value={limit}
                onChange={(event) =>
                  setLimit(Number(event.target.value))
                }
                className="mt-2 w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm outline-none focus:border-neutral-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-300">
                Live Refresh
              </label>

              <label className="mt-2 flex h-[46px] items-center gap-3 rounded-xl border border-neutral-700 bg-neutral-950 px-3">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(event) =>
                    setAutoRefresh(
                      event.target.checked
                    )
                  }
                />

                <span className="text-sm text-neutral-300">
                  Every 3 seconds
                </span>
              </label>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => void loadJobs()}
              disabled={loading}
              className="rounded-xl bg-white px-5 py-2 text-sm font-medium text-black disabled:opacity-50"
            >
              {loading
                ? "Refreshing..."
                : "Refresh Jobs"}
            </button>

            {autoRefresh && hasActiveJobs && (
              <span className="text-sm text-neutral-500">
                Live updates are active.
              </span>
            )}
          </div>
        </section>

        {error && (
          <pre className="mt-6 overflow-auto whitespace-pre-wrap rounded-xl border border-red-900 bg-red-950 p-4 text-sm text-red-200">
            {error}
          </pre>
        )}

        <section className="mt-8 space-y-4">
          {jobs.map((job) => {
            const actionRunning =
              actionJobId === job.job_id;

            return (
              <article
                key={job.job_id}
                className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-semibold text-white">
                        {job.original_filename ||
                          "Unknown document"}
                      </h2>

                      <StatusBadge
                        status={job.status}
                      />
                    </div>

                    <p className="mt-2 text-sm text-neutral-500">
                      Step:{" "}
                      {job.current_step ||
                        "Not available"}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {job.status === "queued" && (
                      <button
                        type="button"
                        disabled={actionRunning}
                        onClick={() =>
                          void cancelJob(job.job_id)
                        }
                        className="rounded-lg border border-yellow-800 px-3 py-1.5 text-xs text-yellow-300 disabled:opacity-40"
                      >
                        {actionRunning
                          ? "Cancelling..."
                          : "Cancel"}
                      </button>
                    )}

                    {(job.status === "failed" ||
                      job.status === "cancelled") && (
                      <button
                        type="button"
                        disabled={actionRunning}
                        onClick={() =>
                          void retryJob(job.job_id)
                        }
                        className="rounded-lg border border-blue-800 px-3 py-1.5 text-xs text-blue-300 disabled:opacity-40"
                      >
                        {actionRunning
                          ? "Retrying..."
                          : "Retry"}
                      </button>
                    )}
                  </div>
                </div>

                <div className="mt-5">
                  <ProgressBar
                    progress={job.progress_percent}
                  />
                </div>

                <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Job ID
                    </p>

                    <p className="mt-1 break-all font-mono text-xs text-neutral-300">
                      {job.job_id}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Document ID
                    </p>

                    <p className="mt-1 break-all font-mono text-xs text-neutral-300">
                      {job.document_id || "Pending"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Tool
                    </p>

                    <p className="mt-1 text-sm text-neutral-300">
                      {job.tool_name || "N/A"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Version
                    </p>

                    <p className="mt-1 text-sm text-neutral-300">
                      {job.tool_version ||
                        job.version_major ||
                        "N/A"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Attempts
                    </p>

                    <p className="mt-1 text-sm text-neutral-300">
                      {job.attempt_count} /{" "}
                      {job.max_attempts}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Index After Ingest
                    </p>

                    <p className="mt-1 text-sm text-neutral-300">
                      {job.index_after_ingest
                        ? "Yes"
                        : "No"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Created
                    </p>

                    <p className="mt-1 text-sm text-neutral-300">
                      {formatDate(job.created_at)}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-500">
                      Completed
                    </p>

                    <p className="mt-1 text-sm text-neutral-300">
                      {formatDate(job.completed_at)}
                    </p>
                  </div>
                </div>

                {job.error_message && (
                  <details className="mt-5 rounded-xl border border-red-900 bg-red-950">
                    <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-red-300">
                      View error details
                    </summary>

                    <pre className="overflow-auto whitespace-pre-wrap border-t border-red-900 p-4 text-xs text-red-200">
                      {job.error_message}
                    </pre>
                  </details>
                )}

                {job.result && (
                  <details className="mt-4 rounded-xl border border-neutral-800 bg-neutral-950">
                    <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-neutral-300">
                      View job result
                    </summary>

                    <pre className="overflow-auto whitespace-pre-wrap border-t border-neutral-800 p-4 text-xs text-neutral-400">
                      {JSON.stringify(
                        job.result,
                        null,
                        2
                      )}
                    </pre>
                  </details>
                )}
              </article>
            );
          })}

          {!loading && jobs.length === 0 && (
            <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-8 text-center text-neutral-400">
              No ingestion jobs found.
            </div>
          )}
        </section>
      </section>
    </main>
  );
}