"""Server-side state machine for a timed, sectioned exam attempt.

A test is split into parts (USMLE blocks, SAT modules) from its ``test_sections``;
a test without sections is one part using the test's own time limit. Each part
is timed separately, only the active part's questions are served, and a part
is locked once submitted or once its deadline (plus grace) passes.

Between parts the student may take a break. With ``Test.break_pool_minutes`` set
(USMLE Step 1) every break draws from one shared budget; otherwise each part's
``TestSection.break_after_minutes`` applies (SAT: 10 after Reading and Writing,
0 between modules), defaulting to ``EXAM_MAX_BREAK_MINUTES``. When the allowed
break runs out the next part starts on its own, as on test day.
"""

import math
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import EXAM_MAX_BREAK_MINUTES, EXAM_SUBMIT_GRACE_SECONDS
from app.models.models import (
    AttemptSection, Exam, Question, QuestionAttempt, Section, Test, TestAttempt, TestQuestion, TestSection,
)
from app.schemas.question_validators import (
    NUMERIC_ENTRY,
    is_answer_correct,
    normalize_numeric_answer,
)
from app.services.entitlements import as_aware, utcnow

GRACE = timedelta(seconds=EXAM_SUBMIT_GRACE_SECONDS)
MAX_BREAK = timedelta(minutes=EXAM_MAX_BREAK_MINUTES)


@dataclass
class Part:
    order: int
    test_section_id: Optional[int]
    name: str
    time_limit_minutes: int
    questions: List[Tuple[TestQuestion, Question]] = field(default_factory=list)


def build_parts(db: Session, test: Test, attempt: Optional[TestAttempt] = None) -> List[Part]:
    """Split a test into timed parts. Without an attempt (starting fresh) archived questions are
    left out; with one, exactly the questions that attempt started with are used."""
    query = (
        db.query(TestQuestion, Question)
        .join(Question, TestQuestion.question_id == Question.id)
        .filter(TestQuestion.test_id == test.id)
    )
    if attempt is None:
        query = query.filter(Question.is_active == True)  # noqa: E712
    elif attempt.question_ids is not None:
        query = query.filter(Question.id.in_(attempt.question_ids))
    rows = query.order_by(TestQuestion.question_order).all()
    if not rows:
        return []

    test_sections = (
        db.query(TestSection)
        .filter(TestSection.test_id == test.id)
        .order_by(TestSection.section_order)
        .all()
    )
    if not test_sections:
        return [Part(1, None, test.name, test.time_limit_minutes, rows)]

    by_test_section: Dict[int, list] = {ts.id: [] for ts in test_sections}
    first_for_subject: Dict[int, int] = {}
    for ts in test_sections:
        first_for_subject.setdefault(ts.section_id, ts.id)
    for test_question, question in rows:
        target = test_question.test_section_id
        if target not in by_test_section:
            target = first_for_subject.get(test_question.section_id, test_sections[0].id)
        by_test_section[target].append((test_question, question))

    subject_names = {
        s.id: s.name for s in db.query(Section).filter(Section.id.in_({ts.section_id for ts in test_sections}))
    }
    parts: List[Part] = []
    for ts in test_sections:
        questions = by_test_section[ts.id]
        if not questions:
            continue
        time_limit = ts.time_limit_minutes or max(
            1, math.ceil(test.time_limit_minutes * len(questions) / len(rows))
        )
        name = ts.name or subject_names.get(ts.section_id) or f"Section {ts.section_order}"
        parts.append(Part(len(parts) + 1, ts.id, name, time_limit, questions))
    return parts


def _part_for(section: AttemptSection, parts: List[Part]) -> Optional[Part]:
    for part in parts:
        if part.test_section_id == section.test_section_id and part.test_section_id is not None:
            return part
    for part in parts:
        if part.order == section.section_order:
            return part
    return None


