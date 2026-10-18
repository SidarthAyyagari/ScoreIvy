import csv
import io
from typing import Dict, Iterable, List, Optional, Set, Tuple

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.models import Exam, Question, Section, User
from app.schemas.schemas import QuestionCreate
from app.services.questions import create_question

CHOICE_COLUMNS = tuple(f"choice_{letter}" for letter in "abcdefghij")
REQUIRED_COLUMNS = frozenset({"question_text", "correct_answer"})
OPTIONAL_COLUMNS = frozenset(
    {
        *CHOICE_COLUMNS,
        "exam",
        "section_id",
        "question_type",
        "accepted_answers",
        "tags",
        "image_url",
        "explanation",
        "difficulty",
        "status",  # active (default) or archived
        "id",  # Written by export for reference; ignored on import (rows are always added as new questions)
    }
)
EXPORT_COLUMNS = (
    "id", "exam", "section_id", "question_type", "question_text", *CHOICE_COLUMNS,
    "correct_answer", "accepted_answers", "tags", "image_url", "explanation", "difficulty", "status",
)
STATUSES = {"active": True, "archived": False}
ALLOWED_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS
LIST_SEPARATOR = ";"
MAX_ROWS = 10000


class CsvValidationErrorDetail:
    def __init__(self, row: int, message: str, column: Optional[str] = None):
        self.row = row
        self.message = message
        self.column = column

    def to_dict(self) -> dict:
        payload = {"row": self.row, "message": self.message}
        if self.column is not None:
            payload["column"] = self.column
        return payload


