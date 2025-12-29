from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
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

    # Relationships
    packages = relationship("UserPackage", back_populates="user")
    test_attempts = relationship("TestAttempt", back_populates="user")


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    test_count = Column(Integer, nullable=False)  # Number of tests included
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_packages = relationship("UserPackage", back_populates="package")


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


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Relationships
    questions = relationship("Question", back_populates="section")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    question_text = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)  # URL to question image
    answer_choices = Column(JSON, nullable=False)  # {"A": "choice text", "B": "choice text", ...}
    correct_answer = Column(String, nullable=False)  # e.g., "A", "B", "C", "D"
    explanation = Column(Text, nullable=True)
    difficulty = Column(String, default="medium")  # easy, medium, hard
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    section = relationship("Section", back_populates="questions")
    question_attempts = relationship("QuestionAttempt", back_populates="question")


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    time_limit_minutes = Column(Integer, nullable=False)  # Total time limit for the test
    question_count = Column(Integer, nullable=False)  # Number of questions in the test
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    test_questions = relationship("TestQuestion", back_populates="test")
    test_attempts = relationship("TestAttempt", back_populates="test")


class TestQuestion(Base):
    """Many-to-many relationship between tests and questions"""
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    question_order = Column(Integer, nullable=False)  # Order of question in the test

    # Relationships
    test = relationship("Test", back_populates="test_questions")
    question = relationship("Question")


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    user_package_id = Column(Integer, ForeignKey("user_packages.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Float, nullable=True)  # Percentage score
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="test_attempts")
    test = relationship("Test", back_populates="test_attempts")
    user_package = relationship("UserPackage", back_populates="test_attempts")
    question_attempts = relationship("QuestionAttempt", back_populates="test_attempt", cascade="all, delete-orphan")


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

