"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { PageFrame, PageHeader } from "@/components/PageHeader";
import { Field, StatusMessage } from "@/components/WorkspaceUI";
import {
  evaluationApi,
  type EvaluationDashboard,
  type EvaluationResult,
  type EvaluationRun,
} from "@/lib/evaluation-api";
import {
  EvaluationResults,
  formatRate,
  formatRunStatus,
} from "./EvaluationResults";

type DashboardState = {
  revision: number;
  data: EvaluationDashboard | null;
  error?: string;
};

type ResultsState = {
  id: string;
  revision: number;
} & (
  | { run: EvaluationRun; results: EvaluationResult[]; error?: undefined }
  | { run?: undefined; results?: undefined; error: string }
);

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="workspace-panel min-w-0">
      <dt className="text-sm text-neutral-400">{label}</dt>
      <dd className="mt-2 break-words text-xl font-semibold tabular-nums text-neutral-100">
        {value}
      </dd>
    </div>
  );
}

export default function EvaluationPage() {
  const [dashboard, setDashboard] = useState<DashboardState | null>(null);
  const [dashboardRevision, setDashboardRevision] = useState(0);
  const [selection, setSelection] = useState({ id: "", revision: 0 });
  const [resultsState, setResultsState] = useState<ResultsState | null>(null);
  const [dataset, setDataset] = useState("smoke");
  const [version, setVersion] = useState("v1");
  const [baseline, setBaseline] = useState("");
  const [notes, setNotes] = useState(
    "Reviewed against retrieved source passages.",
  );
  const [action, setAction] = useState<
    { kind: "create" } | { kind: "review"; resultId: string } | null
  >(null);
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const actionRequest = useRef<AbortController | null>(null);

  const { id: selectedId, revision: resultsRevision } = selection;
  const dashboardLoading = dashboard?.revision !== dashboardRevision;
  const activeResults =
    resultsState?.id === selectedId && resultsState.revision === resultsRevision
      ? resultsState
      : null;

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    evaluationApi.dashboard({ signal }).then(
      (data) => {
        if (!signal.aborted)
          setDashboard({ revision: dashboardRevision, data });
      },
      (error: unknown) => {
        if (!signal.aborted) {
          setDashboard((previous) => ({
            revision: dashboardRevision,
            data: previous?.data ?? null,
            error: errorMessage(
              error,
              "Could not load the evaluation dashboard.",
            ),
          }));
        }
      },
    );

    return () => controller.abort();
  }, [dashboardRevision]);

  useEffect(() => {
    if (!selectedId) return;

    const controller = new AbortController();
    const { signal } = controller;

    Promise.all([
      evaluationApi.run(selectedId, { signal }),
      evaluationApi.results(selectedId, { signal }),
    ]).then(
      ([run, results]) => {
        if (!signal.aborted)
          setResultsState({
            id: selectedId,
            revision: resultsRevision,
            run,
            results,
          });
      },
      (error: unknown) => {
        if (!signal.aborted) {
          setResultsState({
            id: selectedId,
            revision: resultsRevision,
            error: errorMessage(error, "Could not load the selected run."),
          });
        }
      },
    );

    return () => controller.abort();
  }, [selectedId, resultsRevision]);

  useEffect(() => () => actionRequest.current?.abort(), []);

  async function runAction(
    name: NonNullable<typeof action>,
    request: (signal: AbortSignal) => Promise<void>,
  ) {
    if (actionRequest.current) return;

    const controller = new AbortController();
    actionRequest.current = controller;
    setAction(name);
    setActionError("");
    setNotice("");

    try {
      await request(controller.signal);
    } catch (error) {
      if (!controller.signal.aborted) {
        setActionError(errorMessage(error, "The evaluation request failed."));
      }
    } finally {
      if (actionRequest.current === controller) {
        actionRequest.current = null;
        if (!controller.signal.aborted) setAction(null);
      }
    }
  }

  function createRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!dataset.trim() || !version.trim()) return;

    void runAction({ kind: "create" }, async (signal) => {
      const run = await evaluationApi.start(
        {
          dataset_name: dataset.trim(),
          dataset_version: version.trim(),
          top_k: 5,
          max_cases: 20,
          ...(baseline.trim() ? { baseline_run_id: baseline.trim() } : {}),
          system_config: { label: "manual-ui-baseline" },
        },
        { signal },
      );

      if (signal.aborted) return;
      setSelection(({ revision }) => ({
        id: run.evaluation_run_id,
        revision: revision + 1,
      }));
      setDashboardRevision((revision) => revision + 1);
      if (run.status === "failed") {
        setActionError(
          "The evaluation run failed. See the run results for details.",
        );
      } else {
        setNotice("Evaluation run saved.");
      }
    });
  }

  function review(resultId: string, approved: boolean) {
    if (!activeResults?.run || !notes.trim()) return;

    void runAction({ kind: "review", resultId }, async (signal) => {
      await evaluationApi.review(
        resultId,
        {
          grounded: approved,
          relevant: approved,
          complete: approved,
          notes: notes.trim(),
        },
        { signal },
      );

      if (signal.aborted) return;
      setSelection((current) => ({
        ...current,
        revision: current.revision + 1,
      }));
      setDashboardRevision((revision) => revision + 1);
      setNotice("Case review saved.");
    });
  }

  const data = dashboard?.data;
  const runs = data?.recent_evaluation_runs ?? [];

  return (
    <PageFrame>
      <PageHeader
        eyebrow="Retrieval"
        title="RAG Evaluation"
        description="Benchmark ebook retrieval and verify the citations behind generated answers."
        back={{ label: "Workspace", href: "/" }}
      />

      <section
        className="space-y-3"
        aria-labelledby="evaluation-metrics"
        aria-busy={dashboardLoading}
      >
        <h2 id="evaluation-metrics" className="text-xl font-semibold">
          Recent retrieval activity
        </h2>
        {dashboardLoading && !data && (
          <StatusMessage tone="info">Loading retrieval activity…</StatusMessage>
        )}
        {!dashboardLoading && dashboard?.error && (
          <StatusMessage tone="error">
            <p className="break-words">{dashboard.error}</p>
            <button
              type="button"
              className="workspace-button workspace-button--secondary mt-3"
              onClick={() => setDashboardRevision((revision) => revision + 1)}
            >
              Retry dashboard
            </button>
          </StatusMessage>
        )}
        {data && (
          <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Metric
              label="RAG traces sampled"
              value={data.operational_sample_size}
            />
            <Metric
              label="Fallback rate"
              value={formatRate(data.fallback_rate_recent)}
            />
            <Metric
              label="Weak-source rate"
              value={formatRate(data.weak_source_rate_recent)}
            />
            <Metric
              label="Mean latency"
              value={
                data.avg_latency_ms_recent == null
                  ? "Not measured"
                  : `${data.avg_latency_ms_recent.toLocaleString("en")} ms`
              }
            />
          </dl>
        )}
      </section>

      <section
        className="workspace-panel space-y-4"
        aria-labelledby="evaluate-dataset"
      >
        <h2 id="evaluate-dataset" className="text-xl font-semibold">
          Run a versioned dataset
        </h2>
        <form
          className="grid items-end gap-4 sm:grid-cols-2 lg:grid-cols-4"
          onSubmit={createRun}
        >
          <Field label="Dataset">
            <input
              className="workspace-field"
              value={dataset}
              onChange={(event) => setDataset(event.target.value)}
              required
            />
          </Field>
          <Field label="Version">
            <input
              className="workspace-field"
              value={version}
              onChange={(event) => setVersion(event.target.value)}
              required
            />
          </Field>
          <Field label="Baseline run ID (optional)">
            <input
              className="workspace-field"
              value={baseline}
              onChange={(event) => setBaseline(event.target.value)}
            />
          </Field>
          <button
            type="submit"
            className="workspace-button justify-center"
            disabled={Boolean(action) || !dataset.trim() || !version.trim()}
          >
            {action?.kind === "create" ? "Evaluating…" : "Run evaluation"}
          </button>
        </form>
      </section>

      {actionError && <StatusMessage tone="error">{actionError}</StatusMessage>}
      {notice && <StatusMessage tone="success">{notice}</StatusMessage>}

      <section
        className="workspace-panel space-y-3"
        aria-labelledby="recent-runs"
        aria-busy={dashboardLoading}
      >
        <h2 id="recent-runs" className="text-xl font-semibold">
          Recent runs
        </h2>
        {data && !runs.length && (
          <p className="text-neutral-400">
            No evaluation runs yet. Run a dataset to get started.
          </p>
        )}
        {!data && (
          <p className="text-neutral-400">
            {dashboardLoading
              ? "Loading recent runs…"
              : "Recent runs are unavailable."}
          </p>
        )}
        {runs.length > 0 && (
          <ul className="space-y-2">
            {runs.map((run) => (
              <li key={run.evaluation_run_id}>
                <button
                  type="button"
                  className="w-full min-w-0 rounded-lg border border-neutral-800 bg-neutral-950 p-3 text-left hover:border-neutral-500 aria-pressed:border-neutral-500 disabled:opacity-65"
                  aria-pressed={selectedId === run.evaluation_run_id}
                  disabled={Boolean(action)}
                  onClick={() => {
                    setActionError("");
                    setNotice("");
                    setSelection((current) =>
                      current.id === run.evaluation_run_id
                        ? current
                        : {
                            id: run.evaluation_run_id,
                            revision: current.revision + 1,
                          },
                    );
                  }}
                >
                  <span className="flex flex-wrap items-center gap-x-4 gap-y-1">
                    <span className="min-w-0 break-words font-medium">
                      {run.dataset_name} / {run.dataset_version}
                    </span>
                    <span className="workspace-badge">
                      {formatRunStatus(run.status)}
                    </span>
                    <span className="text-sm text-neutral-400">
                      Recall@K{" "}
                      {formatRate(run.summary_metrics?.avg_recall_at_k)}
                    </span>
                  </span>
                  <span className="mt-2 block break-all font-mono text-xs text-neutral-400">
                    {run.evaluation_run_id}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {selectedId && !activeResults && (
        <StatusMessage tone="info">Loading run results…</StatusMessage>
      )}
      {activeResults?.error && (
        <StatusMessage tone="error">
          <p className="break-words">{activeResults.error}</p>
          <button
            type="button"
            className="workspace-button workspace-button--secondary mt-3"
            onClick={() =>
              setSelection((current) => ({
                ...current,
                revision: current.revision + 1,
              }))
            }
          >
            Retry run results
          </button>
        </StatusMessage>
      )}
      {activeResults?.run && (
        <EvaluationResults
          run={activeResults.run}
          results={activeResults.results}
          notes={notes}
          onNotesChange={setNotes}
          onReview={review}
          disabled={Boolean(action)}
          reviewingId={action?.kind === "review" ? action.resultId : undefined}
        />
      )}
    </PageFrame>
  );
}
