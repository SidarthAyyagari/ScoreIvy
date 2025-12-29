from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime


# Question Schemas
class AnswerChoice(BaseModel):
    choice: str  # e.g., "A", "B", "C", "D"
    text: str


class QuestionCreate(BaseModel):
    section_id: Optional[int] = None
    question_text: str
    image_url: Optional[str] = None
    answer_choices: Dict[str, str]  # {"A": "choice text", "B": "choice text", ...}
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str = "medium"


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
    username: str
    is_active: bool
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

