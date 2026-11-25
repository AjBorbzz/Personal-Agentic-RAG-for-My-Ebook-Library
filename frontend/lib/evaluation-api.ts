import { apiGet, apiRequest, type ApiReadOptions } from "./api";

export type EvaluationRun = {
  evaluation_run_id: string;
  dataset_name: string;
  dataset_version: string;
  status: string;
  summary_metrics: Record<string, unknown> | null;
  error_detail?: string | null;
  comparison?: { status?: string; decision?: string } | null;
};

export type EvaluationSource = {
  document_id?: string | null;
  source_file?: string | null;
  page_start?: number | null;
  page_end?: number | null;
};

export type EvaluationResult = {
  evaluation_result_id: string;
  evaluation_case_id: string;
  metrics: Record<string, unknown>;
  failure_categories: string[];
  passed: boolean;
  human_groundedness: boolean | null;
  human_relevance: boolean | null;
  human_completeness: boolean | null;
  answer: string | null;
  retrieved_sources: EvaluationSource[] | null;
  citations: EvaluationSource[] | null;
  error_detail: string | null;
};

export type EvaluationDashboard = {
  recent_evaluation_runs: EvaluationRun[];
  operational_sample_size: number;
  fallback_rate_recent: number | null;
  weak_source_rate_recent: number | null;
  avg_latency_ms_recent: number | null;
  recent_errors: number;
};

export const evaluationApi = {
  dashboard: (options?: ApiReadOptions) =>
    apiGet<EvaluationDashboard>("/evaluation-dashboard", options),

  run: (id: string, options?: ApiReadOptions) =>
    apiGet<EvaluationRun>(
      `/evaluation-runs/${encodeURIComponent(id)}`,
      options,
    ),

  results: (id: string, options?: ApiReadOptions) =>
    apiGet<EvaluationResult[]>(
      `/evaluation-runs/${encodeURIComponent(id)}/results`,
      options,
    ),

  start: (
    body: {
      dataset_name: string;
      dataset_version: string;
      baseline_run_id?: string;
      top_k: number;
      max_cases: number;
      system_config: { label: string };
    },
    options?: ApiReadOptions,
  ) =>
    apiRequest<EvaluationRun>("/evaluation-runs", {
      ...options,
      method: "POST",
      json: body,
    }),

  review: (
    id: string,
    body: {
      grounded: boolean;
      relevant: boolean;
      complete: boolean;
      notes: string;
    },
    options?: ApiReadOptions,
  ) =>
    apiRequest(`/evaluation-results/${encodeURIComponent(id)}/review`, {
      ...options,
      method: "PATCH",
      json: body,
      responseType: "void",
    }),
};
