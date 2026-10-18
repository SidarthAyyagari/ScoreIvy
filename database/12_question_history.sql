-- Question edit history and per-attempt question snapshots
CREATE TABLE IF NOT EXISTS question_revisions (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL,
    action VARCHAR NOT NULL,
    snapshot JSONB NOT NULL,
    note VARCHAR,
    changed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    changed_by_email VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_question_revisions_question ON question_revisions(question_id, id);

ALTER TABLE test_attempts ADD COLUMN IF NOT EXISTS question_ids JSONB;
