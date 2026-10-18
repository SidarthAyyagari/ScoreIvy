-- Package credit expiry (days after purchase; NULL = never expires) and server-enforced exam deadlines
ALTER TABLE packages ADD COLUMN IF NOT EXISTS validity_days INTEGER DEFAULT 180;
ALTER TABLE test_attempts ADD COLUMN IF NOT EXISTS deadline_at TIMESTAMP WITH TIME ZONE;
CREATE INDEX IF NOT EXISTS idx_test_attempts_user_test ON test_attempts(user_id, test_id);
