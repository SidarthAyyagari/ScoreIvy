from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AdminUserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class AdminUserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    picture: Optional[str]
    oauth_provider: Optional[str]
    oauth_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True


class AdminPackageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    test_count: int = Field(..., gt=0)
    price: float = Field(..., ge=0)
    is_active: bool = True


class AdminPackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    test_count: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class AdminPackageResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    test_count: int
    price: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminPackageTestCreate(BaseModel):
    package_id: int
    test_id: int
    test_order: int = Field(..., ge=1)


class AdminPackageTestUpdate(BaseModel):
    package_id: Optional[int] = None
    test_id: Optional[int] = None
    test_order: Optional[int] = Field(None, ge=1)


class AdminPackageTestResponse(BaseModel):
    id: int
    package_id: int
    test_id: int
    test_order: int

    class Config:
        from_attributes = True


class AdminUserPackageCreate(BaseModel):
    user_id: int
    package_id: int
    tests_remaining: int = Field(..., ge=0)
    expires_at: Optional[datetime] = None


class AdminUserPackageUpdate(BaseModel):
    user_id: Optional[int] = None
    package_id: Optional[int] = None
    tests_remaining: Optional[int] = Field(None, ge=0)
    expires_at: Optional[datetime] = None


class AdminUserPackageResponse(BaseModel):
    id: int
    user_id: int
    package_id: int
    tests_remaining: int
    purchased_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class AdminTestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    time_limit_minutes: int = Field(..., gt=0)
    question_count: int = Field(..., ge=0)
    is_active: bool = True


class AdminTestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, gt=0)
    question_count: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class AdminTestResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    time_limit_minutes: int
    question_count: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class AdminTestSectionCreate(BaseModel):
    test_id: int
    section_id: int
    section_order: int = Field(..., ge=1)
    question_count: int = Field(..., ge=0)


class AdminTestSectionUpdate(BaseModel):
    test_id: Optional[int] = None
    section_id: Optional[int] = None
    section_order: Optional[int] = Field(None, ge=1)
    question_count: Optional[int] = Field(None, ge=0)


class AdminTestSectionResponse(BaseModel):
    id: int
    test_id: int
    section_id: int
    section_order: int
    question_count: int

    class Config:
        from_attributes = True


class AdminTestQuestionCreate(BaseModel):
    test_id: int
    question_id: int
    section_id: int
    question_order: int = Field(..., ge=1)
    section_question_order: int = Field(..., ge=1)


class AdminTestQuestionUpdate(BaseModel):
    test_id: Optional[int] = None
    question_id: Optional[int] = None
    section_id: Optional[int] = None
    question_order: Optional[int] = Field(None, ge=1)
    section_question_order: Optional[int] = Field(None, ge=1)


class AdminTestQuestionResponse(BaseModel):
    id: int
    test_id: int
    question_id: int
    section_id: int
    question_order: int
    section_question_order: int

    class Config:
        from_attributes = True


class AdminTestAttemptCreate(BaseModel):
    user_id: int
    test_id: int
    user_package_id: Optional[int] = None
    total_questions: int = Field(..., gt=0)
    score: Optional[float] = None
    correct_answers: Optional[int] = None
    completed_at: Optional[datetime] = None


class AdminTestAttemptUpdate(BaseModel):
    user_id: Optional[int] = None
    test_id: Optional[int] = None
    user_package_id: Optional[int] = None
    total_questions: Optional[int] = Field(None, gt=0)
    score: Optional[float] = None
    correct_answers: Optional[int] = None
    completed_at: Optional[datetime] = None


class AdminTestAttemptResponse(BaseModel):
    id: int
    user_id: int
    test_id: int
    user_package_id: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    score: Optional[float]
    total_questions: int
    correct_answers: Optional[int]

    class Config:
        from_attributes = True


class AdminQuestionAttemptCreate(BaseModel):
    test_attempt_id: int
    question_id: int
    selected_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    time_spent_seconds: Optional[int] = None


class AdminQuestionAttemptUpdate(BaseModel):
    test_attempt_id: Optional[int] = None
    question_id: Optional[int] = None
    selected_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    time_spent_seconds: Optional[int] = None


class AdminQuestionAttemptResponse(BaseModel):
    id: int
    test_attempt_id: int
    question_id: int
    selected_answer: Optional[str]
    is_correct: Optional[bool]
    time_spent_seconds: Optional[int]
    answered_at: datetime

    class Config:
        from_attributes = True


class AdminQuestionResponse(BaseModel):
    id: int
    section_id: Optional[int]
    question_text: str
    image_url: Optional[str]
    answer_choices: Dict[str, str]
    correct_answer: str
    explanation: Optional[str]
    difficulty: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class AdminSectionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True
