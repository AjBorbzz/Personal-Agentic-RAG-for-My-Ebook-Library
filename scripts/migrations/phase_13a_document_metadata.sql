ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS subtitle VARCHAR(500);

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS publisher VARCHAR(300);

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS edition VARCHAR(100);

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS isbn_10 VARCHAR(20);

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS isbn_13 VARCHAR(20);

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS language VARCHAR(50);

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS description TEXT;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS difficulty_level VARCHAR(50);

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS topics JSON;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS technologies JSON;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS tags JSON;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS prerequisite_skills JSON;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS metadata_source VARCHAR(50);

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS metadata_confidence DOUBLE PRECISION;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS metadata_reviewed BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_documents_isbn_10
    ON documents (isbn_10);

CREATE INDEX IF NOT EXISTS ix_documents_isbn_13
    ON documents (isbn_13);

CREATE INDEX IF NOT EXISTS ix_documents_difficulty_level
    ON documents (difficulty_level);

CREATE INDEX IF NOT EXISTS ix_documents_metadata_reviewed
    ON documents (metadata_reviewed);