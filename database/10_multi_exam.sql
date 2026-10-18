-- Multiple exams (USMLE, SAT, ...), timed sections, question types, topic tags, scaled scoring
CREATE TABLE IF NOT EXISTS exams (
    id SERIAL PRIMARY KEY,
    slug VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    tools JSONB NOT NULL DEFAULT '[]'::jsonb,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE packages ADD COLUMN IF NOT EXISTS exam_id INTEGER REFERENCES exams(id);
ALTER TABLE tests ADD COLUMN IF NOT EXISTS exam_id INTEGER REFERENCES exams(id);
ALTER TABLE tests ADD COLUMN IF NOT EXISTS scoring JSONB;
ALTER TABLE sections ADD COLUMN IF NOT EXISTS exam_id INTEGER REFERENCES exams(id);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS exam_id INTEGER REFERENCES exams(id);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS question_type VARCHAR NOT NULL DEFAULT 'multiple_choice';
ALTER TABLE questions ADD COLUMN IF NOT EXISTS accepted_answers JSONB;
ALTER TABLE test_sections ADD COLUMN IF NOT EXISTS name VARCHAR;
ALTER TABLE test_sections ADD COLUMN IF NOT EXISTS time_limit_minutes INTEGER;
ALTER TABLE test_questions ADD COLUMN IF NOT EXISTS test_section_id INTEGER REFERENCES test_sections(id) ON DELETE SET NULL;
ALTER TABLE test_attempts ADD COLUMN IF NOT EXISTS scaled_score INTEGER;
ALTER TABLE test_attempts ADD COLUMN IF NOT EXISTS section_scores JSONB;

CREATE TABLE IF NOT EXISTS attempt_sections (
    id SERIAL PRIMARY KEY,
    test_attempt_id INTEGER NOT NULL REFERENCES test_attempts(id) ON DELETE CASCADE,
    test_section_id INTEGER REFERENCES test_sections(id) ON DELETE SET NULL,
    section_order INTEGER NOT NULL,
    name VARCHAR,
    time_limit_minutes INTEGER NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    deadline_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(test_attempt_id, section_order)
);

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    category VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    UNIQUE(exam_id, category, name)
);

CREATE TABLE IF NOT EXISTS question_tags (
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (question_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_packages_exam ON packages(exam_id);
CREATE INDEX IF NOT EXISTS idx_tests_exam ON tests(exam_id);
CREATE INDEX IF NOT EXISTS idx_questions_exam ON questions(exam_id);
CREATE INDEX IF NOT EXISTS idx_attempt_sections_attempt ON attempt_sections(test_attempt_id);
CREATE INDEX IF NOT EXISTS idx_question_tags_tag ON question_tags(tag_id);
