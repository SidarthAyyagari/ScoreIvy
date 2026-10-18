from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import logging
import re
from app.db.database import get_db
from app.models.models import Exam, Test, TestAttempt, User, UserPackage, PackageTest
from app.schemas.schemas import (
    TestResponse, TestAttemptResponse, QuestionAttemptCreate, SectionSubmit, AvailableTestResponse,
)
from app.routers.auth import get_current_user
from app.services import exam_session
from app.services.entitlements import is_expired

logger = logging.getLogger(__name__)

router = APIRouter()


def _test_number(name: str) -> int:
    match = re.search(r'\d+', name or "")
    return int(match.group()) if match else 0


def _get_own_attempt(db: Session, attempt_id: int, user: User, lock: bool = False) -> TestAttempt:
    query = db.query(TestAttempt).filter(TestAttempt.id == attempt_id, TestAttempt.user_id == user.id)
    if lock:
        query = query.with_for_update()
    attempt = query.first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Test attempt not found")
    return attempt


def _advance_all_for_user(db: Session, user_id: int) -> None:
    open_attempts = db.query(TestAttempt).filter(
        TestAttempt.user_id == user_id,
        TestAttempt.completed_at.is_(None),
    ).all()
    if any([exam_session.advance(db, attempt) for attempt in open_attempts]):
        db.commit()