def create_attempt(db: Session, user_id: int, user_package_id: int, test: Test, parts: List[Part]) -> TestAttempt:
    """New attempt with one AttemptSection per part; the first part starts now. Caller commits."""
    now = utcnow()
    attempt = TestAttempt(
        user_id=user_id,
        test_id=test.id,
        user_package_id=user_package_id,
        started_at=now,
        total_questions=sum(len(p.questions) for p in parts),
        question_ids=[question.id for part in parts for _, question in part.questions],
    )
    db.add(attempt)
    db.flush()
    for part in parts:
        db.add(AttemptSection(
            test_attempt_id=attempt.id,
            test_section_id=part.test_section_id,
            section_order=part.order,
            name=part.name,
            time_limit_minutes=part.time_limit_minutes,
        ))
    db.flush()
    db.refresh(attempt)
    _start_section(attempt.sections[0], now)
    return attempt


def _start_section(section: AttemptSection, now) -> None:
    section.started_at = now
    section.deadline_at = now + timedelta(minutes=section.time_limit_minutes)


def current_section(attempt: TestAttempt) -> Optional[AttemptSection]:
    for section in attempt.sections:
        if section.completed_at is None:
            return section
    return None


def window_open(section: AttemptSection) -> bool:
    deadline = as_aware(section.deadline_at)
    return section.started_at is not None and deadline is not None and utcnow() <= deadline + GRACE


def _break_used(attempt: TestAttempt) -> timedelta:
    used = timedelta(0)
    previous: Optional[AttemptSection] = None
    for section in attempt.sections:
        if previous is not None and section.started_at is not None and previous.completed_at is not None:
            used += max(timedelta(0), as_aware(section.started_at) - as_aware(previous.completed_at))
        previous = section
    return used


def break_allowance(db: Session, attempt: TestAttempt, section: AttemptSection) -> Tuple[timedelta, str]:
    """Break the student may take before ``section`` starts, and whether it is a shared ``pool``
    or a fixed ``scheduled`` break."""
    pool = attempt.test.break_pool_minutes
    if pool is not None:
        return max(timedelta(0), timedelta(minutes=pool) - _break_used(attempt)), "pool"
    previous = next((s for s in attempt.sections if s.section_order == section.section_order - 1), None)
    test_section = db.get(TestSection, previous.test_section_id) if previous and previous.test_section_id else None
    if test_section is not None and test_section.break_after_minutes is not None:
        return timedelta(minutes=test_section.break_after_minutes), "scheduled"
    return MAX_BREAK, "scheduled"


def _break_ends_at(db: Session, attempt: TestAttempt, section: AttemptSection):
    previous = next((s for s in attempt.sections if s.section_order == section.section_order - 1), None)
    started = as_aware(previous.completed_at) if previous else as_aware(attempt.started_at)
    allowance, kind = break_allowance(db, attempt, section)
    return started + allowance, kind


def advance(db: Session, attempt: TestAttempt) -> bool:
    """Apply timeouts: lock sections past their deadline and start the next section when its
    break runs out. Grades the attempt once every section is done. Returns True if anything changed.
    """
    if attempt.completed_at is not None:
        return False
    if not attempt.sections:
        finalize(db, attempt)
        return True
    now = utcnow()
    changed = False
    for section in attempt.sections:
        if section.completed_at is not None:
            continue
        if section.started_at is None:
            starts_at, _ = _break_ends_at(db, attempt, section)
            if now < starts_at:
                break
            _start_section(section, starts_at)
            changed = True
        if window_open(section):
            break
        section.completed_at = section.deadline_at
        changed = True

    if changed:
        db.flush()
    if current_section(attempt) is None:
        finalize(db, attempt)
        return True
    return changed


def _existing_answers(db: Session, attempt: TestAttempt) -> Dict[int, QuestionAttempt]:
    db.flush()  # sessions don't autoflush; include answers recorded earlier in this request
    return {
        qa.question_id: qa
        for qa in db.query(QuestionAttempt).filter(QuestionAttempt.test_attempt_id == attempt.id)
    }


