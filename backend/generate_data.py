#!/usr/bin/env python3
"""
Script to generate comprehensive test data:
- 3 sections
- 500 questions
- 50 tests (each with 3 sections, 10 questions total)
- 3 packages (Basic: 10 tests, Standard: 25 tests, Premium: 50 tests)
"""

import json

def generate_sections():
    """Generate 3 sections"""
    return [
        (1, 'General Knowledge', 'General knowledge and trivia questions'),
        (2, 'Mathematics', 'Mathematics, arithmetic, and problem-solving questions'),
        (3, 'Science', 'Science, physics, chemistry, and biology questions'),
    ]

def generate_questions():
    """Generate 500 questions across 3 sections"""
    questions = []
    
    # General Knowledge questions (section 1)
    gk_questions = [
        ("What is the capital of France?", {"A": "London", "B": "Berlin", "C": "Paris", "D": "Madrid"}, "C", 
         "Paris is the capital and largest city of France. It has been the capital since 987 AD.", "easy"),
        ("Which planet is known as the Red Planet?", {"A": "Venus", "B": "Mars", "C": "Jupiter", "D": "Saturn"}, "B",
         "Mars is called the Red Planet because iron oxide on its surface gives it a reddish appearance.", "easy"),
        ("Who wrote 'Romeo and Juliet'?", {"A": "Charles Dickens", "B": "William Shakespeare", "C": "Jane Austen", "D": "Mark Twain"}, "B",
         "William Shakespeare wrote 'Romeo and Juliet' in the late 16th century.", "medium"),
        ("Which year did World War II end?", {"A": "1943", "B": "1944", "C": "1945", "D": "1946"}, "C",
         "World War II ended in 1945. The war in Europe ended on May 8, 1945 (V-E Day).", "medium"),
        ("What is the largest ocean on Earth?", {"A": "Atlantic Ocean", "B": "Indian Ocean", "C": "Arctic Ocean", "D": "Pacific Ocean"}, "D",
         "The Pacific Ocean is the largest and deepest ocean on Earth, covering approximately 63 million square miles.", "easy"),
        ("Which programming language is known as the 'language of the web'?", {"A": "Python", "B": "Java", "C": "JavaScript", "D": "C++"}, "C",
         "JavaScript is known as the 'language of the web' because it runs in web browsers.", "easy"),
        ("What is the capital of Japan?", {"A": "Seoul", "B": "Beijing", "C": "Tokyo", "D": "Bangkok"}, "C",
         "Tokyo is the capital and largest city of Japan.", "easy"),
        ("Which country is known as the 'Land of the Rising Sun'?", {"A": "China", "B": "Japan", "C": "South Korea", "D": "Thailand"}, "B",
         "Japan is known as the 'Land of the Rising Sun' due to its location east of China.", "easy"),
        ("Who painted the Mona Lisa?", {"A": "Vincent van Gogh", "B": "Pablo Picasso", "C": "Leonardo da Vinci", "D": "Michelangelo"}, "C",
         "Leonardo da Vinci painted the Mona Lisa between 1503 and 1519.", "medium"),
        ("What is the smallest country in the world?", {"A": "Monaco", "B": "Vatican City", "C": "San Marino", "D": "Liechtenstein"}, "B",
         "Vatican City is the smallest country in the world by area, at just 0.17 square miles.", "medium"),
    ]
    
    # Generate more GK questions by varying existing ones
    for i in range(167):  # 167 questions per section (500/3 ≈ 167)
        base_q = gk_questions[i % len(gk_questions)]
        question_id = i + 1
        questions.append({
            'id': question_id,
            'section_id': 1,
            'question_text': base_q[0] if i < len(gk_questions) else f"{base_q[0]} (Question {i+1})",
            'answer_choices': base_q[1],
            'correct_answer': base_q[2],
            'explanation': base_q[3],
            'difficulty': base_q[4]
        })
    
    # Mathematics questions (section 2)
    math_questions = [
        ("What is 2 + 2?", {"A": "3", "B": "4", "C": "5", "D": "6"}, "B",
         "The sum of 2 and 2 equals 4. This is basic arithmetic addition.", "easy"),
        ("What is the smallest prime number?", {"A": "0", "B": "1", "C": "2", "D": "3"}, "C",
         "2 is the smallest prime number and the only even prime number.", "medium"),
        ("What is 5 × 7?", {"A": "30", "B": "35", "C": "40", "D": "42"}, "B",
         "5 multiplied by 7 equals 35.", "easy"),
        ("What is the square root of 16?", {"A": "2", "B": "4", "C": "6", "D": "8"}, "B",
         "The square root of 16 is 4, since 4 × 4 = 16.", "easy"),
        ("What is 15% of 200?", {"A": "20", "B": "30", "C": "40", "D": "50"}, "B",
         "15% of 200 is calculated as 0.15 × 200 = 30.", "medium"),
        ("What is the value of π (pi) approximately?", {"A": "3.12", "B": "3.14", "C": "3.16", "D": "3.18"}, "B",
         "Pi (π) is approximately 3.14159, which rounds to 3.14.", "easy"),
        ("What is 12 ÷ 3?", {"A": "2", "B": "3", "C": "4", "D": "5"}, "C",
         "12 divided by 3 equals 4.", "easy"),
        ("What is 3²?", {"A": "6", "B": "9", "C": "12", "D": "15"}, "B",
         "3 squared (3²) equals 3 × 3 = 9.", "easy"),
        ("What is 100 - 47?", {"A": "53", "B": "54", "C": "55", "D": "56"}, "A",
         "100 minus 47 equals 53.", "easy"),
        ("What is the area of a rectangle with length 8 and width 5?", {"A": "30", "B": "35", "C": "40", "D": "45"}, "C",
         "The area of a rectangle is length × width, so 8 × 5 = 40.", "medium"),
    ]
    
    for i in range(167):
        base_q = math_questions[i % len(math_questions)]
        question_id = 167 + i + 1
        questions.append({
            'id': question_id,
            'section_id': 2,
            'question_text': base_q[0] if i < len(math_questions) else f"{base_q[0]} (Question {i+1})",
            'answer_choices': base_q[1],
            'correct_answer': base_q[2],
            'explanation': base_q[3],
            'difficulty': base_q[4]
        })
    
    # Science questions (section 3)
    science_questions = [
        ("What is the chemical symbol for water?", {"A": "H2O", "B": "CO2", "C": "O2", "D": "NaCl"}, "A",
         "H2O represents water, with two hydrogen atoms bonded to one oxygen atom.", "easy"),
        ("What is the speed of light in vacuum (approximately)?", {"A": "300,000 km/s", "B": "150,000 km/s", "C": "450,000 km/s", "D": "600,000 km/s"}, "A",
         "The speed of light in a vacuum is approximately 299,792,458 meters per second, which rounds to about 300,000 km/s.", "hard"),
        ("At what temperature does water boil at sea level?", {"A": "90°C", "B": "100°C", "C": "110°C", "D": "120°C"}, "B",
         "Water boils at 100°C (212°F) at sea level under standard atmospheric pressure.", "easy"),
        ("What is the smallest unit of matter?", {"A": "Molecule", "B": "Atom", "C": "Electron", "D": "Proton"}, "B",
         "An atom is the smallest unit of matter that retains the properties of an element.", "medium"),
        ("How many bones are in the adult human body?", {"A": "196", "B": "206", "C": "216", "D": "226"}, "B",
         "An adult human body has 206 bones. Babies have more bones that fuse together as they grow.", "medium"),
        ("What gas do plants absorb from the atmosphere?", {"A": "Oxygen", "B": "Carbon Dioxide", "C": "Nitrogen", "D": "Hydrogen"}, "B",
         "Plants absorb carbon dioxide (CO2) from the atmosphere during photosynthesis.", "easy"),
        ("What is the hardest natural substance on Earth?", {"A": "Gold", "B": "Iron", "C": "Diamond", "D": "Platinum"}, "C",
         "Diamond is the hardest naturally occurring substance on Earth on the Mohs scale.", "easy"),
        ("What is the largest planet in our solar system?", {"A": "Earth", "B": "Saturn", "C": "Jupiter", "D": "Neptune"}, "C",
         "Jupiter is the largest planet in our solar system, with a mass greater than all other planets combined.", "easy"),
        ("How many planets are in our solar system?", {"A": "7", "B": "8", "C": "9", "D": "10"}, "B",
         "There are 8 planets in our solar system: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.", "easy"),
        ("What is the chemical symbol for gold?", {"A": "Go", "B": "Gd", "C": "Au", "D": "Ag"}, "C",
         "Au is the chemical symbol for gold, derived from the Latin word 'aurum'.", "medium"),
    ]
    
    for i in range(166):  # 166 questions to make total 500
        base_q = science_questions[i % len(science_questions)]
        question_id = 334 + i + 1
        questions.append({
            'id': question_id,
            'section_id': 3,
            'question_text': base_q[0] if i < len(science_questions) else f"{base_q[0]} (Question {i+1})",
            'answer_choices': base_q[1],
            'correct_answer': base_q[2],
            'explanation': base_q[3],
            'difficulty': base_q[4]
        })
    
    return questions

