-- Migration script to add more tests to existing database
-- Run this if you already have a database with the initial sample data

-- General Knowledge Test 2
INSERT INTO test_questions (test_id, question_id, question_order) VALUES
    (4, 1, 1),  -- What is the capital of France?
    (4, 4, 2),  -- Who wrote "Romeo and Juliet"?
    (4, 7, 3),  -- Which year did World War II end?
    (4, 2, 4),  -- Which planet is known as the Red Planet?
    (4, 5, 5),  -- What is the largest ocean on Earth?
    (4, 6, 6),  -- What is the chemical symbol for water?
    (4, 9, 7),  -- Which programming language is known as the "language of the web"?
    (4, 3, 8),  -- What is 2 + 2?
    (4, 8, 9),  -- What is the smallest prime number?
    (4, 10, 10) -- What is the speed of light?
ON CONFLICT DO NOTHING;

-- Mathematics Test 2
INSERT INTO test_questions (test_id, question_id, question_order) VALUES
    (5, 3, 1),  -- What is 2 + 2?
    (5, 8, 2),  -- What is the smallest prime number?
    (5, 10, 3), -- What is the speed of light?
    (5, 3, 4),  -- What is 2 + 2?
    (5, 8, 5),  -- What is the smallest prime number?
    (5, 10, 6), -- What is the speed of light?
    (5, 3, 7),  -- What is 2 + 2?
    (5, 8, 8)   -- What is the smallest prime number?
ON CONFLICT DO NOTHING;

-- Science Test 2
INSERT INTO test_questions (test_id, question_id, question_order) VALUES
    (6, 2, 1),  -- Which planet is known as the Red Planet?
    (6, 5, 2),  -- What is the largest ocean on Earth?
    (6, 6, 3),  -- What is the chemical symbol for water?
    (6, 10, 4), -- What is the speed of light?
    (6, 2, 5),  -- Which planet is known as the Red Planet?
    (6, 5, 6),  -- What is the largest ocean on Earth?
    (6, 6, 7),  -- What is the chemical symbol for water?
    (6, 10, 8), -- What is the speed of light?
    (6, 2, 9),  -- Which planet is known as the Red Planet?
    (6, 5, 10)  -- What is the largest ocean on Earth?
ON CONFLICT DO NOTHING;

-- Literature Test 1
INSERT INTO test_questions (test_id, question_id, question_order) VALUES
    (7, 4, 1),  -- Who wrote "Romeo and Juliet"?
    (7, 9, 2),  -- Which programming language is known as the "language of the web"?
    (7, 4, 3),  -- Who wrote "Romeo and Juliet"?
    (7, 9, 4),  -- Which programming language is known as the "language of the web"?
    (7, 4, 5),  -- Who wrote "Romeo and Juliet"?
    (7, 9, 6),  -- Which programming language is known as the "language of the web"?
    (7, 4, 7),  -- Who wrote "Romeo and Juliet"?
    (7, 9, 8)   -- Which programming language is known as the "language of the web"?
ON CONFLICT DO NOTHING;

-- History Test 1
INSERT INTO test_questions (test_id, question_id, question_order) VALUES
    (8, 7, 1),  -- Which year did World War II end?
    (8, 1, 2),  -- What is the capital of France?
    (8, 7, 3),  -- Which year did World War II end?
    (8, 1, 4),  -- What is the capital of France?
    (8, 7, 5),  -- Which year did World War II end?
    (8, 1, 6),  -- What is the capital of France?
    (8, 7, 7),  -- Which year did World War II end?
    (8, 1, 8),  -- What is the capital of France?
    (8, 7, 9),  -- Which year did World War II end?
    (8, 1, 10)  -- What is the capital of France?
ON CONFLICT DO NOTHING;

-- General Knowledge Test 3
INSERT INTO test_questions (test_id, question_id, question_order) VALUES
    (9, 1, 1),  -- What is the capital of France?
    (9, 2, 2),  -- Which planet is known as the Red Planet?
    (9, 3, 3),  -- What is 2 + 2?
    (9, 4, 4),  -- Who wrote "Romeo and Juliet"?
    (9, 5, 5),  -- What is the largest ocean on Earth?
    (9, 6, 6),  -- What is the chemical symbol for water?
    (9, 7, 7),  -- Which year did World War II end?
    (9, 8, 8),  -- What is the smallest prime number?
    (9, 9, 9),  -- Which programming language is known as the "language of the web"?
    (9, 10, 10) -- What is the speed of light?
ON CONFLICT DO NOTHING;

-- Mathematics Test 3
INSERT INTO test_questions (test_id, question_id, question_order) VALUES
    (10, 3, 1),  -- What is 2 + 2?
    (10, 8, 2),  -- What is the smallest prime number?
    (10, 10, 3), -- What is the speed of light?
    (10, 3, 4),  -- What is 2 + 2?
    (10, 8, 5),  -- What is the smallest prime number?
    (10, 10, 6), -- What is the speed of light?
    (10, 3, 7),  -- What is 2 + 2?
    (10, 8, 8),  -- What is the smallest prime number?
    (10, 10, 9), -- What is the speed of light?
    (10, 3, 10)  -- What is 2 + 2?
ON CONFLICT DO NOTHING;

