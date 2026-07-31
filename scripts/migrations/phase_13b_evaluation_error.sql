ALTER TABLE book_curations
    ADD COLUMN IF NOT EXISTS evaluation_error TEXT;