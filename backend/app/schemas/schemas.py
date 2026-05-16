from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, List, Dict
from datetime import datetime
from app.schemas.question_validators import (
    validate_answer_choices,
    validate_correct_answer,
    validate_difficulty,
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

    section_id: Optional[int] = Field(default=None, gt=0)
    question_text: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    answer_choices: Dict[str, str]  # {"A": "choice text", "B": "choice text", ...}
    correct_answer: str = Field(..., min_length=1)
    explanation: Optional[str] = None
    difficulty: str = "medium"

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

    @field_validator("answer_choices")
    @classmethod
    def validate_answer_choices_field(cls, value: Dict[str, str]) -> Dict[str, str]:
        return validate_answer_choices(value)

    @field_validator("correct_answer")
    @classmethod
    def normalize_correct_answer(cls, value: str) -> str:
        return value.strip().upper()

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
    def validate_correct_answer_in_choices(self) -> "QuestionCreate":
        self.correct_answer = validate_correct_answer(self.correct_answer, self.answer_choices)
        return self


class QuestionResponse(BaseModel):
    id: int
    section_id: Optional[int]
    question_text: str
    image_url: Optional[str]
    answer_choices: Dict[str, str]
    correct_answer: str
    explanation: Optional[str]
    difficulty: str
    created_at: datetime

    class Config:
        from_attributes = True


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
class TestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    time_limit_minutes: int
    question_ids: List[int]  # List of question IDs to include in the test


class TestResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    time_limit_minutes: int
    question_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class TestQuestionResponse(BaseModel):
    id: int
    question_text: str
    image_url: Optional[str]
    answer_choices: Dict[str, str]
    question_order: int

    class Config:
        from_attributes = True


class TestDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    time_limit_minutes: int
    questions: List[TestQuestionResponse]

    class Config:
        from_attributes = True


# Test Attempt Schemas
class QuestionAttemptCreate(BaseModel):
    question_id: int
    selected_answer: Optional[str]
    time_spent_seconds: Optional[int] = None


class TestAttemptCreate(BaseModel):
    test_id: int
    question_attempts: List[QuestionAttemptCreate]


class TestAttemptResponse(BaseModel):
    id: int
    test_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    score: Optional[float]
    total_questions: int
    correct_answers: Optional[int]

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
class PackageResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    test_count: int
    price: float
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


# Package Schemas
class PackageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    test_count: int
    price: float
    is_active: bool = True


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    test_count: Optional[int] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None


# Section Schemas
class SectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SectionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


# Question Update Schema
class QuestionUpdate(BaseModel):
    section_id: Optional[int] = None
    question_text: Optional[str] = None
    image_url: Optional[str] = None
    answer_choices: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    is_active: Optional[bool] = None


# Test Update Schema
class TestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    question_ids: Optional[List[int]] = None  # If provided, will update test questions


# UserPackage Update Schema
class UserPackageUpdate(BaseModel):
    tests_remaining: Optional[int] = None
    expires_at: Optional[datetime] = None


# TestAttempt Update Schema
class TestAttemptUpdate(BaseModel):
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    correct_answers: Optional[int] = None


# QuestionAttempt Update Schema
class QuestionAttemptUpdate(BaseModel):
    selected_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    time_spent_seconds: Optional[int] = None


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

