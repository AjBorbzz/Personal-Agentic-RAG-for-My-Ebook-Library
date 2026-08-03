CREATE TABLE IF NOT EXISTS skill_domains (
    domain_id VARCHAR(100) PRIMARY KEY,
    slug VARCHAR(120) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skill_categories (
    category_id VARCHAR(100) PRIMARY KEY,

    domain_id VARCHAR(100)
        NOT NULL
        REFERENCES skill_domains(domain_id)
        ON DELETE CASCADE,

    parent_category_id VARCHAR(100)
        REFERENCES skill_categories(category_id)
        ON DELETE SET NULL,

    slug VARCHAR(120) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_skill_categories_domain_slug
        UNIQUE (domain_id, slug)
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id VARCHAR(100) PRIMARY KEY,

    domain_id VARCHAR(100)
        NOT NULL
        REFERENCES skill_domains(domain_id)
        ON DELETE CASCADE,

    category_id VARCHAR(100)
        REFERENCES skill_categories(category_id)
        ON DELETE SET NULL,

    slug VARCHAR(160) NOT NULL UNIQUE,
    name VARCHAR(240) NOT NULL,
    description TEXT,

    skill_type VARCHAR(50)
        NOT NULL DEFAULT 'concept',

    difficulty_level VARCHAR(30)
        NOT NULL DEFAULT 'foundational',

    tags JSON,

    is_active BOOLEAN
        NOT NULL DEFAULT TRUE,

    is_deprecated BOOLEAN
        NOT NULL DEFAULT FALSE,

    superseded_by_skill_id VARCHAR(100)
        REFERENCES skills(skill_id)
        ON DELETE SET NULL,

    source VARCHAR(50)
        NOT NULL DEFAULT 'manual',

    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skill_aliases (
    alias_id VARCHAR(100) PRIMARY KEY,

    skill_id VARCHAR(100)
        NOT NULL
        REFERENCES skills(skill_id)
        ON DELETE CASCADE,

    alias VARCHAR(240) NOT NULL,
    normalized_alias VARCHAR(240) NOT NULL,

    alias_type VARCHAR(40)
        NOT NULL DEFAULT 'synonym',

    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_skill_aliases_skill_alias
        UNIQUE (skill_id, normalized_alias)
);

CREATE TABLE IF NOT EXISTS skill_relationships (
    relationship_id VARCHAR(100) PRIMARY KEY,

    source_skill_id VARCHAR(100)
        NOT NULL
        REFERENCES skills(skill_id)
        ON DELETE CASCADE,

    target_skill_id VARCHAR(100)
        NOT NULL
        REFERENCES skills(skill_id)
        ON DELETE CASCADE,

    relationship_type VARCHAR(50) NOT NULL,

    strength DOUBLE PRECISION
        NOT NULL DEFAULT 1.0,

    notes TEXT,

    source VARCHAR(50)
        NOT NULL DEFAULT 'manual',

    is_active BOOLEAN
        NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_skill_relationships_edge
        UNIQUE (
            source_skill_id,
            target_skill_id,
            relationship_type
        )
);

CREATE TABLE IF NOT EXISTS proficiency_levels (
    level_id VARCHAR(100) PRIMARY KEY,

    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL UNIQUE,
    level_order INTEGER NOT NULL UNIQUE,

    description TEXT,
    evidence_expectations JSON,

    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_skill_domains_slug
    ON skill_domains(slug);

CREATE INDEX IF NOT EXISTS ix_skill_domains_active
    ON skill_domains(is_active);

CREATE INDEX IF NOT EXISTS ix_skill_categories_domain
    ON skill_categories(domain_id);

CREATE INDEX IF NOT EXISTS ix_skill_categories_parent
    ON skill_categories(parent_category_id);

CREATE INDEX IF NOT EXISTS ix_skills_domain
    ON skills(domain_id);

CREATE INDEX IF NOT EXISTS ix_skills_category
    ON skills(category_id);

CREATE INDEX IF NOT EXISTS ix_skills_name
    ON skills(name);

CREATE INDEX IF NOT EXISTS ix_skills_type
    ON skills(skill_type);

CREATE INDEX IF NOT EXISTS ix_skills_difficulty
    ON skills(difficulty_level);

CREATE INDEX IF NOT EXISTS ix_skills_active
    ON skills(is_active);

CREATE INDEX IF NOT EXISTS ix_skills_deprecated
    ON skills(is_deprecated);

CREATE INDEX IF NOT EXISTS ix_skill_aliases_skill
    ON skill_aliases(skill_id);

CREATE INDEX IF NOT EXISTS ix_skill_aliases_normalized
    ON skill_aliases(normalized_alias);

CREATE INDEX IF NOT EXISTS ix_skill_relationships_source
    ON skill_relationships(source_skill_id);

CREATE INDEX IF NOT EXISTS ix_skill_relationships_target
    ON skill_relationships(target_skill_id);

CREATE INDEX IF NOT EXISTS ix_skill_relationships_type
    ON skill_relationships(relationship_type);