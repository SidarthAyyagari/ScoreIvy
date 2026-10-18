-- Mixed-subject parts (USMLE blocks) and per-exam break rules
ALTER TABLE test_sections ALTER COLUMN section_id DROP NOT NULL;
ALTER TABLE test_questions ALTER COLUMN section_id DROP NOT NULL;

-- Shared break budget for the whole test (USMLE Step 1: 45). NULL = use test_sections.break_after_minutes.
ALTER TABLE tests ADD COLUMN IF NOT EXISTS break_pool_minutes INTEGER;
-- Break allowed after this part when there is no shared budget (SAT: 10 after Reading and Writing, else 0).
ALTER TABLE test_sections ADD COLUMN IF NOT EXISTS break_after_minutes INTEGER;
