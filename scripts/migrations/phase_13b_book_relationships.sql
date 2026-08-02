CREATE TABLE IF NOT EXISTS book_relationships (
    relationship_id VARCHAR(100) PRIMARY KEY,
    pair_key VARCHAR(250) NOT NULL UNIQUE,

    document_a_id VARCHAR(100)
        NOT NULL
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    document_b_id VARCHAR(100)
        NOT NULL
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    relationship_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',

    exact_hash_match BOOLEAN NOT NULL DEFAULT FALSE,
    isbn_match BOOLEAN NOT NULL DEFAULT FALSE,

    title_similarity DOUBLE PRECISION,
    author_similarity DOUBLE PRECISION,
    metadata_overlap_score DOUBLE PRECISION,
    content_overlap_score DOUBLE PRECISION,

    confidence DOUBLE PRECISION NOT NULL,

    reasons JSON,
    document_a_snapshot JSON,
    document_b_snapshot JSON,

    recommended_primary_document_id VARCHAR(100),
    recommended_superseded_document_id VARCHAR(100),
    recommended_action VARCHAR(100),

    detector_version INTEGER NOT NULL DEFAULT 1,

    review_notes TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_book_relationships_pair_key
    ON book_relationships(pair_key);

CREATE INDEX IF NOT EXISTS ix_book_relationships_document_a_id
    ON book_relationships(document_a_id);

CREATE INDEX IF NOT EXISTS ix_book_relationships_document_b_id
    ON book_relationships(document_b_id);

CREATE INDEX IF NOT EXISTS ix_book_relationships_relationship_type
    ON book_relationships(relationship_type);

CREATE INDEX IF NOT EXISTS ix_book_relationships_status
    ON book_relationships(status);

CREATE INDEX IF NOT EXISTS ix_book_relationships_confidence
    ON book_relationships(confidence);