@router.get("/", response_model=List[TestResponse])
async def get_tests(
    exam: Optional[str] = Query(None, description="Exam slug to filter by"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get active tests (metadata only), optionally for one exam."""
    query = db.query(Test).filter(Test.is_active == True)
    if exam:
        query = query.join(Exam, Test.exam_id == Exam.id).filter(Exam.slug == exam)
    return query.offset(skip).limit(limit).all()


@router.get("/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get test metadata. Questions are only served through an exam session (``/start``)."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test


@router.post("/{test_id}/start")
async def start_test(
    test_id: int,
    user_package_id: int = Query(..., description="User package whose credit pays for this test"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start (or resume) a timed attempt and return the exam session.

    Starting consumes one credit and starts the first section's timer.
    Calling again while the attempt is open resumes it without using another
    credit. Each test can be taken once per user.
    """
    # Serialize starts per user so concurrent requests can't double-spend a credit.
    db.query(User).filter(User.id == current_user.id).with_for_update().one()

    existing = db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id,
        TestAttempt.test_id == test_id,
    ).order_by(TestAttempt.id.desc()).first()
    if existing:
        if exam_session.advance(db, existing):
            db.commit()
        if existing.completed_at is not None:
            raise HTTPException(status_code=409, detail="You have already taken this test")
        return exam_session.session_payload(db, existing)

    user_package = db.query(UserPackage).filter(
        UserPackage.id == user_package_id,
        UserPackage.user_id == current_user.id,
    ).first()
    if not user_package:
        raise HTTPException(status_code=404, detail="User package not found")
    if is_expired(user_package):
        raise HTTPException(status_code=403, detail="This package has expired")
    if user_package.tests_remaining <= 0:
        raise HTTPException(status_code=403, detail="No tests remaining in this package")

    in_package = db.query(PackageTest).filter(
        PackageTest.package_id == user_package.package_id,
        PackageTest.test_id == test_id,
    ).first()
    test = db.query(Test).filter(Test.id == test_id, Test.is_active == True).first()
    if not in_package or not test:
        raise HTTPException(status_code=404, detail="Test not available in this package")

    parts = exam_session.build_parts(db, test)
    if not parts:
        raise HTTPException(status_code=409, detail="This test has no questions yet")

    attempt = exam_session.create_attempt(db, current_user.id, user_package.id, test, parts)
    user_package.tests_remaining -= 1
    db.commit()
    db.refresh(attempt)
    logger.info(f"User {current_user.id} started test {test_id} (attempt {attempt.id})")
    return exam_session.session_payload(db, attempt)


@router.get("/attempts/{attempt_id}/session")
async def get_session(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Current state of an attempt (active section, break, or completed)."""
    attempt = _get_own_attempt(db, attempt_id, current_user)
    if exam_session.advance(db, attempt):
        db.commit()
    return exam_session.session_payload(db, attempt)


@router.put("/attempts/{attempt_id}/answers", status_code=204)
async def save_answer(
    attempt_id: int,
    answer: QuestionAttemptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Autosave one answer in the active section."""
    attempt = _get_own_attempt(db, attempt_id, current_user, lock=True)
    if exam_session.advance(db, attempt):
        db.commit()
    exam_session.save_answer(db, attempt, answer.question_id, answer.selected_answer, answer.time_spent_seconds)
    db.commit()
    return Response(status_code=204)


@router.post("/attempts/{attempt_id}/sections/{section_order}/submit")
async def submit_section(
    attempt_id: int,
    section_order: int,
    submission: SectionSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit and lock the active section. The attempt is graded after the last section."""
    attempt = _get_own_attempt(db, attempt_id, current_user, lock=True)
    if exam_session.advance(db, attempt):
        db.commit()
    exam_session.submit_section(db, attempt, section_order, submission.question_attempts)
    db.commit()
    db.refresh(attempt)
    return exam_session.session_payload(db, attempt)


@router.post("/attempts/{attempt_id}/sections/{section_order}/start")
async def start_section(
    attempt_id: int,
    section_order: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End the break and start the next section's timer."""
    attempt = _get_own_attempt(db, attempt_id, current_user, lock=True)
    if exam_session.advance(db, attempt):
        db.commit()
    exam_session.start_next_section(db, attempt, section_order)
    db.commit()
    db.refresh(attempt)
    return exam_session.session_payload(db, attempt)


@router.get("/attempts/{attempt_id}", response_model=TestAttemptResponse)
async def get_test_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a test attempt by ID (must belong to current user)"""
    attempt = _get_own_attempt(db, attempt_id, current_user)
    if exam_session.advance(db, attempt):
        db.commit()
        db.refresh(attempt)
    return attempt


@router.get("/user-package/{user_package_id}/attempts", response_model=List[TestAttemptResponse])
async def get_user_package_test_attempts(
    user_package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all test attempts for a user package"""
    user_package = db.query(UserPackage).filter(
        UserPackage.id == user_package_id,
        UserPackage.user_id == current_user.id
    ).first()
    if not user_package:
        raise HTTPException(status_code=404, detail="User package not found")

    _advance_all_for_user(db, current_user.id)

    attempts_with_tests = db.query(TestAttempt, Test).join(
        Test, TestAttempt.test_id == Test.id
    ).filter(
        TestAttempt.user_package_id == user_package_id
    ).all()
    attempts_with_tests.sort(key=lambda pair: _test_number(pair[1].name))
    return [attempt for attempt, _ in attempts_with_tests]


@router.get("/user-package/{user_package_id}/available", response_model=List[AvailableTestResponse])
async def get_available_tests_for_package(
    user_package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tests the user can start (or resume) with this package.

    Tests the user has completed through any package are excluded (no retakes).
    Expired or used-up packages only list attempts that are still in progress.
    """
    user_package = db.query(UserPackage).filter(
        UserPackage.id == user_package_id,
        UserPackage.user_id == current_user.id
    ).first()
    if not user_package:
        raise HTTPException(status_code=404, detail="User package not found")

    _advance_all_for_user(db, current_user.id)

    package_test_ids = [
        row[0] for row in db.query(PackageTest.test_id)
        .filter(PackageTest.package_id == user_package.package_id)
        .all()
    ]
    if not package_test_ids:
        return []

    package_tests = db.query(Test).filter(
        Test.id.in_(package_test_ids),
        Test.is_active == True
    ).all()

    user_attempts = db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id,
        TestAttempt.test_id.in_(package_test_ids),
    ).all()
    completed = {a.test_id for a in user_attempts if a.completed_at is not None}
    in_progress: Dict[int, int] = {a.test_id: a.id for a in user_attempts if a.completed_at is None}

    can_start_new = not is_expired(user_package) and user_package.tests_remaining > 0

    available: List[AvailableTestResponse] = []
    for test in package_tests:
        if test.id in completed:
            continue
        attempt_id: Optional[int] = in_progress.get(test.id)
        if attempt_id is None and not can_start_new:
            continue
        item = AvailableTestResponse.model_validate(test)
        item.in_progress_attempt_id = attempt_id
        item.section_count = max(1, len(exam_session.build_parts(db, test)))
        available.append(item)

    available.sort(key=lambda t: _test_number(t.name))
    return available
