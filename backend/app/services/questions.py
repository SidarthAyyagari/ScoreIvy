"""Create/update questions with the same validation and tag handling everywhere
(question API, admin CRUD, CSV import)."""

from typing import List

from sqlalchemy.orm import Session

from app.models.models import Exam, Question, Section, Tag
from app.schemas.question_validators import (
    parse_tag,
    validate_difficulty,
    validate_question_content,
    validate_question_type,
)
from app.schemas.schemas import QuestionCreate


class QuestionInputError(ValueError):
    pass


def _check_references(db: Session, exam_id, section_id) -> None:
    if exam_id is not None and not db.get(Exam, exam_id):
        raise QuestionInputError(f"Exam {exam_id} not found")
    if section_id is not None and not db.get(Section, section_id):
        raise QuestionInputError(f"Section {section_id} not found")


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


def create_question(db: Session, payload: QuestionCreate) -> Question:
    """Add a validated question (and its tags) to the session. Caller commits."""
    _check_references(db, payload.exam_id, payload.section_id)
    question = Question(**payload.column_values())
    db.add(question)
    db.flush()
    if payload.tags:
        set_question_tags(db, question, payload.tags)
    return question


def update_question(db: Session, question: Question, data: dict) -> Question:
    """Apply a partial update, then re-validate the answer fields as a whole. Caller commits."""
    tags = data.pop("tags", None)
    data = {key: value for key, value in data.items() if value is not None or key == "accepted_answers"}

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
    return question
