"""Load demo content for USMLE Step 1 and SAT so the site can be clicked through locally.

Adds clearly labeled "[Demo]" subject sections, questions, tests, and one package per exam:
a full-length test in the real format plus a short "Quick Check" test (tiny parts, 2-minute
timers and breaks) for trying the timing and break flow quickly.

    cd backend && source venv/bin/activate && python -m scripts.seed_demo

Safe to run more than once: it does nothing if the demo packages already exist.
Refuses to run with ENV=production.
"""

import random
import sys
from typing import Dict, List

from app.config import IS_PRODUCTION
from app.db.database import SessionLocal
from app.models.models import Exam, Package, Section
from app.schemas.admin_schemas import BuildPart, BuildTestRequest
from app.schemas.schemas import QuestionCreate
from app.services.questions import create_question
from app.services.test_builder import build_test

DEMO = "[Demo]"

STEP1_SUBJECTS = ["Physiology", "Pathology", "Pharmacology", "Microbiology", "Biochemistry"]
STEP1_SYSTEMS = ["Cardiovascular", "Renal", "Respiratory", "Gastrointestinal", "Nervous System", "Endocrine"]
SAT_RW_SKILLS = ["Craft and Structure", "Information and Ideas", "Standard English Conventions", "Expression of Ideas"]
SAT_MATH_SKILLS = ["Algebra", "Advanced Math", "Problem-Solving and Data Analysis", "Geometry and Trigonometry"]


def _section(db, exam: Exam, name: str) -> Section:
    full_name = f"{DEMO} {exam.name}: {name}"
    section = db.query(Section).filter(Section.name == full_name).first()
    if section is None:
        section = Section(exam_id=exam.id, name=full_name, description="Demo subject")
        db.add(section)
        db.flush()
    return section


def _scale(raw_max: int) -> Dict[str, int]:
    """Linear 200-800 table (SAT section scale), rounded to 10."""
    return {str(raw): 200 + round(60 * raw / raw_max) * 10 for raw in range(raw_max + 1)}


def _step1_questions(db, exam: Exam, rng: random.Random, count: int) -> None:
    sections = [_section(db, exam, name) for name in STEP1_SUBJECTS]
    for n in range(1, count + 1):
        section = sections[n % len(sections)]
        system = STEP1_SYSTEMS[n % len(STEP1_SYSTEMS)]
        subject = section.name.split(": ")[-1]
        age = rng.randint(19, 78)
        correct = rng.choice("ABCDE")
        create_question(db, QuestionCreate(
            exam_id=exam.id,
            section_id=section.id,
            question_text=(
                f"{DEMO} Step 1 #{n} ({subject}, {system}). A {age}-year-old patient presents with symptoms "
                f"involving the {system.lower()} system. Which of the following is the most likely explanation?"
            ),
            answer_choices={letter: f"Demo option {letter}" for letter in "ABCDE"},
            correct_answer=correct,
            explanation=f"Demo explanation: option {correct} is correct for this placeholder question.",
            difficulty=rng.choice(["easy", "medium", "hard"]),
            tags=[f"system:{system}", f"discipline:{subject}"],
        ))


def _sat_questions(db, exam: Exam, rng: random.Random, rw_count: int, math_count: int) -> List[Section]:
    reading = _section(db, exam, "Reading and Writing")
    math = _section(db, exam, "Math")
    for n in range(1, rw_count + 1):
        skill = SAT_RW_SKILLS[n % len(SAT_RW_SKILLS)]
        correct = rng.choice("ABCD")
        create_question(db, QuestionCreate(
            exam_id=exam.id,
            section_id=reading.id,
            question_text=(
                f"{DEMO} SAT Reading and Writing #{n} ({skill}). Read the short passage and choose the "
                "answer that most logically completes the text."
            ),
            answer_choices={letter: f"Demo option {letter}" for letter in "ABCD"},
            correct_answer=correct,
            explanation=f"Demo explanation: option {correct} is correct for this placeholder question.",
            difficulty=rng.choice(["easy", "medium", "hard"]),
            tags=[f"skill:{skill}"],
        ))
    for n in range(1, math_count + 1):
        skill = SAT_MATH_SKILLS[n % len(SAT_MATH_SKILLS)]
        a, x, b = rng.randint(2, 9), rng.randint(1, 12), rng.randint(1, 30)
        stem = f"{DEMO} SAT Math #{n} ({skill}). If {a}x + {b} = {a * x + b}, what is the value of x?"
        tags = [f"skill:{skill}"]
        if n % 4 == 0:
            create_question(db, QuestionCreate(
                exam_id=exam.id, section_id=math.id, question_type="numeric_entry",
                question_text=stem + " (Enter your answer.)", correct_answer=str(x),
                explanation=f"Subtract {b} and divide by {a}: x = {x}.", difficulty="medium", tags=tags,
            ))
            continue
        choices = sorted({x, x + 1, x - 1, x + 2} if x > 1 else {x, x + 1, x + 2, x + 3})
        letters = dict(zip("ABCD", (str(c) for c in choices)))
        correct = next(letter for letter, value in letters.items() if value == str(x))
        create_question(db, QuestionCreate(
            exam_id=exam.id, section_id=math.id, question_text=stem, answer_choices=letters,
            correct_answer=correct, explanation=f"Subtract {b} and divide by {a}: x = {x}.",
            difficulty=rng.choice(["easy", "medium", "hard"]), tags=tags,
        ))
    return [reading, math]


