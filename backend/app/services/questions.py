"""Create/update questions with the same validation, tag handling, and history everywhere
(question API, admin CRUD, CSV import).

Every change writes a ``QuestionRevision`` with the full question state, so any edit can be
reverted. "Deleting" a question that students have seen archives it instead: it disappears
from tests nobody has started, while past attempts and results keep it.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import (
    Exam, Question, QuestionAttempt, QuestionRevision, Section, Tag, Test, TestAttempt, TestQuestion, User,
)
from app.schemas.question_validators import (
    parse_tag,
    validate_difficulty,
    validate_question_content,
    validate_question_type,
)
from app.schemas.schemas import QuestionCreate

CONTENT_FIELDS = (
    "exam_id", "section_id", "question_type", "question_text", "image_url",
    "answer_choices", "correct_answer", "accepted_answers", "explanation", "difficulty",
)
# Explicit None clears these; for other fields None means "leave unchanged".
NULLABLE_FIELDS = frozenset({"exam_id", "section_id", "image_url", "accepted_answers", "explanation"})


class QuestionInputError(ValueError):
    pass


def _check_references(db: Session, exam_id, section_id) -> None:
    if exam_id is not None and not db.get(Exam, exam_id):
        raise QuestionInputError(f"Exam {exam_id} not found")
    if section_id is not None and not db.get(Section, section_id):
        raise QuestionInputError(f"Section {section_id} not found")


def tag_labels(question: Question) -> List[str]:
    return [f"{tag.category}:{tag.name}" for tag in question.tags]


def snapshot(question: Question) -> dict:
    data = {field: getattr(question, field) for field in CONTENT_FIELDS}
    data["is_active"] = bool(question.is_active)
    data["tags"] = tag_labels(question)
    return data


def record_revision(
    db: Session, question: Question, action: str, actor: Optional[User], note: Optional[str] = None
) -> QuestionRevision:
    revision = QuestionRevision(
        question_id=question.id,
        action=action,
        snapshot=snapshot(question),
        note=note,
        changed_by_user_id=actor.id if actor else None,
        changed_by_email=actor.email if actor else None,
    )
    db.add(revision)
    return revision


def set_question_tags(db: Session, question: Question, tags: List[str]) -> None:
    """Replace a question's tags, creating any ``category:name`` tags that don't exist yet for its exam."""
    resolved: List[Tag] = []
    for raw in tags:
        category, _, name = parse_tag(raw).partition(":")
        tag = (
            db.query(Tag)
            .filter(Tag.exam_id == question.exam_id, Tag.category == category, Tag.name == name)
            .first()
        )
        if tag is None:
            tag = Tag(exam_id=question.exam_id, category=category, name=name)
            db.add(tag)
            db.flush()
        if tag not in resolved:
            resolved.append(tag)
    question.tags = resolved


def create_question(
    db: Session, payload: QuestionCreate, actor: Optional[User] = None, action: str = "created"
) -> Question:
    """Add a validated question (and its tags) to the session. Caller commits."""
    _check_references(db, payload.exam_id, payload.section_id)
    question = Question(**payload.column_values())
    db.add(question)
    db.flush()
    if payload.tags:
        set_question_tags(db, question, payload.tags)
    record_revision(db, question, action, actor)
    return question


def update_question(
    db: Session,
    question: Question,
    data: dict,
    actor: Optional[User] = None,
    action: str = "updated",
    note: Optional[str] = None,
) -> Question:
    """Apply a partial update, then re-validate the answer fields as a whole. Caller commits."""
    data = dict(data)
    tags = data.pop("tags", None)
    data = {key: value for key, value in data.items() if value is not None or key in NULLABLE_FIELDS}

    _check_references(db, data.get("exam_id"), data.get("section_id"))

    question_type = validate_question_type(data.get("question_type", question.question_type))
    switching_type = question_type != question.question_type
    answer_choices = data.get("answer_choices", {} if switching_type else question.answer_choices)
    accepted = data.get("accepted_answers", None if switching_type else question.accepted_answers)
    correct = data.get("correct_answer", question.correct_answer).strip().upper()

    try:
        answer_choices, correct, accepted = validate_question_content(
            question_type, answer_choices, correct, accepted
        )
        if "difficulty" in data:
            data["difficulty"] = validate_difficulty(data["difficulty"])
    except ValueError as exc:
        raise QuestionInputError(str(exc)) from exc

    for key, value in data.items():
        setattr(question, key, value)
    question.question_type = question_type
    question.answer_choices = answer_choices
    question.correct_answer = correct
    question.accepted_answers = accepted

    if tags is not None:
        set_question_tags(db, question, tags)
    db.flush()
    record_revision(db, question, action, actor, note)
    return question


def usage(db: Session, question: Question) -> dict:
    """Which tests include the question and how many attempts have been served it."""
    tests = (
        db.query(Test)
        .join(TestQuestion, TestQuestion.test_id == Test.id)
        .filter(TestQuestion.question_id == question.id)
        .order_by(Test.id)
        .all()
    )
    answered = db.query(QuestionAttempt).filter(QuestionAttempt.question_id == question.id).count()
    served = answered
    if not answered and tests:
        attempts = db.query(TestAttempt).filter(TestAttempt.test_id.in_([t.id for t in tests])).all()
        served = sum(1 for a in attempts if a.question_ids is None or question.id in a.question_ids)
    return {
        "tests": [{"id": t.id, "name": t.name} for t in tests],
        "attempt_count": served,
    }


def set_active(db: Session, question: Question, active: bool, actor: Optional[User] = None) -> Question:
    if bool(question.is_active) != active:
        question.is_active = active
        db.flush()
        record_revision(db, question, "restored" if active else "archived", actor)
    return question


def remove_question(db: Session, question: Question, actor: Optional[User] = None) -> str:
    """Permanently delete a question no student has been served; otherwise archive it.
    Returns ``"deleted"`` or ``"archived"``. Caller commits."""
    if usage(db, question)["attempt_count"]:
        set_active(db, question, False, actor)
        return "archived"
    record_revision(db, question, "deleted", actor)
    db.query(TestQuestion).filter(TestQuestion.question_id == question.id).delete(synchronize_session=False)
    question.tags = []
    db.flush()
    db.delete(question)
    return "deleted"


def revert_question(
    db: Session, question: Question, revision: QuestionRevision, actor: Optional[User] = None
) -> Question:
    """Restore the question's content (not its archived status) to an earlier revision. Caller commits."""
    if revision.question_id != question.id:
        raise QuestionInputError("That revision belongs to a different question")
    data = {field: revision.snapshot.get(field) for field in CONTENT_FIELDS}
    data["tags"] = revision.snapshot.get("tags") or []
    if not data.get("difficulty"):
        data.pop("difficulty")
    return update_question(db, question, data, actor, action="reverted", note=f"Reverted to revision {revision.id}")
