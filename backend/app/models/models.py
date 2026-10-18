from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)  # Full name from OAuth
    picture = Column(String, nullable=True)  # Profile picture URL from OAuth
    oauth_provider = Column(String, nullable=True)  # e.g., 'google'
    oauth_id = Column(String, nullable=True)  # OAuth provider user ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Relationships
    packages = relationship("UserPackage", back_populates="user")
    test_attempts = relationship("TestAttempt", back_populates="user")


class Exam(Base):
    """A standardized exam the site offers practice for (e.g. USMLE Step 1, SAT)."""
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False)  # URL-safe id, e.g. "usmle-step-1", "sat"
    name = Column(String, nullable=False)
    description = Column(Text)
    tools = Column(JSON, nullable=False, default=list)  # Exam UI tools, e.g. ["lab_values", "calculator", "reference_sheet"]
    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    test_count = Column(Integer, nullable=False)  # Number of tests included
    price = Column(Float, nullable=False)
    validity_days = Column(Integer, nullable=True, default=180)  # Days credits last after purchase; NULL = never expire
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_packages = relationship("UserPackage", back_populates="package")
    package_tests = relationship("PackageTest", back_populates="package")
    exam = relationship("Exam")


class PackageTest(Base):
    """Links packages to their included tests"""
    __tablename__ = "package_tests"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    test_order = Column(Integer, nullable=False)  # Order of test within the package

    # Relationships
    package = relationship("Package", back_populates="package_tests")
    test = relationship("Test", back_populates="package_tests")


class UserPackage(Base):
    __tablename__ = "user_packages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)
    tests_remaining = Column(Integer, nullable=False)
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="packages")
    package = relationship("Package", back_populates="user_packages")
    test_attempts = relationship("TestAttempt", back_populates="user_package")


class Order(Base):
    """A Stripe Checkout purchase of a package. Status: pending, paid, expired, refunded."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    stripe_checkout_session_id = Column(String, unique=True, nullable=True)
    stripe_payment_intent_id = Column(String, nullable=True, index=True)
    user_package_id = Column(Integer, ForeignKey("user_packages.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    package = relationship("Package")
    user_package = relationship("UserPackage")


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Relationships
    questions = relationship("Question", back_populates="section")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    question_type = Column(String, nullable=False, default="multiple_choice")  # multiple_choice | numeric_entry
    question_text = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)  # URL to question image
    answer_choices = Column(JSON, nullable=False)  # {"A": "choice text", ...}; {} for numeric_entry
    correct_answer = Column(String, nullable=False)  # Choice key ("A") or numeric answer ("3/4")
    accepted_answers = Column(JSON, nullable=True)  # Extra accepted numeric_entry answers, e.g. [".75", ".7500"]
    explanation = Column(Text, nullable=True)
    difficulty = Column(String, default="medium")  # easy, medium, hard
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    section = relationship("Section", back_populates="questions")
    question_attempts = relationship("QuestionAttempt", back_populates="question")
    tags = relationship("Tag", secondary="question_tags")


class Tag(Base):
    """Topic tag scoped to an exam, e.g. (system, Cardiovascular) or (domain, Algebra)."""
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("exam_id", "category", "name"),)

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=True)
    category = Column(String, nullable=False)  # e.g. "system", "discipline", "domain", "skill"
    name = Column(String, nullable=False)


class QuestionTag(Base):
    __tablename__ = "question_tags"

    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    time_limit_minutes = Column(Integer, nullable=False)  # Total time; used for sections without their own limit
    question_count = Column(Integer, nullable=False)  # Number of questions in the test
    # Optional raw→scaled conversion: {"overall": {"0": 1, ...}} or {"sections": {"<section_id>": {"0": 200, ...}}}
    scoring = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    test_questions = relationship("TestQuestion", back_populates="test")
    test_sections = relationship("TestSection", back_populates="test")
    test_attempts = relationship("TestAttempt", back_populates="test")
    package_tests = relationship("PackageTest", back_populates="test")


class TestSection(Base):
    """Links sections to tests"""
    __tablename__ = "test_sections"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    section_order = Column(Integer, nullable=False)  # Order of section in the test (1, 2, 3)
    question_count = Column(Integer, nullable=False)  # Number of questions in this section for this test
    name = Column(String, nullable=True)  # Display name, e.g. "Block 1" or "Math — Module 2"
    time_limit_minutes = Column(Integer, nullable=True)  # Separately timed section; NULL = share of test time

    # Relationships
    test = relationship("Test", back_populates="test_sections")
    section = relationship("Section")


class TestQuestion(Base):
    """Many-to-many relationship between tests and questions"""
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    test_section_id = Column(Integer, ForeignKey("test_sections.id", ondelete="SET NULL"), nullable=True)  # Timed block/module
    question_order = Column(Integer, nullable=False)  # Order of question in the test
    section_question_order = Column(Integer, nullable=False)  # Order within the section

    # Relationships
    test = relationship("Test", back_populates="test_questions")
    question = relationship("Question")
    section = relationship("Section")


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    user_package_id = Column(Integer, ForeignKey("user_packages.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    deadline_at = Column(DateTime(timezone=True), nullable=True)  # Server-enforced end of the time limit
    completed_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Float, nullable=True)  # Percentage score
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=True)
    scaled_score = Column(Integer, nullable=True)  # From Test.scoring when configured
    section_scores = Column(JSON, nullable=True)  # [{"section_id", "name", "correct", "total", "scaled"}]
    
    # Relationships
    user = relationship("User", back_populates="test_attempts")
    test = relationship("Test", back_populates="test_attempts")
    user_package = relationship("UserPackage", back_populates="test_attempts")
    question_attempts = relationship("QuestionAttempt", back_populates="test_attempt", cascade="all, delete-orphan")
    sections = relationship(
        "AttemptSection", back_populates="test_attempt",
        cascade="all, delete-orphan", order_by="AttemptSection.section_order",
    )


class AttemptSection(Base):
    """Per-attempt state of one timed section (block/module). Snapshot of name and time limit."""
    __tablename__ = "attempt_sections"
    __table_args__ = (UniqueConstraint("test_attempt_id", "section_order"),)

    id = Column(Integer, primary_key=True, index=True)
    test_attempt_id = Column(Integer, ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False)
    test_section_id = Column(Integer, ForeignKey("test_sections.id", ondelete="SET NULL"), nullable=True)
    section_order = Column(Integer, nullable=False)
    name = Column(String, nullable=True)
    time_limit_minutes = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    deadline_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    test_attempt = relationship("TestAttempt", back_populates="sections")


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id = Column(Integer, primary_key=True, index=True)
    test_attempt_id = Column(Integer, ForeignKey("test_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_answer = Column(String, nullable=True)  # User's selected answer (e.g., "A", "B")
    is_correct = Column(Boolean, nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)  # Time spent on this question
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    test_attempt = relationship("TestAttempt", back_populates="question_attempts")
    question = relationship("Question", back_populates="question_attempts")

