CREATE TABLE IF NOT EXISTS book_curations (
    curation_id VARCHAR(100) PRIMARY KEY,

    document_id VARCHAR(100)
        NOT NULL
        UNIQUE
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    evaluation_status VARCHAR(30)
        NOT NULL
        DEFAULT 'not_evaluated',

    overall_score DOUBLE PRECISION,
    technical_depth_score DOUBLE PRECISION,
    practicality_score DOUBLE PRECISION,
    freshness_score DOUBLE PRECISION,
    authority_score DOUBLE PRECISION,
    clarity_score DOUBLE PRECISION,
    outdated_risk_score DOUBLE PRECISION,

    audience_level VARCHAR(50),
    recommended_role VARCHAR(50),
    library_priority VARCHAR(30),

    curator_summary TEXT,
    unique_value TEXT,

    strengths JSON,
    weaknesses JSON,
    best_for JSON,
    not_recommended_for JSON,
    outdated_topics JSON,

    evaluation_source VARCHAR(30),
    evaluation_model VARCHAR(100),
    evaluation_version INTEGER NOT NULL DEFAULT 1,

    confidence DOUBLE PRECISION,

    metadata_snapshot JSON,
    evaluation_candidate JSON,
    review_notes TEXT,

    evaluated_at TIMESTAMP WITH TIME ZONE,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_book_curations_overall_score
        CHECK (
            overall_score IS NULL
            OR overall_score BETWEEN 0 AND 100
        ),

    CONSTRAINT ck_book_curations_technical_depth_score
        CHECK (
            technical_depth_score IS NULL
            OR technical_depth_score BETWEEN 0 AND 100
        ),

    CONSTRAINT ck_book_curations_practicality_score
        CHECK (
            practicality_score IS NULL
            OR practicality_score BETWEEN 0 AND 100
        ),

    CONSTRAINT ck_book_curations_freshness_score
        CHECK (
            freshness_score IS NULL
            OR freshness_score BETWEEN 0 AND 100
        ),

    CONSTRAINT ck_book_curations_authority_score
        CHECK (
            authority_score IS NULL
            OR authority_score BETWEEN 0 AND 100
        ),

    CONSTRAINT ck_book_curations_clarity_score
        CHECK (
            clarity_score IS NULL
            OR clarity_score BETWEEN 0 AND 100
        ),

    CONSTRAINT ck_book_curations_outdated_risk_score
        CHECK (
            outdated_risk_score IS NULL
            OR outdated_risk_score BETWEEN 0 AND 100
        ),

    CONSTRAINT ck_book_curations_confidence
        CHECK (
            confidence IS NULL
            OR confidence BETWEEN 0 AND 1
        )
);

CREATE INDEX IF NOT EXISTS ix_book_curations_document_id
    ON book_curations(document_id);

CREATE INDEX IF NOT EXISTS ix_book_curations_evaluation_status
    ON book_curations(evaluation_status);

CREATE INDEX IF NOT EXISTS ix_book_curations_overall_score
    ON book_curations(overall_score);

CREATE INDEX IF NOT EXISTS ix_book_curations_audience_level
    ON book_curations(audience_level);

CREATE INDEX IF NOT EXISTS ix_book_curations_recommended_role
    ON book_curations(recommended_role);

CREATE INDEX IF NOT EXISTS ix_book_curations_library_priority
    ON book_curations(library_priority);