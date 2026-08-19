BEGIN;

-- ============================================================
-- Phase 13E.1
-- Personal Skill Profile Data Model
--
-- IMPORTANT:
-- Existing application identities such as skill_id,
-- proficiency_level_id, and document_id are stored as
-- character varying in the current PostgreSQL schema.
--
-- New Phase 13E-owned row identities use native UUID.
-- ============================================================


-- ============================================================
-- 1. PERSONAL SKILL PROFILES
-- ============================================================

CREATE TABLE personal_skill_profiles (
    profile_id UUID PRIMARY KEY,

    profile_name VARCHAR(255) NOT NULL,
    description TEXT,

    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE UNIQUE INDEX uq_personal_skill_profiles_one_default
    ON personal_skill_profiles (is_default)
    WHERE is_default = TRUE;


CREATE INDEX ix_personal_skill_profiles_is_active
    ON personal_skill_profiles (is_active);


-- ============================================================
-- 2. PERSONAL SKILL STATES
-- ============================================================

CREATE TABLE personal_skill_states (
    profile_skill_id UUID PRIMARY KEY,

    profile_id UUID NOT NULL,

    -- Existing Phase 13C canonical identity.
    skill_id VARCHAR NOT NULL,

    -- Existing Phase 13C proficiency identities.
    current_level_id VARCHAR,
    target_level_id VARCHAR,

    confidence NUMERIC(4, 3),

    career_priority INTEGER NOT NULL DEFAULT 3,

    learning_status VARCHAR(32) NOT NULL DEFAULT 'not_started',

    last_assessed_at TIMESTAMPTZ,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_personal_skill_states_profile
        FOREIGN KEY (profile_id)
        REFERENCES personal_skill_profiles(profile_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_personal_skill_states_skill
    FOREIGN KEY (skill_id)
    REFERENCES skills(skill_id),

    CONSTRAINT fk_personal_skill_states_current_level
        FOREIGN KEY (current_level_id)
        REFERENCES proficiency_levels(level_id),

    CONSTRAINT fk_personal_skill_states_target_level
        FOREIGN KEY (target_level_id)
        REFERENCES proficiency_levels(level_id),

    CONSTRAINT uq_personal_skill_states_profile_skill
        UNIQUE (profile_id, skill_id),

    CONSTRAINT ck_personal_skill_states_confidence
        CHECK (
            confidence IS NULL
            OR (
                confidence >= 0
                AND confidence <= 1
            )
        ),

    CONSTRAINT ck_personal_skill_states_career_priority
        CHECK (
            career_priority >= 1
            AND career_priority <= 5
        ),

    CONSTRAINT ck_personal_skill_states_learning_status
        CHECK (
            learning_status IN (
                'not_started',
                'planned',
                'learning',
                'practicing',
                'demonstrated',
                'maintained',
                'paused'
            )
        )
);


CREATE INDEX ix_personal_skill_states_profile_id
    ON personal_skill_states (profile_id);


CREATE INDEX ix_personal_skill_states_skill_id
    ON personal_skill_states (skill_id);


CREATE INDEX ix_personal_skill_states_current_level_id
    ON personal_skill_states (current_level_id);


CREATE INDEX ix_personal_skill_states_target_level_id
    ON personal_skill_states (target_level_id);


CREATE INDEX ix_personal_skill_states_learning_status
    ON personal_skill_states (learning_status);


-- ============================================================
-- 3. PERSONAL SKILL EVIDENCE
-- ============================================================

CREATE TABLE personal_skill_evidence (
    evidence_id UUID PRIMARY KEY,

    profile_skill_id UUID NOT NULL,

    evidence_type VARCHAR(32) NOT NULL,

    title VARCHAR(255) NOT NULL,

    description TEXT,

    evidence_date TIMESTAMPTZ,

    strength INTEGER,

    verification_status VARCHAR(32)
        NOT NULL
        DEFAULT 'unverified',

    source_url TEXT,

    -- Existing Phase 12 document identity.
    source_document_id VARCHAR,

    metadata JSON NOT NULL DEFAULT '{}'::json,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_personal_skill_evidence_skill_state
        FOREIGN KEY (profile_skill_id)
        REFERENCES personal_skill_states(profile_skill_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_personal_skill_evidence_source_document
        FOREIGN KEY (source_document_id)
        REFERENCES documents(document_id)
        ON DELETE SET NULL,

    CONSTRAINT ck_personal_skill_evidence_type
        CHECK (
            evidence_type IN (
                'project',
                'work_experience',
                'certification',
                'course',
                'assessment',
                'repository',
                'exercise',
                'publication',
                'manual'
            )
        ),

    CONSTRAINT ck_personal_skill_evidence_strength
        CHECK (
            strength IS NULL
            OR (
                strength >= 1
                AND strength <= 5
            )
        ),

    CONSTRAINT ck_personal_skill_evidence_verification_status
        CHECK (
            verification_status IN (
                'unverified',
                'reviewed',
                'verified',
                'rejected'
            )
        )
);


CREATE INDEX ix_personal_skill_evidence_profile_skill_id
    ON personal_skill_evidence (profile_skill_id);


CREATE INDEX ix_personal_skill_evidence_verification_status
    ON personal_skill_evidence (verification_status);


CREATE INDEX ix_personal_skill_evidence_source_document_id
    ON personal_skill_evidence (source_document_id);


COMMIT;

