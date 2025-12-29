from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
import logging
from app.db.database import get_db
from app.models.models import (
    Test, TestQuestion, Question, TestAttempt, QuestionAttempt, User, UserPackage
)
from app.schemas.schemas import (
    TestCreate, TestResponse, TestDetailResponse, TestQuestionResponse,
    TestAttemptCreate, TestAttemptResponse
)
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=TestResponse)
async def create_test(
    test: TestCreate,
    db: Session = Depends(get_db)
):
    """Create a new test with specified questions"""
    # Validate all questions exist
    questions = db.query(Question).filter(
        Question.id.in_(test.question_ids),
        Question.is_active == True
    ).all()
    
    if len(questions) != len(test.question_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more questions not found"
        )
    
    # Create test
    db_test = Test(
        name=test.name,
        description=test.description,
        time_limit_minutes=test.time_limit_minutes,
        question_count=len(test.question_ids)
    )
    db.add(db_test)
    db.flush()  # Get the test ID
    
    # Add questions to test
    for index, question_id in enumerate(test.question_ids):
        db_test_question = TestQuestion(
            test_id=db_test.id,
            question_id=question_id,
            question_order=index + 1
        )
        db.add(db_test_question)
    
    db.commit()
    db.refresh(db_test)
    return db_test


@router.get("/", response_model=List[TestResponse])
async def get_tests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all active tests"""
    tests = db.query(Test).filter(Test.is_active == True).offset(skip).limit(limit).all()
    return tests


@router.get("/{test_id}", response_model=TestDetailResponse)
async def get_test(
    test_id: int,
    db: Session = Depends(get_db)
):
    """Get test details including questions (without correct answers)"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Get test questions ordered by question_order
    test_questions = (
        db.query(TestQuestion, Question)
        .join(Question, TestQuestion.question_id == Question.id)
        .filter(TestQuestion.test_id == test_id)
        .order_by(TestQuestion.question_order)
        .all()
    )
    
    questions = []
    for test_question, question in test_questions:
        # Don't include correct_answer or explanation in the response
        questions.append(TestQuestionResponse(
            id=question.id,
            question_text=question.question_text,
            image_url=question.image_url,
            answer_choices=question.answer_choices,
            question_order=test_question.question_order
        ))
    
    return TestDetailResponse(
        id=test.id,
        name=test.name,
        description=test.description,
        time_limit_minutes=test.time_limit_minutes,
        questions=questions
    )


@router.post("/{test_id}/attempt", response_model=TestAttemptResponse)
async def submit_test_attempt(
    test_id: int,
    attempt: TestAttemptCreate,
    user_package_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a completed test attempt"""
    try:
        logger.info(f"Test attempt submission: User {current_user.id}, Test {test_id}, UserPackage {user_package_id}")
        
        # Verify test exists
        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            logger.warning(f"Test {test_id} not found")
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Verify attempt is for the correct test
        if attempt.test_id != test_id:
            logger.warning(f"Test ID mismatch: expected {test_id}, got {attempt.test_id}")
            raise HTTPException(status_code=400, detail="Test ID mismatch")
        
        # Verify user package if provided
        if user_package_id:
            user_package = db.query(UserPackage).filter(
                UserPackage.id == user_package_id,
                UserPackage.user_id == current_user.id
            ).first()
            if not user_package:
                logger.warning(f"User package {user_package_id} not found for user {current_user.id}")
                raise HTTPException(status_code=404, detail="User package not found")
            
            # Decrement tests remaining
            if user_package.tests_remaining > 0:
                user_package.tests_remaining -= 1
        
        # Get all questions for this test with correct answers
        test_questions = (
            db.query(TestQuestion, Question)
            .join(Question, TestQuestion.question_id == Question.id)
            .filter(TestQuestion.test_id == test_id)
            .all()
        )
        
        # Create a map of question_id to correct answer
        correct_answers = {q.id: q.correct_answer for _, q in test_questions}
        
        # Calculate score
        correct_count = 0
        total_questions = len(attempt.question_attempts)
        
        # Create test attempt
        db_test_attempt = TestAttempt(
            user_id=current_user.id,
            test_id=test_id,
            user_package_id=user_package_id,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            total_questions=total_questions
        )
        db.add(db_test_attempt)
        db.flush()
        
        # Create question attempts and calculate score
        for q_attempt in attempt.question_attempts:
            is_correct = q_attempt.selected_answer == correct_answers.get(q_attempt.question_id)
            if is_correct:
                correct_count += 1
            
            db_q_attempt = QuestionAttempt(
                test_attempt_id=db_test_attempt.id,
                question_id=q_attempt.question_id,
                selected_answer=q_attempt.selected_answer,
                is_correct=is_correct,
                time_spent_seconds=q_attempt.time_spent_seconds
            )
            db.add(db_q_attempt)
        
        # Calculate score percentage
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        db_test_attempt.score = score
        db_test_attempt.correct_answers = correct_count
        
        db.commit()
        db.refresh(db_test_attempt)
        
        logger.info(f"Test attempt completed: Attempt ID {db_test_attempt.id}, Score: {score:.1f}%, Correct: {correct_count}/{total_questions}")
        return db_test_attempt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting test attempt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/attempts/{attempt_id}", response_model=TestAttemptResponse)
async def get_test_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a test attempt by ID (must belong to current user)"""
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Test attempt not found")
    return attempt


@router.get("/user-package/{user_package_id}/attempts", response_model=List[TestAttemptResponse])
async def get_user_package_test_attempts(
    user_package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all test attempts for a user package"""
    # Verify user package belongs to current user
    user_package = db.query(UserPackage).filter(
        UserPackage.id == user_package_id,
        UserPackage.user_id == current_user.id
    ).first()
    if not user_package:
        raise HTTPException(status_code=404, detail="User package not found")
    
    attempts = db.query(TestAttempt).filter(
        TestAttempt.user_package_id == user_package_id
    ).order_by(TestAttempt.completed_at.desc()).all()
    
    return attempts

