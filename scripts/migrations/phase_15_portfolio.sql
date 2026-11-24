-- Phase 15A–15G. Additive migration; manual migrations remain standard until Phase 16.
-- Apply only after inspecting live schema and taking a PostgreSQL backup.
BEGIN;
CREATE TABLE portfolio_projects (
  portfolio_project_id UUID PRIMARY KEY,
  profile_id UUID NOT NULL REFERENCES personal_skill_profiles(profile_id) ON DELETE RESTRICT,
  career_target_id UUID NOT NULL REFERENCES career_targets(career_target_id) ON DELETE RESTRICT,
  title TEXT NOT NULL CHECK (length(trim(title)) > 0),
  slug VARCHAR(160) NOT NULL CHECK (length(trim(slug)) > 0),
  problem_statement TEXT NOT NULL,
  status VARCHAR(24) NOT NULL DEFAULT 'idea'
    CHECK (status IN ('idea','approved','planned','in_progress','blocked','completed','published','archived')),
  scope JSONB NOT NULL DEFAULT '{}'::jsonb,
  architecture JSONB NOT NULL DEFAULT '{}'::jsonb,
  tech_stack JSONB NOT NULL DEFAULT '[]'::jsonb,
  target_skill_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  source_document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  source_mapping_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  blueprint_versions JSONB NOT NULL DEFAULT '[]'::jsonb,
  approved_blueprint_version INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  CONSTRAINT uq_portfolio_projects_profile_slug UNIQUE(profile_id,slug),
  CONSTRAINT ck_portfolio_approved_version CHECK (approved_blueprint_version IS NULL OR approved_blueprint_version > 0)
);
CREATE INDEX ix_portfolio_projects_profile_status ON portfolio_projects (profile_id, status, created_at DESC);
CREATE TABLE portfolio_milestones (
  milestone_id UUID PRIMARY KEY,
  portfolio_project_id UUID NOT NULL REFERENCES portfolio_projects(portfolio_project_id) ON DELETE CASCADE,
  title TEXT NOT NULL CHECK (length(trim(title)) > 0),
  description TEXT NOT NULL DEFAULT '',
  status VARCHAR(16) NOT NULL DEFAULT 'planned'
    CHECK (status IN ('planned','active','blocked','completed','skipped')),
  sequence_order INTEGER NOT NULL CHECK (sequence_order > 0),
  acceptance_criteria JSONB NOT NULL DEFAULT '[]'::jsonb,
  completion_notes TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  CONSTRAINT uq_portfolio_milestone_order UNIQUE(portfolio_project_id,sequence_order)
);
CREATE INDEX ix_portfolio_milestones_project ON portfolio_milestones (portfolio_project_id,sequence_order);
CREATE TABLE portfolio_artifacts (
  artifact_id UUID PRIMARY KEY,
  portfolio_project_id UUID NOT NULL REFERENCES portfolio_projects(portfolio_project_id) ON DELETE CASCADE,
  milestone_id UUID REFERENCES portfolio_milestones(milestone_id) ON DELETE SET NULL,
  artifact_type VARCHAR(32) NOT NULL CHECK (artifact_type IN
    ('repository','architecture','README','test_report','demo','case_study','resume_bullet','interview_story','publication')),
  title TEXT NOT NULL CHECK(length(trim(title)) > 0),
  content TEXT NOT NULL DEFAULT '',
  file_path TEXT,
  source_url TEXT,
  verification_status VARCHAR(16) NOT NULL DEFAULT 'draft' CHECK (verification_status IN
    ('draft','reviewed','verified','published')),
  claim_scope VARCHAR(16) NOT NULL DEFAULT 'planned' CHECK (claim_scope IN
    ('planned','implemented','tested','measured','published')),
  evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
  version INTEGER NOT NULL DEFAULT 1 CHECK(version > 0),
  revision_history JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT ck_portfolio_artifact_claim_evidence CHECK (
    claim_scope = 'planned' OR
    (verification_status IN ('reviewed','verified','published') AND evidence <> '{}'::jsonb)
  ),
  CONSTRAINT ck_portfolio_artifact_published CHECK (
    claim_scope <> 'published' OR (verification_status = 'published' AND NULLIF(trim(source_url), '') IS NOT NULL)
  )
);
CREATE INDEX ix_portfolio_artifacts_project ON portfolio_artifacts (portfolio_project_id, artifact_type,created_at DESC);
COMMIT;