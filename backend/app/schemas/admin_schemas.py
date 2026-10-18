from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class AdminExamCreate(BaseModel):
    slug: str = Field(..., min_length=1, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    tools: List[str] = []  # lab_values, calculator, reference_sheet, notes
    display_order: int = 0
    is_active: bool = True


class AdminExamUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=1, pattern=r"^[a-z0-9-]+$")
    name: Optional[str] = None
    description: Optional[str] = None
    tools: Optional[List[str]] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class AdminExamResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: Optional[str]
    tools: List[str] = []
    display_order: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminTagCreate(BaseModel):
    exam_id: Optional[int] = None
    category: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)


class AdminTagUpdate(BaseModel):
    exam_id: Optional[int] = None
    category: Optional[str] = None
    name: Optional[str] = None


class AdminTagResponse(BaseModel):
    id: int
    exam_id: Optional[int]
    category: str
    name: str

    class Config:
        from_attributes = True


class AdminQuestionTagCreate(BaseModel):
    question_id: int
    tag_id: int


class AdminQuestionTagResponse(BaseModel):
    question_id: int
    tag_id: int

    class Config:
        from_attributes = True


class BuildPart(BaseModel):
    name: str = Field(..., min_length=1)
    question_count: int = Field(..., gt=0, le=200)
    time_limit_minutes: int = Field(..., gt=0)
    section_ids: Optional[List[int]] = None  # Limit to these subjects; empty = any
    break_after_minutes: Optional[int] = Field(None, ge=0)  # Ignored when break_pool_minutes is set


class BuildTestRequest(BaseModel):
    exam_id: int
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    parts: List[BuildPart] = Field(..., min_length=1, max_length=20)
    break_pool_minutes: Optional[int] = Field(None, ge=0)
    scoring: Optional[Dict[str, Any]] = None
    exclude_used: bool = True  # Skip questions already in another test
    package_id: Optional[int] = None  # Add the new test to this package
    seed: Optional[int] = None
    dry_run: bool = False


class BuildPartResult(BaseModel):
    name: str
    question_count: int
    time_limit_minutes: int
    available: int
    by_section: Dict[str, int]


class BuildTestResult(BaseModel):
    test_id: Optional[int]
    parts: List[BuildPartResult]
    pool_size: int
    pool_remaining: int
    problems: List[str]


class AdminOrderResponse(BaseModel):
    id: int
    user_id: int
    package_id: int
    status: str
    amount_cents: int
    currency: str
    stripe_checkout_session_id: Optional[str]
    stripe_payment_intent_id: Optional[str]
    user_package_id: Optional[int]
    created_at: datetime
    paid_at: Optional[datetime]
    refunded_at: Optional[datetime]

    class Config:
        from_attributes = True


class AdminAttemptSectionResponse(BaseModel):
    id: int
    test_attempt_id: int
    test_section_id: Optional[int]
    section_order: int
    name: Optional[str]
    time_limit_minutes: int
    started_at: Optional[datetime]
    deadline_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


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
    exam_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    test_count: int = Field(..., gt=0)
    price: float = Field(..., ge=0)
    validity_days: Optional[int] = Field(180, gt=0)  # None = credits never expire
    is_active: bool = True


class AdminPackageUpdate(BaseModel):
    exam_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    test_count: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, ge=0)
    validity_days: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class AdminPackageResponse(BaseModel):
    id: int
    exam_id: Optional[int] = None
    name: str
    description: Optional[str]
    test_count: int
    price: float
    validity_days: Optional[int] = None
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
    exam_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    time_limit_minutes: int = Field(..., gt=0)
    question_count: int = Field(..., ge=0)
    scoring: Optional[Dict[str, Any]] = None
    break_pool_minutes: Optional[int] = Field(None, ge=0)
    is_active: bool = True


class AdminTestUpdate(BaseModel):
    exam_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, gt=0)
    question_count: Optional[int] = Field(None, ge=0)
    scoring: Optional[Dict[str, Any]] = None
    break_pool_minutes: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class AdminTestResponse(BaseModel):
    id: int
    exam_id: Optional[int] = None
    name: str
    description: Optional[str]
    time_limit_minutes: int
    question_count: int
    scoring: Optional[Dict[str, Any]] = None
    break_pool_minutes: Optional[int] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class AdminTestSectionCreate(BaseModel):
    test_id: int
    section_id: Optional[int] = None
    section_order: int = Field(..., ge=1)
    question_count: int = Field(..., ge=0)
    name: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, gt=0)
    break_after_minutes: Optional[int] = Field(None, ge=0)


class AdminTestSectionUpdate(BaseModel):
    test_id: Optional[int] = None
    section_id: Optional[int] = None
    section_order: Optional[int] = Field(None, ge=1)
    question_count: Optional[int] = Field(None, ge=0)
    name: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, gt=0)
    break_after_minutes: Optional[int] = Field(None, ge=0)


class AdminTestSectionResponse(BaseModel):
    id: int
    test_id: int
    section_id: Optional[int] = None
    section_order: int
    question_count: int
    name: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    break_after_minutes: Optional[int] = None

    class Config:
        from_attributes = True


class AdminTestQuestionCreate(BaseModel):
    test_id: int
    question_id: int
    section_id: Optional[int] = None
    test_section_id: Optional[int] = None
    question_order: int = Field(..., ge=1)
    section_question_order: int = Field(..., ge=1)


class AdminTestQuestionUpdate(BaseModel):
    test_id: Optional[int] = None
    question_id: Optional[int] = None
    section_id: Optional[int] = None
    test_section_id: Optional[int] = None
    question_order: Optional[int] = Field(None, ge=1)
    section_question_order: Optional[int] = Field(None, ge=1)


class AdminTestQuestionResponse(BaseModel):
    id: int
    test_id: int
    question_id: int
    section_id: Optional[int] = None
    test_section_id: Optional[int] = None
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
    scaled_score: Optional[int] = None
    section_scores: Optional[List[Dict[str, Any]]] = None
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
    is_active: bool
    tags: List[str] = []

    @field_validator("tags", mode="before")
    @classmethod
    def tags_as_labels(cls, value: Any) -> List[str]:
        return [tag if isinstance(tag, str) else f"{tag.category}:{tag.name}" for tag in value or []]

    class Config:
        from_attributes = True


class AdminSectionResponse(BaseModel):
    id: int
    exam_id: Optional[int] = None
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True
