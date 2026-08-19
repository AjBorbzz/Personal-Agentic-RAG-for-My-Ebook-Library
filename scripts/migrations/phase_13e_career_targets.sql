BEGIN;

CREATE TABLE career_targets (
    career_target_id UUID PRIMARY KEY,

    profile_id UUID NOT NULL,

    role_name VARCHAR(255) NOT NULL,
    role_slug VARCHAR(160) NOT NULL,

    description TEXT,

    priority INTEGER NOT NULL,

    status VARCHAR(32) NOT NULL,

    target_date DATE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_career_targets_profile
        FOREIGN KEY (profile_id)
        REFERENCES personal_skill_profiles(profile_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_career_targets_profile_role_slug
        UNIQUE (profile_id, role_slug),

    CONSTRAINT ck_career_targets_priority
        CHECK (
            priority >= 1
            AND priority <= 5
        ),

    CONSTRAINT ck_career_targets_status
        CHECK (
            status IN (
                'exploring',
                'active',
                'paused',
                'achieved'
            )
        )
);


CREATE INDEX ix_career_targets_profile_id
    ON career_targets(profile_id);

CREATE INDEX ix_career_targets_status
    ON career_targets(status);

CREATE INDEX ix_career_targets_priority
    ON career_targets(priority);


CREATE TABLE career_target_skills (
    career_target_skill_id UUID PRIMARY KEY,

    career_target_id UUID NOT NULL,

    skill_id VARCHAR(100) NOT NULL,

    required_level_id VARCHAR(100) NOT NULL,

    importance_weight INTEGER NOT NULL,

    is_required BOOLEAN NOT NULL,

    rationale TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_career_target_skills_target
        FOREIGN KEY (career_target_id)
        REFERENCES career_targets(career_target_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_career_target_skills_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(skill_id),

    CONSTRAINT fk_career_target_skills_level
        FOREIGN KEY (required_level_id)
        REFERENCES proficiency_levels(level_id),

    CONSTRAINT uq_career_target_skills_target_skill
        UNIQUE (
            career_target_id,
            skill_id
        ),

    CONSTRAINT ck_career_target_skills_importance
        CHECK (
            importance_weight >= 1
            AND importance_weight <= 5
        )
);


CREATE INDEX ix_career_target_skills_target_id
    ON career_target_skills(career_target_id);

CREATE INDEX ix_career_target_skills_skill_id
    ON career_target_skills(skill_id);

CREATE INDEX ix_career_target_skills_required_level_id
    ON career_target_skills(required_level_id);

CREATE INDEX ix_career_target_skills_is_required
    ON career_target_skills(is_required);

COMMIT;