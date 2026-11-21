"use client";

import { useCallback, useEffect, useState } from "react";

type Run = {
  evaluation_run_id: string;
  dataset_name: string;
  dataset_version: string;
  status: string;
  summary_metrics: Record<string, unknown>;
  comparison?: { blocked?: boolean; decision?: string; delta?: Record<string, number> } | null;
};
type Result = {
  evaluation_result_id: string;
  evaluation_case_id: string;
  metrics: Record<string, unknown>;
  failure_categories: string[];
  passed: boolean;
  human_groundedness: boolean | null;
  human_relevance: boolean | null;
  human_completeness: boolean | null;
  answer: string | null;
  retrieved_sources: Array<{ document_id?: string | null; page_start?: number | null; page_end?: number | null }>;
  citations: Array<{ document_id?: string | null; page_start?: number | null; page_end?: number | null }>;
  error_detail: string | null;
};
type Dashboard = {
  recent_evaluation_runs: Run[];
  operational_sample_size: number;
  fallback_rate_recent: number | null;
  weak_source_rate_recent: number | null;
  avg_latency_ms_recent: number | null;
  recent_errors: number;
};
const API = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { cache: "no-store", ...init });
  const text = await response.text();
  const parsed: unknown = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${JSON.stringify(parsed).slice(0, 500)}`);
  }
  return parsed as T;
}

function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
      <div className="text-xs text-neutral-400">{label}</div>
      <div className="mt-2 text-lg font-semibold text-neutral-100">{value == null ? "Not measured" : String(value)}</div>
    </div>
  );
}

export default function EvaluationPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [dataset, setDataset] = useState("smoke");
  const [version, setVersion] = useState("v1");
  const [baseline, setBaseline] = useState("");
  const [selected, setSelected] = useState<Run | null>(null);
  const [results, setResults] = useState<Result[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notes, setNotes] = useState("Reviewed against retrieved source passages.");

  const reload = useCallback(async () => {
    setDashboard(await api<Dashboard>("/evaluation-dashboard"));
  }, []);
  useEffect(() => { reload().catch((e: unknown) => setError(String(e))); }, [reload]);

  async function createRun() {
    setBusy(true); setError("");
    try {
      const run = await api<Run>("/evaluation-runs", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_name: dataset, dataset_version: version, top_k: 5, max_cases: 20,
          ...(baseline ? { baseline_run_id: baseline } : {}),
          system_config: { label: "manual-ui-baseline" },
        }),
      });
      setSelected(run);
      setResults(await api<Result[]>(`/evaluation-runs/${run.evaluation_run_id}/results`));
      await reload();
    } catch (e: unknown) { setError(String(e)); }
    finally { setBusy(false); }
  }

  async function viewRun(run: Run) {
    setBusy(true); setError("");
    try {
      setSelected(run);
      setResults(await api<Result[]>(`/evaluation-runs/${run.evaluation_run_id}/results`));
    } catch (e: unknown) { setError(String(e)); }
    finally { setBusy(false); }
  }

  async function review(resultId: string, approved: boolean) {
    setBusy(true); setError("");
    try {
      await api(`/evaluation-results/${resultId}/review`, {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grounded: approved, relevant: approved,
          complete: approved, notes }),
      });
      if (selected) {
        const run = await api<Run>(`/evaluation-runs/${selected.evaluation_run_id}`);
        setSelected(run);
        setResults(await api<Result[]>(`/evaluation-runs/${run.evaluation_run_id}/results`));
      }
      await reload();
    } catch (e: unknown) { setError(String(e)); }
    finally { setBusy(false); }
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8 text-neutral-100">
      <header>
        <h1 className="text-2xl font-semibold">RAG Evaluation</h1>
        <p className="mt-2 text-sm text-neutral-400">Phase 14 — dataset, retrieval metrics, human-reviewed citations, and operational traces.</p>
      </header>
      {error && <div role="alert" className="rounded-2xl border border-red-900 bg-neutral-900 p-4 text-red-300">{error}</div>}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-4">
        <Metric label="RAG traces sampled" value={dashboard?.operational_sample_size} />
        <Metric label="Fallback rate" value={dashboard?.fallback_rate_recent} />
        <Metric label="Weak-source rate" value={dashboard?.weak_source_rate_recent} />
        <Metric label="Mean latency (ms)" value={dashboard?.avg_latency_ms_recent} />
      </section>
      <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-3 text-lg font-semibold">Run a versioned dataset</h2>
        <div className="grid gap-3 md:grid-cols-4">
          <label className="text-sm">Dataset
            <input value={dataset} onChange={e => setDataset(e.target.value)} className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" />
          </label>
          <label className="text-sm">Version
            <input value={version} onChange={e => setVersion(e.target.value)} className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" />
          </label>
          <label className="text-sm">Baseline run ID (optional)
            <input value={baseline} onChange={e => setBaseline(e.target.value)} className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" />
          </label>
          <button disabled={busy || !dataset || !version} onClick={createRun} className="self-end rounded-lg bg-white p-2 text-neutral-950 disabled:opacity-50">
            {busy ? "Working" : "Evaluate"}
          </button>
        </div>
      </section>
      <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-3 text-lg font-semibold">Recent runs</h2>
        <div className="space-y-2">
          {(dashboard?.recent_evaluation_runs ?? []).map(run => (
            <button key={run.evaluation_run_id} onClick={() => viewRun(run)} disabled={busy}
              className="block w-full rounded-xl border border-neutral-800 bg-neutral-950 p-3 text-left text-sm hover:border-neutral-600">
              <span className="font-medium">{run.dataset_name} / {run.dataset_version}</span>
              <span className="ml-3 text-neutral-400">{run.status}</span>
              <span className="ml-3 text-neutral-400">Recall@K: {String(run.summary_metrics?.avg_recall_at_k ?? "N/A")}</span>
              {run.comparison && <span className="ml-3 text-amber-300">{run.comparison.decision}</span>}
              <span className="mt-1 block break-all text-xs text-neutral-500">{run.evaluation_run_id}</span>
            </button>
          ))}
        </div>
      </section>
      {selected && (
        <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
          <h2 className="text-lg font-semibold">Run detail</h2>
          <p className="mb-3 break-all text-xs text-neutral-400">{selected.evaluation_run_id}</p>
          <p className="mb-3 text-sm text-neutral-300">Approval status: {selected.comparison?.decision || "No baseline; establish review baseline"}</p>
          <label className="mb-3 block text-sm">Review notes
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2}
              className="mt-1 w-full rounded-lg border border-neutral-700 bg-neutral-950 p-2" />
          </label>
          {results.map(item => (
            <article key={item.evaluation_result_id} className="mb-3 space-y-2 rounded-xl border border-neutral-800 bg-neutral-950 p-3">
              <p className="break-all text-xs text-neutral-500">Case: {item.evaluation_case_id}</p>
              <p className="text-sm">Failures: {item.failure_categories.join(", ") || "None detected"}</p>
              <p className="text-sm text-neutral-300">Answer: {item.answer?.slice(0, 1000) || "No answer"}</p>
              <pre className="overflow-x-auto text-xs text-neutral-400">{JSON.stringify(item.metrics, null, 2)}</pre>
              <details className="text-xs text-neutral-400">
                <summary>Retrieved documents and cited pages</summary>
                {[...(item.retrieved_sources ?? []), ...(item.citations ?? [])].map((s, i) => (
                  <p key={i} className="mt-1">
                    {s.document_id ? <a className="underline" href={`/documents/${encodeURIComponent(s.document_id)}`}>{s.document_id}</a> : "Unknown document"}
                    {" — pages "}{s.page_start ?? "?"}{"–"}{s.page_end ?? "?"}
                  </p>
                ))}
              </details>
              {item.error_detail && <p className="text-sm text-red-300">{item.error_detail}</p>}
              <div className="flex gap-2">
                <button disabled={busy || !notes.trim()} onClick={() => review(item.evaluation_result_id, true)}
                  className="rounded-lg border border-neutral-700 px-3 py-2 text-sm">Approve groundedness/relevance/completeness</button>
                <button disabled={busy || !notes.trim()} onClick={() => review(item.evaluation_result_id, false)}
                  className="rounded-lg border border-neutral-700 px-3 py-2 text-sm">Reject</button>
                <span className="text-sm text-neutral-400">{item.passed ? "PASS" : "PENDING/FAIL"}</span>
              </div>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}