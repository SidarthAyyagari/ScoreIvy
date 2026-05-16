import csv
import io
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from app.models.models import Question, Section
from app.schemas.schemas import QuestionCreate

REQUIRED_COLUMNS = frozenset({"question_text", "correct_answer", "choice_a", "choice_b"})
OPTIONAL_COLUMNS = frozenset(
    {
        "choice_c",
        "choice_d",
        "choice_e",
        "choice_f",
        "section_id",
        "image_url",
        "explanation",
        "difficulty",
    }
)
ALLOWED_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS
CHOICE_COLUMNS = ("choice_a", "choice_b", "choice_c", "choice_d", "choice_e", "choice_f")
VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})
MAX_ROWS = 2000


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


def _parse_section_id(raw: str, row_number: int, errors: List[CsvValidationErrorDetail]) -> Optional[int]:
    value = raw.strip()
    if not value:
        return None
    try:
        section_id = int(value)
    except ValueError:
        errors.append(
            CsvValidationErrorDetail(
                row_number, "section_id must be an integer", column="section_id"
            )
        )
        return None
    if section_id <= 0:
        errors.append(
            CsvValidationErrorDetail(
                row_number, "section_id must be a positive integer", column="section_id"
            )
        )
    return section_id


def _build_answer_choices(row: dict, row_number: int, errors: List[CsvValidationErrorDetail]) -> Optional[Dict[str, str]]:
    choices: Dict[str, str] = {}
    for index, column in enumerate(CHOICE_COLUMNS):
        raw = (row.get(column) or "").strip()
        if not raw:
            continue
        letter = chr(ord("A") + index)
        choices[letter] = raw

    if len(choices) < 2:
        errors.append(
            CsvValidationErrorDetail(
                row_number,
                "At least two answer choices are required (non-empty choice_a and choice_b, etc.)",
            )
        )
        return None
    return choices


def parse_and_validate_csv(
    content: str, db: Session
) -> Tuple[List[QuestionCreate], List[CsvValidationErrorDetail], int]:
    """
    Parse CSV text and validate all rows.
    Returns (valid questions, errors, total_data_rows).
    Row numbers in errors are 1-based CSV line numbers (header is row 1).
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
        errors.append(
            CsvValidationErrorDetail(
                1,
                f"Unknown column(s): {', '.join(sorted(unknown))}",
            )
        )

    missing = REQUIRED_COLUMNS - header_set
    if missing:
        errors.append(
            CsvValidationErrorDetail(
                1,
                f"Missing required column(s): {', '.join(sorted(missing))}",
            )
        )

    if errors:
        return [], errors, 0

    reader.fieldnames = normalized_fieldnames

    section_ids: Set[int] = set()
    parsed_rows: List[Tuple[int, dict]] = []
    data_row_count = 0

    for line_number, raw_row in enumerate(reader, start=2):
        row = {key: (value or "") for key, value in raw_row.items()}
        if _is_blank_row(row):
            continue

        data_row_count += 1
        if data_row_count > MAX_ROWS:
            errors.append(
                CsvValidationErrorDetail(
                    line_number, f"CSV exceeds maximum of {MAX_ROWS} data rows"
                )
            )
            break

        parsed_rows.append((line_number, row))
        section_raw = row.get("section_id", "").strip()
        if section_raw:
            section_id = _parse_section_id(section_raw, line_number, errors)
            if section_id is not None:
                section_ids.add(section_id)

    if errors:
        return [], errors, data_row_count

    existing_section_ids: Set[int] = set()
    if section_ids:
        rows = db.query(Section.id).filter(Section.id.in_(section_ids)).all()
        existing_section_ids = {row[0] for row in rows}

    valid_questions: List[QuestionCreate] = []

    for line_number, row in parsed_rows:
        question_text = row.get("question_text", "").strip()
        if not question_text:
            errors.append(
                CsvValidationErrorDetail(
                    line_number, "question_text is required", column="question_text"
                )
            )
            continue

        answer_choices = _build_answer_choices(row, line_number, errors)
        if answer_choices is None:
            continue

        correct_answer = row.get("correct_answer", "").strip().upper()
        if not correct_answer:
            errors.append(
                CsvValidationErrorDetail(
                    line_number, "correct_answer is required", column="correct_answer"
                )
            )
            continue
        if correct_answer not in answer_choices:
            errors.append(
                CsvValidationErrorDetail(
                    line_number,
                    f"correct_answer '{correct_answer}' is not among provided choices "
                    f"({', '.join(sorted(answer_choices.keys()))})",
                    column="correct_answer",
                )
            )
            continue

        section_id: Optional[int] = None
        section_raw = row.get("section_id", "").strip()
        if section_raw:
            section_id = _parse_section_id(section_raw, line_number, errors)
            if section_id is None:
                continue
            if section_id not in existing_section_ids:
                errors.append(
                    CsvValidationErrorDetail(
                        line_number,
                        f"section_id {section_id} does not exist",
                        column="section_id",
                    )
                )
                continue

        difficulty = row.get("difficulty", "").strip().lower() or "medium"
        if difficulty not in VALID_DIFFICULTIES:
            errors.append(
                CsvValidationErrorDetail(
                    line_number,
                    f"difficulty must be one of: {', '.join(sorted(VALID_DIFFICULTIES))}",
                    column="difficulty",
                )
            )
            continue

        image_url = row.get("image_url", "").strip() or None
        explanation = row.get("explanation", "").strip() or None

        valid_questions.append(
            QuestionCreate(
                section_id=section_id,
                question_text=question_text,
                image_url=image_url,
                answer_choices=answer_choices,
                correct_answer=correct_answer,
                explanation=explanation,
                difficulty=difficulty,
            )
        )

    if data_row_count == 0 and not errors:
        errors.append(CsvValidationErrorDetail(0, "CSV contains no question rows"))

    return valid_questions, errors, data_row_count


def import_questions(db: Session, questions: List[QuestionCreate]) -> List[Question]:
    created: List[Question] = []
    for question in questions:
        db_question = Question(**question.model_dump())
        db.add(db_question)
        created.append(db_question)
    db.commit()
    for question in created:
        db.refresh(question)
    return created
