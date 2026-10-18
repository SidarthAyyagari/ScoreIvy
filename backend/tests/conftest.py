import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ENV"] = "test"
os.environ["SKIP_ADMIN_AUTH"] = "false"
os.environ["ALLOW_FREE_PURCHASE"] = "true"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["ADMIN_EMAILS"] = "admin@example.com"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-1234"
os.environ["STRIPE_SECRET_KEY"] = ""
os.environ["STRIPE_WEBHOOK_SECRET"] = ""
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token
from app.db.database import Base, get_db
from app.models.models import (
    Exam, Package, PackageTest, Question, Section, Test, TestQuestion, TestSection, User,
)
from main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def _get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def student(db):
    user = User(email="student@example.com", name="Student", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id), 'email': user.email})}"}


def _add_question(db, exam, section, test, order, test_section=None, **fields):
    question = Question(
        exam_id=exam.id,
        section_id=section.id,
        question_text=f"{test.name} Q{order}",
        answer_choices=fields.pop("answer_choices", {"A": "a", "B": "b", "C": "c", "D": "d"}),
        correct_answer=fields.pop("correct_answer", "A"),
        explanation="because",
        **fields,
    )
    db.add(question)
    db.flush()
    db.add(TestQuestion(
        test_id=test.id, question_id=question.id, section_id=section.id,
        test_section_id=test_section.id if test_section else None,
        question_order=order, section_question_order=order,
    ))
    return question


@pytest.fixture()
def catalog(db):
    """USMLE package (2 credits, 30-day validity) with two 3-question single-block tests,
    a USMLE test outside the package, a two-block USMLE test, and an SAT test with
    a numeric-entry question and a scaled score table."""
    usmle = Exam(slug="usmle-step-1", name="USMLE Step 1", tools=["lab_values"], display_order=1)
    sat = Exam(slug="sat", name="SAT", tools=["calculator", "reference_sheet"], display_order=2)
    db.add_all([usmle, sat])
    db.flush()
    physiology = Section(exam_id=usmle.id, name="Physiology")
    pharmacology = Section(exam_id=usmle.id, name="Pharmacology")
    sat_math = Section(exam_id=sat.id, name="Math")
    db.add_all([physiology, pharmacology, sat_math])
    db.flush()

    def make_test(exam, name, time_limit=60, **fields):
        test = Test(exam_id=exam.id, name=name, time_limit_minutes=time_limit, question_count=3, is_active=True, **fields)
        db.add(test)
        db.flush()
        return test

    single_block = []
    for name in ("Practice Test 1", "Practice Test 2", "Other 1"):
        test = make_test(usmle, name)
        for order in range(1, 4):
            _add_question(db, usmle, physiology, test, order)
        single_block.append(test)
    test1, test2, other = single_block

    blocks = make_test(usmle, "Practice Test 3", time_limit=120)
    block1 = TestSection(test_id=blocks.id, section_id=physiology.id, section_order=1, question_count=2,
                         name="Block 1", time_limit_minutes=60)
    block2 = TestSection(test_id=blocks.id, section_id=pharmacology.id, section_order=2, question_count=1,
                         name="Block 2", time_limit_minutes=30)
    db.add_all([block1, block2])
    db.flush()
    _add_question(db, usmle, physiology, blocks, 1, block1)
    _add_question(db, usmle, physiology, blocks, 2, block1)
    _add_question(db, usmle, pharmacology, blocks, 3, block2)

    sat_test = make_test(sat, "SAT Practice 1", time_limit=35,
                         scoring={"sections": {str(sat_math.id): {"0": 200, "1": 500, "2": 800}}})
    _add_question(db, sat, sat_math, sat_test, 1)
    _add_question(db, sat, sat_math, sat_test, 2, question_type="numeric_entry", answer_choices={},
                  correct_answer="3/4", accepted_answers=[".75"])

    package = Package(exam_id=usmle.id, name="Starter", test_count=2, price=49.0, validity_days=30, is_active=True)
    big_package = Package(exam_id=usmle.id, name="Blocks", test_count=5, price=99.0, validity_days=30, is_active=True)
    sat_package = Package(exam_id=sat.id, name="SAT Starter", test_count=1, price=29.0, validity_days=30, is_active=True)
    db.add_all([package, big_package, sat_package])
    db.flush()
    db.add_all([
        PackageTest(package_id=package.id, test_id=test1.id, test_order=1),
        PackageTest(package_id=package.id, test_id=test2.id, test_order=2),
        PackageTest(package_id=big_package.id, test_id=blocks.id, test_order=1),
        PackageTest(package_id=sat_package.id, test_id=sat_test.id, test_order=1),
    ])
    db.commit()
    return {
        "usmle": usmle, "sat": sat,
        "package": package, "big_package": big_package, "sat_package": sat_package,
        "test1": test1, "test2": test2, "other": other, "blocks": blocks, "sat_test": sat_test,
        "sat_math": sat_math,
    }
