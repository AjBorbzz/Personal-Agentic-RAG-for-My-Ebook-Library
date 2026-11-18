-- Phase 13F: additive manual migration. PostgreSQL 13E + 13C/13D must already exist.
-- Back up the live database before applying. Execute once using psql ON_ERROR_STOP.
BEGIN;

CREATE TABLE IF NOT EXISTS recommendation_runs (
    recommendation_run_id UUID PRIMARY KEY,
    profile_id UUID NOT NULL REFERENCES personal_skill_profiles(profile_id) ON DELETE CASCADE,
    career_target_id UUID NULL REFERENCES career_targets(career_target_id) ON DELETE SET NULL,
    rule_version VARCHAR(40) NOT NULL,
    input_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(16) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed')),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    error_detail TEXT NULL
);
CREATE INDEX IF NOT EXISTS ix_recommendation_runs_profile_date
    ON recommendation_runs(profile_id, generated_at DESC);

CREATE TABLE IF NOT EXISTS skill_recommendations (
    recommendation_id UUID PRIMARY KEY,
    recommendation_run_id UUID NOT NULL
        REFERENCES recommendation_runs(recommendation_run_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) NOT NULL REFERENCES skills(skill_id),
    recommendation_type VARCHAR(32) NOT NULL
        CHECK (recommendation_type IN ('prerequisite', 'book', 'project', 'evidence', 'review', 'learning_path')),
    priority_score NUMERIC(7,2) NOT NULL CHECK (priority_score BETWEEN 0 AND 100),
    score_components JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_mapping_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommended_document_id VARCHAR(100) NULL REFERENCES documents(document_id),
    title TEXT NOT NULL,
    explanation TEXT NOT NULL,
    decision_status VARCHAR(16) NOT NULL DEFAULT 'new'
        CHECK (decision_status IN ('new', 'accepted', 'deferred', 'dismissed', 'completed')),
    decision_notes TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_skill_recommendations_run_priority
    ON skill_recommendations(recommendation_run_id, priority_score DESC, skill_id);
CREATE INDEX IF NOT EXISTS ix_skill_recommendations_skill
    ON skill_recommendations(skill_id);

CREATE TABLE IF NOT EXISTS reading_queue_items (
    reading_queue_item_id UUID PRIMARY KEY,
    profile_id UUID NOT NULL REFERENCES personal_skill_profiles(profile_id) ON DELETE CASCADE,
    document_id VARCHAR(100) NULL REFERENCES documents(document_id),
    skill_id VARCHAR(100) NULL REFERENCES skills(skill_id),
    recommendation_id UUID NULL REFERENCES skill_recommendations(recommendation_id) ON DELETE SET NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'active', 'paused', 'completed', 'removed')),
    priority SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    planned_start DATE NULL,
    target_finish DATE NULL,
    progress_percent SMALLINT NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100),
    notes TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_reading_queue_has_target
        CHECK (recommendation_id IS NOT NULL OR document_id IS NOT NULL OR skill_id IS NOT NULL),
    CONSTRAINT ck_reading_queue_date_order
        CHECK (planned_start IS NULL OR target_finish IS NULL OR target_finish >= planned_start)
);
CREATE INDEX IF NOT EXISTS ix_reading_queue_profile_status
    ON reading_queue_items(profile_id, status, priority);
COMMIT;