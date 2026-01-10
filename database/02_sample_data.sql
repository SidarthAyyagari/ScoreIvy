-- Sample data for testing
-- Run this after 01_init_database.sql

-- Insert Literature section (other 3 sections are handled by comprehensive_data.sql)
-- This ensures we have 4 sections total: General Knowledge, Mathematics, Science, Literature
INSERT INTO sections (id, name, description) VALUES 
    (4, 'Literature', 'Literature and writing questions')
ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;

-- Insert sample questions
INSERT INTO questions (section_id, question_text, answer_choices, correct_answer, explanation, difficulty) VALUES
    (1, 'What is the capital of France?', '{"A": "London", "B": "Berlin", "C": "Paris", "D": "Madrid"}'::jsonb, 'C', 'Paris is the capital and largest city of France. It has been the capital since 987 AD and is known as the "City of Light".', 'easy'),
    (2, 'Which planet is known as the Red Planet?', '{"A": "Venus", "B": "Mars", "C": "Jupiter", "D": "Saturn"}'::jsonb, 'B', 'Mars is called the Red Planet because iron oxide (rust) on its surface gives it a distinctive reddish appearance.', 'easy'),
    (3, 'What is 2 + 2?', '{"A": "3", "B": "4", "C": "5", "D": "6"}'::jsonb, 'B', 'The sum of 2 and 2 equals 4. This is basic arithmetic addition.', 'easy'),
    (1, 'Who wrote "Romeo and Juliet"?', '{"A": "Charles Dickens", "B": "William Shakespeare", "C": "Jane Austen", "D": "Mark Twain"}'::jsonb, 'B', 'William Shakespeare wrote "Romeo and Juliet" in the late 16th century. It is one of his most famous tragedies.', 'medium'),
    (2, 'What is the largest ocean on Earth?', '{"A": "Atlantic Ocean", "B": "Indian Ocean", "C": "Arctic Ocean", "D": "Pacific Ocean"}'::jsonb, 'D', 'The Pacific Ocean is the largest and deepest ocean on Earth, covering approximately 63 million square miles.', 'easy'),
    (3, 'What is the chemical symbol for water?', '{"A": "H2O", "B": "CO2", "C": "O2", "D": "NaCl"}'::jsonb, 'A', 'H2O represents water, with two hydrogen atoms bonded to one oxygen atom. Water is the most abundant compound on Earth.', 'easy'),
    (1, 'Which year did World War II end?', '{"A": "1943", "B": "1944", "C": "1945", "D": "1946"}'::jsonb, 'C', 'World War II ended in 1945. The war in Europe ended on May 8, 1945 (V-E Day), and the war in the Pacific ended on September 2, 1945 (V-J Day).', 'medium'),
    (2, 'What is the smallest prime number?', '{"A": "0", "B": "1", "C": "2", "D": "3"}'::jsonb, 'C', '2 is the smallest prime number and the only even prime number, as it has exactly two positive divisors: 1 and 2.', 'medium'),
    (4, 'Which programming language is known as the "language of the web"?', '{"A": "Python", "B": "Java", "C": "JavaScript", "D": "C++"}'::jsonb, 'C', 'JavaScript is known as the "language of the web" because it is the primary scripting language that runs in web browsers.', 'easy'),
    (2, 'What is the speed of light in vacuum (approximately)?', '{"A": "300,000 km/s", "B": "150,000 km/s", "C": "450,000 km/s", "D": "600,000 km/s"}'::jsonb, 'A', 'The speed of light in a vacuum is approximately 299,792,458 meters per second, which rounds to about 300,000 km/s.', 'hard')
ON CONFLICT DO NOTHING;

-- Note: Packages, tests, and test_questions are now inserted via 05_comprehensive_data.sql
-- This ensures consistent "Practice Test 1-50" naming convention
-- All old test and test_questions data has been removed

