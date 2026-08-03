CREATE TABLE IF NOT EXISTS book_skill_mappings (
    mapping_id VARCHAR(100) PRIMARY KEY,

    document_id VARCHAR(100)
        NOT NULL
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    skill_id VARCHAR(100)
        NOT NULL
        REFERENCES skills(skill_id)
        ON DELETE CASCADE,

    mapping_status VARCHAR(30)
        NOT NULL DEFAULT 'pending',

    coverage_level VARCHAR(40),

    is_primary_skill BOOLEAN
        NOT NULL DEFAULT FALSE,

    relevance_score DOUBLE PRECISION,
    coverage_score DOUBLE PRECISION,
    depth_score DOUBLE PRECISION,
    practicality_score DOUBLE PRECISION,

    confidence DOUBLE PRECISION,

    recommended_entry_level_id VARCHAR(100)
        REFERENCES proficiency_levels(level_id)
        ON DELETE SET NULL,

    recommended_exit_level_id VARCHAR(100)
        REFERENCES proficiency_levels(level_id)
        ON DELETE SET NULL,

    coverage_summary TEXT,

    learning_outcomes JSON,
    covered_topics JSON,
    limitations JSON,

    mapping_source VARCHAR(50)
        NOT NULL DEFAULT 'manual',

    mapping_model VARCHAR(200),

    mapping_version INTEGER
        NOT NULL DEFAULT 1,

    candidate_payload JSON,
    candidate_error TEXT,

    candidate_generated_at
        TIMESTAMP WITH TIME ZONE,

    review_notes TEXT,

    reviewed_at
        TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_book_skill_mappings_document_skill
        UNIQUE (document_id, skill_id),

    CONSTRAINT ck_book_skill_mapping_relevance
        CHECK (
            relevance_score IS NULL
            OR (
                relevance_score >= 0
                AND relevance_score <= 100
            )
        ),

    CONSTRAINT ck_book_skill_mapping_coverage
        CHECK (
            coverage_score IS NULL
            OR (
                coverage_score >= 0
                AND coverage_score <= 100
            )
        ),

    CONSTRAINT ck_book_skill_mapping_depth
        CHECK (
            depth_score IS NULL
            OR (
                depth_score >= 0
                AND depth_score <= 100
            )
        ),

    CONSTRAINT ck_book_skill_mapping_practicality
        CHECK (
            practicality_score IS NULL
            OR (
                practicality_score >= 0
                AND practicality_score <= 100
            )
        ),

    CONSTRAINT ck_book_skill_mapping_confidence
        CHECK (
            confidence IS NULL
            OR (
                confidence >= 0
                AND confidence <= 1
            )
        )
);

CREATE TABLE IF NOT EXISTS book_skill_evidence (
    evidence_id VARCHAR(100) PRIMARY KEY,

    mapping_id VARCHAR(100)
        NOT NULL
        REFERENCES book_skill_mappings(mapping_id)
        ON DELETE CASCADE,

    evidence_type VARCHAR(40) NOT NULL,

    chapter_title VARCHAR(500),
    section_title VARCHAR(500),

    page_start INTEGER,
    page_end INTEGER,

    chunk_id VARCHAR(200),

    excerpt TEXT,
    source_locator JSON,

    confidence DOUBLE PRECISION,

    display_order INTEGER
        NOT NULL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_book_skill_evidence_confidence
        CHECK (
            confidence IS NULL
            OR (
                confidence >= 0
                AND confidence <= 1
            )
        ),

    CONSTRAINT ck_book_skill_evidence_page_start
        CHECK (
            page_start IS NULL
            OR page_start >= 1
        ),

    CONSTRAINT ck_book_skill_evidence_page_end
        CHECK (
            page_end IS NULL
            OR page_end >= 1
        ),

    CONSTRAINT ck_book_skill_evidence_page_range
        CHECK (
            page_end IS NULL
            OR page_start IS NULL
            OR page_end >= page_start
        )
);

CREATE INDEX IF NOT EXISTS
    ix_book_skill_mappings_document
    ON book_skill_mappings(document_id);

CREATE INDEX IF NOT EXISTS
    ix_book_skill_mappings_skill
    ON book_skill_mappings(skill_id);

CREATE INDEX IF NOT EXISTS
    ix_book_skill_mappings_status
    ON book_skill_mappings(mapping_status);

CREATE INDEX IF NOT EXISTS
    ix_book_skill_mappings_coverage_level
    ON book_skill_mappings(coverage_level);

CREATE INDEX IF NOT EXISTS
    ix_book_skill_mappings_primary
    ON book_skill_mappings(is_primary_skill);

CREATE INDEX IF NOT EXISTS
    ix_book_skill_mappings_source
    ON book_skill_mappings(mapping_source);

CREATE INDEX IF NOT EXISTS
    ix_book_skill_mappings_entry_level
    ON book_skill_mappings(
        recommended_entry_level_id
    );

CREATE INDEX IF NOT EXISTS
    ix_book_skill_mappings_exit_level
    ON book_skill_mappings(
        recommended_exit_level_id
    );

CREATE INDEX IF NOT EXISTS
    ix_book_skill_evidence_mapping
    ON book_skill_evidence(mapping_id);

CREATE INDEX IF NOT EXISTS
    ix_book_skill_evidence_type
    ON book_skill_evidence(evidence_type);

CREATE INDEX IF NOT EXISTS
    ix_book_skill_evidence_chunk
    ON book_skill_evidence(chunk_id);