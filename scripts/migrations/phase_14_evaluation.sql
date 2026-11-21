-- Phase 14 (14A-14G). Apply once after taking a verified backup.
-- Manual migrations remain the policy until Phase 16. No existing tables are altered.
BEGIN;
CREATE TABLE IF NOT EXISTS evaluation_cases (
  evaluation_case_id UUID PRIMARY KEY,
  case_id VARCHAR(160) NOT NULL,
  dataset_name VARCHAR(120) NOT NULL,
  dataset_version VARCHAR(80) NOT NULL,
  question TEXT NOT NULL,
  expected_intent VARCHAR(120),
  expected_domains JSONB NOT NULL DEFAULT '[]'::jsonb,
  expected_document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  expected_page_ranges JSONB NOT NULL DEFAULT '[]'::jsonb,
  expected_concepts JSONB NOT NULL DEFAULT '[]'::jsonb,
  forbidden_document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  request_filters JSONB NOT NULL DEFAULT '{}'::jsonb,
  expected_refusal BOOLEAN NOT NULL DEFAULT FALSE,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_evaluation_case_version UNIQUE (dataset_name, dataset_version, case_id)
);
CREATE INDEX IF NOT EXISTS ix_evaluation_case_dataset
  ON evaluation_cases (dataset_name, dataset_version, is_active);

CREATE TABLE IF NOT EXISTS evaluation_runs (
  evaluation_run_id UUID PRIMARY KEY,
  dataset_name VARCHAR(120) NOT NULL,
  dataset_version VARCHAR(80) NOT NULL,
  system_config JSONB NOT NULL DEFAULT '{}'::jsonb,
  status VARCHAR(32) NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  summary_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
  baseline_run_id UUID REFERENCES evaluation_runs(evaluation_run_id) ON DELETE SET NULL,
  error_detail TEXT,
  CONSTRAINT ck_eval_run_status CHECK (status IN ('queued','running','completed','failed','cancelled'))
);
CREATE INDEX IF NOT EXISTS ix_eval_runs_dataset_started
  ON evaluation_runs (dataset_name, dataset_version, started_at DESC);

CREATE TABLE IF NOT EXISTS evaluation_results (
  evaluation_result_id UUID PRIMARY KEY,
  evaluation_run_id UUID NOT NULL REFERENCES evaluation_runs(evaluation_run_id) ON DELETE CASCADE,
  evaluation_case_id UUID NOT NULL REFERENCES evaluation_cases(evaluation_case_id) ON DELETE RESTRICT,
  retrieved_sources JSONB NOT NULL DEFAULT '[]'::jsonb,
  answer TEXT,
  citations JSONB NOT NULL DEFAULT '[]'::jsonb,
  metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
  passed BOOLEAN NOT NULL DEFAULT FALSE,
  failure_categories JSONB NOT NULL DEFAULT '[]'::jsonb,
  human_groundedness BOOLEAN,
  human_relevance BOOLEAN,
  human_completeness BOOLEAN,
  human_notes TEXT,
  latency_ms INTEGER NOT NULL DEFAULT 0,
  error_detail TEXT,
  CONSTRAINT uq_evaluation_run_case UNIQUE (evaluation_run_id, evaluation_case_id),
  CONSTRAINT ck_eval_result_latency CHECK (latency_ms >= 0)
);
CREATE INDEX IF NOT EXISTS ix_eval_result_run ON evaluation_results (evaluation_run_id);

CREATE TABLE IF NOT EXISTS rag_run_history (
  rag_run_id UUID PRIMARY KEY,
  request_type VARCHAR(100) NOT NULL,
  question TEXT,
  request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  intent VARCHAR(120),
  strategy VARCHAR(120),
  domains JSONB NOT NULL DEFAULT '[]'::jsonb,
  rewritten_queries JSONB NOT NULL DEFAULT '[]'::jsonb,
  attempts JSONB NOT NULL DEFAULT '[]'::jsonb,
  retrieved_sources JSONB NOT NULL DEFAULT '[]'::jsonb,
  answer TEXT,
  citations JSONB NOT NULL DEFAULT '[]'::jsonb,
  fallback_used BOOLEAN,
  weak_source BOOLEAN,
  status_code INTEGER,
  latency_ms INTEGER NOT NULL DEFAULT 0,
  error_detail TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT ck_rag_run_latency CHECK (latency_ms >= 0)
);
CREATE INDEX IF NOT EXISTS ix_rag_run_history_created
  ON rag_run_history (created_at DESC);
COMMIT;