def generate_tests_and_questions():
    """Generate 50 tests, each with 3 sections and 10 questions"""
    # Section distributions: [3, 4, 3], [3, 3, 4], [4, 3, 3], etc.
    section_distributions = [
        (3, 4, 3), (3, 3, 4), (4, 3, 3),
        (4, 3, 3), (3, 4, 3), (3, 3, 4),
    ]
    
    tests = []
    test_questions_data = []
    test_sections_data = []
    
    # Question IDs by section
    gk_questions = list(range(1, 168))  # 167 GK questions
    math_questions = list(range(168, 335))  # 167 Math questions
    science_questions = list(range(335, 501))  # 166 Science questions
    
    question_idx_by_section = {
        1: 0,  # GK
        2: 0,  # Math
        3: 0,  # Science
    }
    
    for test_num in range(1, 51):
        # Get section distribution for this test
        dist = section_distributions[(test_num - 1) % len(section_distributions)]
        q1_count, q2_count, q3_count = dist
        
        # Standard naming convention: Practice Test 1, Practice Test 2, etc.
        test_name = f"Practice Test {test_num}"
        tests.append({
            'id': test_num,
            'name': test_name,
            'description': f'Comprehensive practice test with {q1_count}+{q2_count}+{q3_count} questions across 3 sections',
            'time_limit_minutes': 30,
            'question_count': 10,
            'is_active': True,
        })
        
        # Add test sections
        test_sections_data.append({
            'test_id': test_num,
            'section_id': 1,
            'section_order': 1,
            'question_count': q1_count,
        })
        test_sections_data.append({
            'test_id': test_num,
            'section_id': 2,
            'section_order': 2,
            'question_count': q2_count,
        })
        test_sections_data.append({
            'test_id': test_num,
            'section_id': 3,
            'section_order': 3,
            'question_count': q3_count,
        })
        
        # Add questions for each section
        question_order = 1
        
        # Section 1 questions
        for i in range(q1_count):
            q_idx = question_idx_by_section[1] % len(gk_questions)
            q_id = gk_questions[q_idx]
            test_questions_data.append({
                'test_id': test_num,
                'question_id': q_id,
                'section_id': 1,
                'question_order': question_order,
                'section_question_order': i + 1,
            })
            question_order += 1
            question_idx_by_section[1] += 1
        
        # Section 2 questions
        for i in range(q2_count):
            q_idx = question_idx_by_section[2] % len(math_questions)
            q_id = math_questions[q_idx]
            test_questions_data.append({
                'test_id': test_num,
                'question_id': q_id,
                'section_id': 2,
                'question_order': question_order,
                'section_question_order': i + 1,
            })
            question_order += 1
            question_idx_by_section[2] += 1
        
        # Section 3 questions
        for i in range(q3_count):
            q_idx = question_idx_by_section[3] % len(science_questions)
            q_id = science_questions[q_idx]
            test_questions_data.append({
                'test_id': test_num,
                'question_id': q_id,
                'section_id': 3,
                'question_order': question_order,
                'section_question_order': i + 1,
            })
            question_order += 1
            question_idx_by_section[3] += 1
    
    return tests, test_questions_data, test_sections_data

