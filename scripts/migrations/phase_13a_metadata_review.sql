ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS metadata_candidate JSON;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS metadata_proposed_updates JSON;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS metadata_review_status VARCHAR(30)
    NOT NULL DEFAULT 'not_requested';

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS metadata_review_notes TEXT;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS metadata_reviewed_at
    TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_documents_metadata_review_status
    ON documents (metadata_review_status);