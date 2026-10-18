from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, List, Dict
from datetime import datetime
from app.schemas.question_validators import (
    parse_tag,
    validate_difficulty,
    validate_question_content,
    validate_question_type,
)


# Question Schemas
class AnswerChoice(BaseModel):
    choice: str  # e.g., "A", "B", "C", "D"
    text: str


class QuestionCreate(BaseModel):
    """Request body for creating one MCQ question (``POST /api/questions/``).

    Validators normalize strings and reject invalid choice keys, counts, and
    difficulty before the route handler persists to the database.
    """

    exam_id: Optional[int] = Field(default=None, gt=0)
    section_id: Optional[int] = Field(default=None, gt=0)
    question_type: str = "multiple_choice"
    question_text: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    answer_choices: Dict[str, str] = {}  # {"A": "choice text", ...}; empty for numeric_entry
    correct_answer: str = Field(..., min_length=1)
    accepted_answers: Optional[List[str]] = None  # numeric_entry alternatives, e.g. [".75"]
    explanation: Optional[str] = None
    difficulty: str = "medium"
    tags: List[str] = []  # "category:name", e.g. "system:Cardiovascular"
    is_active: bool = True  # False imports the question as archived

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question_text must not be empty")
        return stripped

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("question_type")
    @classmethod
    def validate_question_type_field(cls, value: str) -> str:
        return validate_question_type(value)

    @field_validator("correct_answer")
    @classmethod
    def normalize_correct_answer(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: List[str]) -> List[str]:
        return [parse_tag(tag) for tag in value if tag and tag.strip()]

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty_field(cls, value: str) -> str:
        return validate_difficulty(value)

    @field_validator("explanation")
    @classmethod
    def validate_explanation(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_answers_for_type(self) -> "QuestionCreate":
        self.answer_choices, self.correct_answer, self.accepted_answers = validate_question_content(
            self.question_type, self.answer_choices, self.correct_answer, self.accepted_answers
        )
        return self

    def column_values(self) -> dict:
        """Fields that map directly onto ``Question`` columns (tags are stored separately)."""
        return self.model_dump(exclude={"tags"})


class QuestionResponse(BaseModel):
    id: int
    exam_id: Optional[int] = None
    section_id: Optional[int]
    question_type: str = "multiple_choice"
    question_text: str
    image_url: Optional[str]
    answer_choices: Dict[str, str]
    correct_answer: str
    accepted_answers: Optional[List[str]] = None
    explanation: Optional[str]
    difficulty: str
    created_at: datetime
    is_active: bool = True
    tags: List[str] = []

    @field_validator("tags", mode="before")
    @classmethod
    def tags_as_labels(cls, value) -> List[str]:
        return [tag if isinstance(tag, str) else f"{tag.category}:{tag.name}" for tag in value or []]

    class Config:
        from_attributes = True


class QuestionPage(BaseModel):
    items: List[QuestionResponse]
    total: int


class QuestionUsage(BaseModel):
    tests: List[Dict[str, object]]
    attempt_count: int  # Attempts that were served this question; > 0 means delete archives instead


class QuestionDetailResponse(QuestionResponse):
    usage: QuestionUsage


class QuestionRevisionResponse(BaseModel):
    id: int
    question_id: int
    action: str
    snapshot: Dict[str, object]
    note: Optional[str]
    changed_by_email: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionRemoveResponse(BaseModel):
    result: str  # "deleted" (never served, gone for good) or "archived" (kept for past results)


class QuestionsBulkCreate(BaseModel):
    questions: List[QuestionCreate]


class CsvValidationErrorItem(BaseModel):
    row: int
    message: str
    column: Optional[str] = None


class CsvUploadErrorResponse(BaseModel):
    success: bool = False
    total_rows: int
    error_count: int
    errors: List[CsvValidationErrorItem]
    message: str = "CSV validation failed"


class CsvUploadSuccessResponse(BaseModel):
    success: bool = True
    imported_count: int
    total_rows: int
    questions: List[QuestionResponse]


# Test Schemas
class TestResponse(BaseModel):
    id: int
    exam_id: Optional[int] = None
    name: str
    description: Optional[str]
    time_limit_minutes: int
    question_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AvailableTestResponse(TestResponse):
    in_progress_attempt_id: Optional[int] = None
    section_count: int = 1


# Test Attempt Schemas
class QuestionAttemptCreate(BaseModel):
    question_id: int
    selected_answer: Optional[str] = Field(default=None, max_length=16)
    time_spent_seconds: Optional[int] = Field(default=None, ge=0, le=24 * 60 * 60)


class SectionSubmit(BaseModel):
    """Final answers for the active section (``POST /api/tests/attempts/{id}/sections/{order}/submit``)."""

    question_attempts: List[QuestionAttemptCreate] = []


class TestAttemptResponse(BaseModel):
    id: int
    test_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    score: Optional[float]
    total_questions: int
    correct_answers: Optional[int]
    scaled_score: Optional[int] = None
    section_scores: Optional[List[dict]] = None

    class Config:
        from_attributes = True


# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    picture: Optional[str]
    is_active: bool
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# Package Schemas
class ExamResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: Optional[str]
    tools: List[str] = []
    display_order: int = 0

    class Config:
        from_attributes = True


class PackageResponse(BaseModel):
    id: int
    exam_id: Optional[int] = None
    name: str
    description: Optional[str]
    test_count: int
    price: float
    validity_days: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class UserPackageResponse(BaseModel):
    id: int
    package_id: int
    tests_remaining: int
    purchased_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    checkout_url: Optional[str] = None  # Redirect here to pay
    user_package_id: Optional[int] = None  # Set when granted without payment (dev only)


class OrderResponse(BaseModel):
    id: int
    package_id: int
    status: str
    amount_cents: int
    currency: str
    created_at: datetime
    paid_at: Optional[datetime]
    refunded_at: Optional[datetime]

    class Config:
        from_attributes = True


# Package Schemas
class PackageCreate(BaseModel):
    exam_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    test_count: int = Field(..., gt=0)
    price: float = Field(..., ge=0)
    validity_days: Optional[int] = Field(default=180, gt=0)  # None = credits never expire
    is_active: bool = True


class PackageUpdate(BaseModel):
    exam_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    test_count: Optional[int] = Field(default=None, gt=0)
    price: Optional[float] = Field(default=None, ge=0)
    validity_days: Optional[int] = Field(default=None, gt=0)
    is_active: Optional[bool] = None


# Section Schemas
class SectionCreate(BaseModel):
    exam_id: Optional[int] = None
    name: str
    description: Optional[str] = None


class SectionUpdate(BaseModel):
    exam_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None


class SectionResponse(BaseModel):
    id: int
    exam_id: Optional[int] = None
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


# Question Update Schema
class QuestionUpdate(BaseModel):
    exam_id: Optional[int] = None
    section_id: Optional[int] = None
    question_type: Optional[str] = None
    question_text: Optional[str] = None
    image_url: Optional[str] = None
    answer_choices: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    accepted_answers: Optional[List[str]] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None  # Replaces all tags when provided


class QuestionAttemptResponse(BaseModel):
    id: int
    test_attempt_id: int
    question_id: int
    selected_answer: Optional[str]
    is_correct: Optional[bool]
    time_spent_seconds: Optional[int]
    answered_at: datetime

    class Config:
        from_attributes = True