def generate_sql():
    """Generate SQL script"""
    sections = generate_sections()
    questions = generate_questions()
    tests, test_questions, test_sections = generate_tests_and_questions()
    
    sql_lines = [
        "-- Comprehensive Data Initialization Script",
        "-- Generated automatically",
        "",
        "-- Ensure sections exist (exactly 3)",
    ]
    
    # Sections - use id for conflict resolution since we're specifying IDs
    for section_id, name, desc in sections:
        sql_lines.append(
            f"INSERT INTO sections (id, name, description) VALUES "
            f"({section_id}, '{name}', '{desc}') "
            f"ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description;"
        )
    
    sql_lines.append("")
    sql_lines.append("-- Ensure packages exist (exactly 3)")
    
    # Packages
    packages = [
        (1, 'Basic Package', '10 practice tests', 10, 29.99),
        (2, 'Standard Package', '25 practice tests', 25, 59.99),
        (3, 'Premium Package', '50 practice tests', 50, 99.99),
    ]
    
    for pkg_id, name, desc, count, price in packages:
        sql_lines.append(
            f"INSERT INTO packages (id, name, description, test_count, price, is_active) VALUES "
            f"({pkg_id}, '{name}', '{desc}', {count}, {price}, true) "
            f"ON CONFLICT (name) DO NOTHING;"
        )
    
    sql_lines.append("")
    sql_lines.append("-- Clear existing test data (if needed)")
    sql_lines.append("-- DELETE FROM test_questions;")
    sql_lines.append("-- DELETE FROM test_sections;")
    sql_lines.append("-- DELETE FROM tests;")
    sql_lines.append("-- DELETE FROM questions;")
    sql_lines.append("")
    sql_lines.append("-- Insert questions (only if they don't exist)")
    
    # Questions - use DO NOTHING approach since we can't easily check if they exist
    # We'll insert all, and let the backend handle uniqueness
    for q in questions:
        answer_choices_json = json.dumps(q['answer_choices']).replace("'", "''")
        explanation = q['explanation'].replace("'", "''")
        question_text = q['question_text'].replace("'", "''")
        
        sql_lines.append(
            f"INSERT INTO questions (id, section_id, question_text, answer_choices, correct_answer, explanation, difficulty, is_active) "
            f"VALUES ({q['id']}, {q['section_id']}, '{question_text}', '{answer_choices_json}'::jsonb, "
            f"'{q['correct_answer']}', '{explanation}', '{q['difficulty']}', true) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    
    sql_lines.append("")
    sql_lines.append("-- Insert tests (only if they don't exist)")
    
    # Tests - use DO UPDATE to ensure correct names even if old data exists
    for test in tests:
        description = test['description'].replace("'", "''")
        sql_lines.append(
            f"INSERT INTO tests (id, name, description, time_limit_minutes, question_count, is_active) "
            f"VALUES ({test['id']}, '{test['name']}', '{description}', {test['time_limit_minutes']}, "
            f"{test['question_count']}, {str(test['is_active']).lower()}) "
            f"ON CONFLICT (id) DO UPDATE SET "
            f"name = EXCLUDED.name, description = EXCLUDED.description, "
            f"time_limit_minutes = EXCLUDED.time_limit_minutes, question_count = EXCLUDED.question_count, "
            f"is_active = EXCLUDED.is_active;"
        )
    
    sql_lines.append("")
    sql_lines.append("-- Insert test sections")
    
    # Test sections
    for ts in test_sections:
        sql_lines.append(
            f"INSERT INTO test_sections (test_id, section_id, section_order, question_count) "
            f"VALUES ({ts['test_id']}, {ts['section_id']}, {ts['section_order']}, {ts['question_count']}) "
            f"ON CONFLICT (test_id, section_id, section_order) DO UPDATE SET question_count = EXCLUDED.question_count;"
        )
    
    sql_lines.append("")
    sql_lines.append("-- Insert test questions")
    
    # Test questions
    for tq in test_questions:
        sql_lines.append(
            f"INSERT INTO test_questions (test_id, question_id, section_id, question_order, section_question_order) "
            f"VALUES ({tq['test_id']}, {tq['question_id']}, {tq['section_id']}, {tq['question_order']}, "
            f"{tq['section_question_order']}) "
            f"ON CONFLICT (test_id, question_id) DO UPDATE SET "
            f"section_id = EXCLUDED.section_id, question_order = EXCLUDED.question_order, "
            f"section_question_order = EXCLUDED.section_question_order;"
        )
    
    sql_lines.append("")
    sql_lines.append("-- Insert package-test mappings")
    sql_lines.append("-- Basic Package (1): tests 1-10")
    sql_lines.append("-- Standard Package (2): tests 1-25")
    sql_lines.append("-- Premium Package (3): tests 1-50")
    
    # Package-Test mappings
    package_test_mappings = []
    for pkg_id, test_count in [(1, 10), (2, 25), (3, 50)]:
        for i in range(1, test_count + 1):
            package_test_mappings.append({
                'package_id': pkg_id,
                'test_id': i,
                'test_order': i
            })
    
    for mapping in package_test_mappings:
        sql_lines.append(
            f"INSERT INTO package_tests (package_id, test_id, test_order) "
            f"VALUES ({mapping['package_id']}, {mapping['test_id']}, {mapping['test_order']}) "
            f"ON CONFLICT (package_id, test_id) DO UPDATE SET test_order = EXCLUDED.test_order;"
        )
    
    return '\n'.join(sql_lines)

if __name__ == '__main__':
    sql = generate_sql()
    with open('database/05_comprehensive_data.sql', 'w') as f:
        f.write(sql)
    print("✅ Generated comprehensive data SQL script: database/05_comprehensive_data.sql")
    print("   - 3 sections")
    print("   - 500 questions")
    print("   - 50 tests (each with 3 sections, 10 questions)")
    print("   - 3 packages (Basic: 10 tests, Standard: 25 tests, Premium: 50 tests)")

