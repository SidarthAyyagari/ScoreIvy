-- Migration script to add test_sections table and update test_questions schema
-- Run this if the schema needs to be updated

-- Ensure packages.name has UNIQUE constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'packages_name_key' 
        AND conrelid = 'packages'::regclass
    ) THEN
        ALTER TABLE packages ADD CONSTRAINT packages_name_key UNIQUE (name);
    END IF;
END $$;

-- Ensure sections.name has UNIQUE constraint (may not exist if table was created differently)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'sections_name_key' 
        AND conrelid = 'sections'::regclass
    ) THEN
        ALTER TABLE sections ADD CONSTRAINT sections_name_key UNIQUE (name);
    END IF;
END $$;

-- Create Test Sections table if it doesn't exist
CREATE TABLE IF NOT EXISTS test_sections (
    id SERIAL PRIMARY KEY,
    test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    section_id INTEGER NOT NULL REFERENCES sections(id),
    section_order INTEGER NOT NULL, -- Order of section in the test (1, 2, 3)
    question_count INTEGER NOT NULL, -- Number of questions in this section for this test
    UNIQUE(test_id, section_id, section_order)
);

-- Add new columns to test_questions if they don't exist
DO $$ 
BEGIN
    -- Add section_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='test_questions' AND column_name='section_id') THEN
        ALTER TABLE test_questions ADD COLUMN section_id INTEGER REFERENCES sections(id);
    END IF;
    
    -- Add section_question_order column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='test_questions' AND column_name='section_question_order') THEN
        ALTER TABLE test_questions ADD COLUMN section_question_order INTEGER;
    END IF;
END $$;

-- Create Package Tests mapping table if it doesn't exist
CREATE TABLE IF NOT EXISTS package_tests (
    id SERIAL PRIMARY KEY,
    package_id INTEGER NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    test_order INTEGER NOT NULL, -- Order of test within the package
    UNIQUE(package_id, test_id),
    UNIQUE(package_id, test_order)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_test_sections_test ON test_sections(test_id);
CREATE INDEX IF NOT EXISTS idx_test_questions_section ON test_questions(section_id);
CREATE INDEX IF NOT EXISTS idx_package_tests_package ON package_tests(package_id);
CREATE INDEX IF NOT EXISTS idx_package_tests_test ON package_tests(test_id);

