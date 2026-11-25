"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageFrame, PageHeader } from "@/components/PageHeader";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import { apiGet, apiPatch } from "@/lib/api";

type JobStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

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
    queued: "border-blue-800 bg-blue-950 text-blue-300",
    running: "border-purple-800 bg-purple-950 text-purple-300",
    completed: "border-green-800 bg-green-950 text-green-300",
    failed: "border-red-800 bg-red-950 text-red-300",
    cancelled: "border-neutral-700 bg-neutral-900 text-neutral-300",
  };

  const style =
    styles[status] ?? "border-neutral-700 bg-neutral-900 text-neutral-300";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      {status}
    </span>
  );
}

function ProgressBar({ progress }: { progress: number }) {
  const safeProgress = Math.max(0, Math.min(progress, 100));

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

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-4">
      <p className="text-sm text-neutral-500">{label}</p>

      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

export default function IngestionJobsPage() {
  const [jobs, setJobs] = useState<IngestionJob[]>([]);

  const [statusFilter, setStatusFilter] = useState("all");

  const [toolName, setToolName] = useState("");
  const [limit, setLimit] = useState(50);

  const [autoRefresh, setAutoRefresh] = useState(true);

  const [loading, setLoading] = useState(true);
  const [actionJobId, setActionJobId] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);

  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshCount, setRefreshCount] = useState(0);

  function refreshJobs() {
    setLoading(true);
    setLoadError(null);
    setRefreshCount((count) => count + 1);
  }

  async function cancelJob(jobId: string) {
    const confirmed = window.confirm("Cancel this queued ingestion job?");

    if (!confirmed) {
      return;
    }

    setActionJobId(jobId);
    setError(null);

    try {
      await apiPatch<JobActionResponse, Record<string, never>>(
        `/ingestion-jobs/${jobId}/cancel`,
        {},
      );

      refreshJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel job.");
    } finally {
      setActionJobId(null);
    }
  }

  async function retryJob(jobId: string) {
    const confirmed = window.confirm("Return this job to the ingestion queue?");

    if (!confirmed) {
      return;
    }

    setActionJobId(jobId);
    setError(null);

    try {
      await apiPatch<JobActionResponse, Record<string, never>>(
        `/ingestion-jobs/${jobId}/retry`,
        {},
      );

      refreshJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to retry job.");
    } finally {
      setActionJobId(null);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    const path = buildJobsPath({
      status: statusFilter,
      toolName,
      limit: Math.min(200, Math.max(1, limit || 50)),
    });
    let pending = false;

    async function loadJobs() {
      if (pending) return;
      pending = true;

      try {
        const data = await apiGet<IngestionJob[]>(path, {
          signal: controller.signal,
        });
        if (!controller.signal.aborted) {
          setJobs(data);
          setLoadError(null);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setLoadError(
            err instanceof Error
              ? err.message
              : "Failed to load ingestion jobs.",
          );
        }
      } finally {
        pending = false;
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void loadJobs();
    const intervalId = autoRefresh
      ? window.setInterval(loadJobs, 3000)
      : undefined;

    return () => {
      controller.abort();
      window.clearInterval(intervalId);
    };
  }, [statusFilter, toolName, limit, autoRefresh, refreshCount]);

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
      },
    );
  }, [jobs]);

  const hasActiveJobs = jobs.some((job) => ACTIVE_STATUSES.has(job.status));

  return (
    <PageFrame width="wide" className="space-y-6">
      <PageHeader
        title="Ingestion Jobs"
        description="Follow ebook uploads as they are parsed and indexed for retrieval. Retry failed jobs or cancel queued ones."
        actions={
          <Link href="/ingest" className="workspace-button">
            Upload document
          </Link>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <SummaryCard label="Visible Jobs" value={counts.total} />

        <SummaryCard label="Queued" value={counts.queued} />

        <SummaryCard label="Running" value={counts.running} />

        <SummaryCard label="Completed" value={counts.completed} />

        <SummaryCard label="Failed" value={counts.failed} />
      </section>

      <section className="workspace-panel">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Status">
            <select
              value={statusFilter}
              onChange={(event) => {
                setLoading(true);
                setStatusFilter(event.target.value);
              }}
              className="workspace-field"
            >
              <option value="all">All</option>
              <option value="queued">Queued</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </Field>

          <Field label="Tool name">
            <input
              value={toolName}
              onChange={(event) => {
                setLoading(true);
                setToolName(event.target.value);
              }}
              placeholder="Django, FastAPI, personal-rag"
              className="workspace-field"
            />
          </Field>

          <Field label="Limit">
            <input
              type="number"
              min={1}
              max={200}
              value={limit || ""}
              onChange={(event) => {
                setLoading(true);
                setLimit(Number(event.target.value));
              }}
              className="workspace-field"
            />
          </Field>

          <label className="flex items-center gap-3 self-end workspace-field">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(event) => setAutoRefresh(event.target.checked)}
            />
            Live refresh
          </label>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={refreshJobs}
            disabled={loading}
            className="workspace-button"
          >
            {loading ? "Refreshing..." : "Refresh Jobs"}
          </button>

          {autoRefresh && hasActiveJobs && (
            <span className="text-sm text-neutral-500">
              Live updates are active.
            </span>
          )}
        </div>
      </section>

      {loadError && <StatusMessage tone="error">{loadError}</StatusMessage>}
      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {loading && (
        <StatusMessage tone="info">Loading ingestion jobs…</StatusMessage>
      )}

      <section className="space-y-4">
        {jobs.map((job) => {
          const actionRunning = actionJobId === job.job_id;

          return (
            <article
              key={job.job_id}
              className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-semibold text-white">
                      {job.original_filename || "Unknown document"}
                    </h2>

                    <StatusBadge status={job.status} />
                  </div>

                  <p className="mt-2 text-sm text-neutral-500">
                    Step: {job.current_step || "Not available"}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {job.status === "queued" && (
                    <button
                      type="button"
                      disabled={actionRunning}
                      onClick={() => void cancelJob(job.job_id)}
                      className="rounded-lg border border-yellow-800 px-3 py-1.5 text-xs text-yellow-300 disabled:opacity-40"
                    >
                      {actionRunning ? "Cancelling..." : "Cancel"}
                    </button>
                  )}

                  {(job.status === "failed" || job.status === "cancelled") && (
                    <button
                      type="button"
                      disabled={actionRunning}
                      onClick={() => void retryJob(job.job_id)}
                      className="rounded-lg border border-blue-800 px-3 py-1.5 text-xs text-blue-300 disabled:opacity-40"
                    >
                      {actionRunning ? "Retrying..." : "Retry"}
                    </button>
                  )}
                </div>
              </div>

              <div className="mt-5">
                <ProgressBar progress={job.progress_percent} />
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
                    {job.tool_version || job.version_major || "N/A"}
                  </p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    Attempts
                  </p>

                  <p className="mt-1 text-sm text-neutral-300">
                    {job.attempt_count} / {job.max_attempts}
                  </p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wide text-neutral-500">
                    Index After Ingest
                  </p>

                  <p className="mt-1 text-sm text-neutral-300">
                    {job.index_after_ingest ? "Yes" : "No"}
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
                    {JSON.stringify(job.result, null, 2)}
                  </pre>
                </details>
              )}
            </article>
          );
        })}

        {!loading && !loadError && jobs.length === 0 && (
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-8 text-center text-neutral-400">
            No ingestion jobs found.
          </div>
        )}
      </section>
    </PageFrame>
  );
}