def _normalize_selection(question: Question, selected: Optional[str]) -> Optional[str]:
    value = (selected or "").strip()
    if not value:
        return None
    if question.question_type == NUMERIC_ENTRY:
        try:
            return normalize_numeric_answer(value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    value = value.upper()
    if value not in (question.answer_choices or {}):
        raise HTTPException(status_code=400, detail=f"Invalid answer for question {question.id}")
    return value


def _record_answer(
    db: Session,
    attempt: TestAttempt,
    rows: Dict[int, QuestionAttempt],
    question: Question,
    selected: Optional[str],
    time_spent_seconds: Optional[int],
) -> None:
    normalized = _normalize_selection(question, selected)
    row = rows.get(question.id)
    if row is None:
        row = QuestionAttempt(test_attempt_id=attempt.id, question_id=question.id)
        db.add(row)
        rows[question.id] = row
    row.selected_answer = normalized
    if time_spent_seconds is not None:
        row.time_spent_seconds = time_spent_seconds


def _require_active(attempt: TestAttempt, section_order: Optional[int] = None) -> AttemptSection:
    section = current_section(attempt)
    if attempt.completed_at is not None or section is None:
        raise HTTPException(status_code=409, detail="This test has already been submitted")
    if section.started_at is None or not window_open(section):
        raise HTTPException(status_code=409, detail="This section is not in progress")
    if section_order is not None and section.section_order != section_order:
        raise HTTPException(status_code=409, detail="This section is not in progress")
    return section


def save_answer(db: Session, attempt: TestAttempt, question_id: int, selected, time_spent_seconds) -> None:
    section = _require_active(attempt)
    part = _part_for(section, build_parts(db, attempt.test, attempt))
    question = next((q for _, q in (part.questions if part else []) if q.id == question_id), None)
    if question is None:
        raise HTTPException(status_code=400, detail="Question is not part of the current section")
    rows = {k: v for k, v in _existing_answers(db, attempt).items() if k == question_id}
    _record_answer(db, attempt, rows, question, selected, time_spent_seconds)


def submit_section(db: Session, attempt: TestAttempt, section_order: int, answers: Iterable) -> None:
    """Lock the active section with its final answers; grades the attempt after the last one."""
    section = _require_active(attempt, section_order)
    part = _part_for(section, build_parts(db, attempt.test, attempt))
    questions = {q.id: q for _, q in (part.questions if part else [])}
    rows = _existing_answers(db, attempt)
    for answer in answers:
        question = questions.get(answer.question_id)
        if question is not None:
            _record_answer(db, attempt, rows, question, answer.selected_answer, answer.time_spent_seconds)
    section.completed_at = utcnow()
    advance(db, attempt)


def start_next_section(db: Session, attempt: TestAttempt, section_order: int) -> None:
    section = current_section(attempt)
    if attempt.completed_at is not None or section is None:
        raise HTTPException(status_code=409, detail="This test has already been submitted")
    if section.started_at is not None or section.section_order != section_order:
        raise HTTPException(status_code=409, detail="That section cannot be started now")
    _start_section(section, utcnow())


def _scale_lookup(table: Optional[dict], raw: int) -> Optional[int]:
    if not table:
        return None
    points = sorted((int(k), int(v)) for k, v in table.items())
    eligible = [value for key, value in points if key <= raw]
    return eligible[-1] if eligible else points[0][1]


def finalize(db: Session, attempt: TestAttempt) -> None:
    """Grade every question in the test, compute section and scaled scores, mark complete."""
    now = utcnow()
    for section in attempt.sections:
        if section.completed_at is None:
            section.completed_at = now

    test = attempt.test
    parts = build_parts(db, test, attempt)
    rows = _existing_answers(db, attempt)
    subject_totals: Dict[Optional[int], List[int]] = {}
    correct_count = 0
    total = 0
    for part in parts:
        for _, question in part.questions:
            total += 1
            row = rows.get(question.id)
            if row is None:
                row = QuestionAttempt(test_attempt_id=attempt.id, question_id=question.id, selected_answer=None)
                db.add(row)
                rows[question.id] = row
            row.is_correct = is_answer_correct(
                question.question_type, row.selected_answer, question.correct_answer, question.accepted_answers
            )
            correct_count += int(row.is_correct)
            bucket = subject_totals.setdefault(question.section_id, [0, 0])
            bucket[0] += int(row.is_correct)
            bucket[1] += 1

    scoring = test.scoring or {}
    section_tables = scoring.get("sections") or {}
    subject_names = {
        s.id: s.name for s in db.query(Section).filter(Section.id.in_([k for k in subject_totals if k]))
    }
    section_scores = []
    for subject_id, (correct, count) in subject_totals.items():
        if subject_id is None:
            continue
        section_scores.append({
            "section_id": subject_id,
            "name": subject_names.get(subject_id, "Section"),
            "correct": correct,
            "total": count,
            "scaled": _scale_lookup(section_tables.get(str(subject_id)), correct),
        })

    scaled = _scale_lookup(scoring.get("overall"), correct_count)
    if scaled is None and section_scores and all(s["scaled"] is not None for s in section_scores):
        scaled = sum(s["scaled"] for s in section_scores)

    attempt.total_questions = total
    attempt.correct_answers = correct_count
    attempt.score = (correct_count / total * 100) if total else 0
    attempt.section_scores = section_scores
    attempt.scaled_score = scaled
    attempt.completed_at = now


def session_payload(db: Session, attempt: TestAttempt) -> dict:
    test = attempt.test
    exam = db.get(Exam, test.exam_id) if test.exam_id else None
    parts = build_parts(db, test, attempt)
    active = current_section(attempt)
    now = utcnow()

    sections = []
    for section in attempt.sections:
        part = _part_for(section, parts)
        if section.completed_at is not None:
            status = "completed"
        elif section.started_at is not None:
            status = "active"
        else:
            status = "pending"
        sections.append({
            "order": section.section_order,
            "name": section.name,
            "question_count": len(part.questions) if part else 0,
            "time_limit_minutes": section.time_limit_minutes,
            "status": status,
        })

    payload = {
        "attempt_id": attempt.id,
        "status": "completed",
        "test": {
            "id": test.id,
            "name": test.name,
            "description": test.description,
            "exam": {"id": exam.id, "slug": exam.slug, "name": exam.name, "tools": exam.tools or []} if exam else None,
        },
        "sections": sections,
        "current_section": None,
        "next_section": None,
    }
    if attempt.completed_at is not None or active is None:
        return payload

    if active.started_at is None:
        starts_at, kind = _break_ends_at(db, attempt, active)
        payload["status"] = "between_sections"
        payload["next_section"] = {
            **sections[active.section_order - 1],
            "break_seconds_remaining": max(0, int((starts_at - now).total_seconds())),
            "break_kind": kind,
        }
        return payload

    part = _part_for(active, parts)
    question_ids = {q.id for _, q in (part.questions if part else [])}
    saved = {
        qa.question_id: qa.selected_answer
        for qa in _existing_answers(db, attempt).values()
        if qa.selected_answer and qa.question_id in question_ids
    }
    deadline = as_aware(active.deadline_at)
    payload["status"] = "in_section"
    payload["current_section"] = {
        "order": active.section_order,
        "name": active.name,
        "deadline_at": deadline,
        "seconds_remaining": max(0, int((deadline - now).total_seconds())),
        "questions": [
            {
                "id": question.id,
                "question_type": question.question_type,
                "question_text": question.question_text,
                "image_url": question.image_url,
                "answer_choices": question.answer_choices or {},
                "question_order": test_question.question_order,
            }
            for test_question, question in (part.questions if part else [])
        ],
        "saved_answers": saved,
    }
    return payload