def _package(db, exam: Exam, name: str, price: float, description: str) -> Package:
    package = Package(
        exam_id=exam.id, name=name, description=description, test_count=2, price=price, validity_days=180,
        is_active=True,
    )
    db.add(package)
    db.flush()
    return package


def _build(db, request: BuildTestRequest) -> None:
    result = build_test(db, request)
    print(f"  built test {result.test_id}: {request.name} ({sum(p.question_count for p in result.parts)} questions)")


def seed() -> None:
    if IS_PRODUCTION:
        sys.exit("Refusing to load demo data with ENV=production")
    db = SessionLocal()
    try:
        if db.query(Package).filter(Package.name.like(f"{DEMO}%")).first():
            print("Demo data already loaded; nothing to do.")
            return
        step1 = db.query(Exam).filter(Exam.slug == "usmle-step-1").one()
        sat = db.query(Exam).filter(Exam.slug == "sat").one()
        rng = random.Random(2026)

        print("USMLE Step 1")
        _step1_questions(db, step1, rng, count=300)
        pack = _package(db, step1, f"{DEMO} USMLE Step 1 Pack", 49.0, "1 full-length test + 1 quick check")
        _build(db, BuildTestRequest(
            exam_id=step1.id, name=f"{DEMO} Step 1 Practice Test 1", break_pool_minutes=45, package_id=pack.id,
            parts=[BuildPart(name=f"Block {i}", question_count=40, time_limit_minutes=60) for i in range(1, 8)],
            seed=1,
        ))
        _build(db, BuildTestRequest(
            exam_id=step1.id, name=f"{DEMO} Step 1 Quick Check", break_pool_minutes=2, package_id=pack.id,
            description="3 blocks of 3 questions, 2 minutes each, 2-minute shared break budget",
            parts=[BuildPart(name=f"Block {i}", question_count=3, time_limit_minutes=2) for i in range(1, 4)],
            seed=2,
        ))

        print("SAT")
        reading, math = _sat_questions(db, sat, rng, rw_count=80, math_count=70)
        pack = _package(db, sat, f"{DEMO} SAT Pack", 29.0, "1 full-length test + 1 quick check")

        def sat_parts(rw_count, rw_minutes, math_count, math_minutes, long_break):
            return [
                BuildPart(name="Reading and Writing: Module 1", question_count=rw_count,
                          time_limit_minutes=rw_minutes, section_ids=[reading.id], break_after_minutes=0),
                BuildPart(name="Reading and Writing: Module 2", question_count=rw_count,
                          time_limit_minutes=rw_minutes, section_ids=[reading.id], break_after_minutes=long_break),
                BuildPart(name="Math: Module 1", question_count=math_count,
                          time_limit_minutes=math_minutes, section_ids=[math.id], break_after_minutes=0),
                BuildPart(name="Math: Module 2", question_count=math_count,
                          time_limit_minutes=math_minutes, section_ids=[math.id]),
            ]

        _build(db, BuildTestRequest(
            exam_id=sat.id, name=f"{DEMO} SAT Practice Test 1", package_id=pack.id, seed=3,
            parts=sat_parts(27, 32, 22, 35, long_break=10),
            scoring={"sections": {str(reading.id): _scale(54), str(math.id): _scale(44)}},
        ))
        _build(db, BuildTestRequest(
            exam_id=sat.id, name=f"{DEMO} SAT Quick Check", package_id=pack.id, seed=4,
            description="4 modules of 3 questions, 2 minutes each, 2-minute break between sections",
            parts=sat_parts(3, 2, 3, 2, long_break=2),
            scoring={"sections": {str(reading.id): _scale(6), str(math.id): _scale(6)}},
        ))

        db.commit()
        print("Done. Buy the demo packs on the student dashboard (free locally) to take the tests.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