def _normalize_header(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _is_blank_row(row: dict) -> bool:
    return not any((value or "").strip() for value in row.values())


def _split_list(raw: str) -> List[str]:
    return [item.strip() for item in (raw or "").split(LIST_SEPARATOR) if item.strip()]


def _build_answer_choices(row: dict) -> Dict[str, str]:
    choices: Dict[str, str] = {}
    for index, column in enumerate(CHOICE_COLUMNS):
        raw = (row.get(column) or "").strip()
        if raw:
            choices[chr(ord("A") + index)] = raw
    return choices


def _resolve_exam(raw: str, exams_by_key: Dict[str, int]) -> Optional[int]:
    """``exam`` column accepts an exam slug (``usmle-step-1``) or numeric id."""
    return exams_by_key.get(raw.strip().lower())


def _format_validation_error(exc: ValidationError) -> List[Tuple[str, Optional[str]]]:
    messages = []
    for error in exc.errors():
        location = error.get("loc") or ()
        column = str(location[0]) if location else None
        message = error.get("msg", "Invalid value").replace("Value error, ", "", 1)
        messages.append((message, column))
    return messages


def parse_and_validate_csv(
    content: str, db: Session, default_exam_id: Optional[int] = None
) -> Tuple[List[QuestionCreate], List[CsvValidationErrorDetail], int]:
    """
    Parse CSV text and validate all rows.
    Returns (valid questions, errors, total_data_rows).
    Row numbers in errors are 1-based CSV line numbers (header is row 1).
    ``default_exam_id`` applies to rows without an ``exam`` column value.
    """
    errors: List[CsvValidationErrorDetail] = []

    if not content.strip():
        errors.append(CsvValidationErrorDetail(0, "CSV file is empty"))
        return [], errors, 0

    try:
        reader = csv.DictReader(io.StringIO(content))
    except csv.Error as exc:
        errors.append(CsvValidationErrorDetail(0, f"Invalid CSV format: {exc}"))
        return [], errors, 0

    if reader.fieldnames is None:
        errors.append(CsvValidationErrorDetail(0, "CSV file has no header row"))
        return [], errors, 0

    normalized_fieldnames = [_normalize_header(name) for name in reader.fieldnames if name]
    if len(normalized_fieldnames) != len(set(normalized_fieldnames)):
        errors.append(CsvValidationErrorDetail(1, "Duplicate column names in header"))
        return [], errors, 0

    header_set = set(normalized_fieldnames)
    unknown = header_set - ALLOWED_COLUMNS
    if unknown:
        errors.append(CsvValidationErrorDetail(1, f"Unknown column(s): {', '.join(sorted(unknown))}"))
    missing = REQUIRED_COLUMNS - header_set
    if missing:
        errors.append(CsvValidationErrorDetail(1, f"Missing required column(s): {', '.join(sorted(missing))}"))
    if errors:
        return [], errors, 0

    reader.fieldnames = normalized_fieldnames

    exams_by_key: Dict[str, int] = {}
    for exam in db.query(Exam).all():
        exams_by_key[exam.slug.lower()] = exam.id
        exams_by_key[str(exam.id)] = exam.id
    existing_section_ids: Set[int] = {row[0] for row in db.query(Section.id).all()}

    valid_questions: List[QuestionCreate] = []
    data_row_count = 0

    for line_number, raw_row in enumerate(reader, start=2):
        row = {key: (value or "") for key, value in raw_row.items() if key}
        if _is_blank_row(row):
            continue

        data_row_count += 1
        if data_row_count > MAX_ROWS:
            errors.append(CsvValidationErrorDetail(line_number, f"CSV exceeds maximum of {MAX_ROWS} data rows"))
            break

        exam_id = default_exam_id
        exam_raw = row.get("exam", "").strip()
        if exam_raw:
            exam_id = _resolve_exam(exam_raw, exams_by_key)
            if exam_id is None:
                errors.append(CsvValidationErrorDetail(line_number, f"Unknown exam '{exam_raw}'", column="exam"))
                continue

        section_id: Optional[int] = None
        section_raw = row.get("section_id", "").strip()
        if section_raw:
            if not section_raw.isdigit() or int(section_raw) not in existing_section_ids:
                errors.append(
                    CsvValidationErrorDetail(line_number, f"section_id {section_raw} does not exist", column="section_id")
                )
                continue
            section_id = int(section_raw)

        status_raw = row.get("status", "").strip().lower() or "active"
        if status_raw not in STATUSES:
            errors.append(CsvValidationErrorDetail(line_number, "status must be active or archived", column="status"))
            continue

        try:
            question = QuestionCreate(
                exam_id=exam_id,
                section_id=section_id,
                question_type=row.get("question_type", "").strip() or "multiple_choice",
                question_text=row.get("question_text", ""),
                image_url=row.get("image_url") or None,
                answer_choices=_build_answer_choices(row),
                correct_answer=row.get("correct_answer", ""),
                accepted_answers=_split_list(row.get("accepted_answers", "")) or None,
                explanation=row.get("explanation") or None,
                difficulty=row.get("difficulty", "").strip() or "medium",
                tags=_split_list(row.get("tags", "")),
                is_active=STATUSES[status_raw],
            )
        except ValidationError as exc:
            for message, column in _format_validation_error(exc):
                errors.append(CsvValidationErrorDetail(line_number, message, column=column))
            continue

        valid_questions.append(question)

    if data_row_count == 0 and not errors:
        errors.append(CsvValidationErrorDetail(0, "CSV contains no question rows"))

    return valid_questions, errors, data_row_count


def import_questions(db: Session, questions: List[QuestionCreate], actor: Optional[User] = None) -> List[Question]:
    created = [create_question(db, question, actor, action="imported") for question in questions]
    db.commit()
    for question in created:
        db.refresh(question)
    return created


def export_questions_csv(questions: Iterable[Question], exam_slugs: Dict[int, str]) -> str:
    """CSV in the import format, so an export can be re-imported as a restore."""
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=EXPORT_COLUMNS)
    writer.writeheader()
    for question in questions:
        row = {
            "id": question.id,
            "exam": exam_slugs.get(question.exam_id, ""),
            "section_id": question.section_id or "",
            "question_type": question.question_type,
            "question_text": question.question_text,
            "correct_answer": question.correct_answer,
            "accepted_answers": LIST_SEPARATOR.join(question.accepted_answers or []),
            "tags": LIST_SEPARATOR.join(f"{t.category}:{t.name}" for t in question.tags),
            "image_url": question.image_url or "",
            "explanation": question.explanation or "",
            "difficulty": question.difficulty or "",
            "status": "active" if question.is_active else "archived",
        }
        for index, column in enumerate(CHOICE_COLUMNS):
            row[column] = (question.answer_choices or {}).get(chr(ord("A") + index), "")
        writer.writerow(row)
    return out.getvalue()
