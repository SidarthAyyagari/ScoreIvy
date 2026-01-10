from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
from app.db.database import get_db
from app.models.models import TestAttempt, QuestionAttempt, Question, User
from app.schemas.schemas import TestAttemptUpdate, QuestionAttemptUpdate, QuestionAttemptResponse
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/attempts/{attempt_id}/results")
async def get_test_attempt_results(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed test attempt results with questions and answers"""
    # Get test attempt
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Test attempt not found")
    
    # Get all question attempts with questions
    question_attempts = (
        db.query(QuestionAttempt, Question)
        .join(Question, QuestionAttempt.question_id == Question.id)
        .filter(QuestionAttempt.test_attempt_id == attempt_id)
        .order_by(QuestionAttempt.id)
        .all()
    )
    
    # Format results
    questions_data = []
    for qa, question in question_attempts:
        questions_data.append({
            "id": question.id,
            "question_text": question.question_text,
            "image_url": question.image_url,
            "answer_choices": question.answer_choices,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "selected_answer": qa.selected_answer,
            "is_correct": qa.is_correct,
            "time_spent_seconds": qa.time_spent_seconds
        })
    
    return {
        "attempt": {
            "id": attempt.id,
            "test_id": attempt.test_id,
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "correct_answers": attempt.correct_answers,
            "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None
        },
        "questions": questions_data
    }


@router.put("/attempts/{attempt_id}")
async def update_test_attempt(
    attempt_id: int,
    attempt: TestAttemptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a test attempt (only for current user's attempts)"""
    logger.info(f"Updating test attempt {attempt_id} for user {current_user.id}")
    try:
        db_attempt = db.query(TestAttempt).filter(
            TestAttempt.id == attempt_id,
            TestAttempt.user_id == current_user.id
        ).first()
        
        if not db_attempt:
            logger.warning(f"Test attempt {attempt_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Test attempt not found")
        
        if attempt.completed_at is not None:
            db_attempt.completed_at = attempt.completed_at
        if attempt.score is not None:
            db_attempt.score = attempt.score
        if attempt.correct_answers is not None:
            db_attempt.correct_answers = attempt.correct_answers
        
        db.commit()
        db.refresh(db_attempt)
        logger.info(f"✅ Test attempt {attempt_id} updated")
        return {"message": "Test attempt updated successfully", "id": db_attempt.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating test attempt: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating test attempt: {str(e)}")


@router.delete("/attempts/{attempt_id}")
async def delete_test_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a test attempt (only for current user's attempts)"""
    logger.info(f"Deleting test attempt {attempt_id} for user {current_user.id}")
    try:
        db_attempt = db.query(TestAttempt).filter(
            TestAttempt.id == attempt_id,
            TestAttempt.user_id == current_user.id
        ).first()
        
        if not db_attempt:
            logger.warning(f"Test attempt {attempt_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Test attempt not found")
        
        db.delete(db_attempt)
        db.commit()
        logger.info(f"✅ Test attempt {attempt_id} deleted")
        return {"message": "Test attempt deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting test attempt: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting test attempt: {str(e)}")


@router.get("/question-attempts/{question_attempt_id}", response_model=QuestionAttemptResponse)
async def get_question_attempt(
    question_attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a question attempt by ID (must belong to current user)"""
    logger.info(f"Fetching question attempt {question_attempt_id}")
    qa = (
        db.query(QuestionAttempt)
        .join(TestAttempt, QuestionAttempt.test_attempt_id == TestAttempt.id)
        .filter(
            QuestionAttempt.id == question_attempt_id,
            TestAttempt.user_id == current_user.id
        )
        .first()
    )
    
    if not qa:
        logger.warning(f"Question attempt {question_attempt_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Question attempt not found")
    return qa


@router.put("/question-attempts/{question_attempt_id}", response_model=QuestionAttemptResponse)
async def update_question_attempt(
    question_attempt_id: int,
    question_attempt: QuestionAttemptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a question attempt (only for current user's attempts)"""
    logger.info(f"Updating question attempt {question_attempt_id} for user {current_user.id}")
    try:
        db_qa = (
            db.query(QuestionAttempt)
            .join(TestAttempt, QuestionAttempt.test_attempt_id == TestAttempt.id)
            .filter(
                QuestionAttempt.id == question_attempt_id,
                TestAttempt.user_id == current_user.id
            )
            .first()
        )
        
        if not db_qa:
            logger.warning(f"Question attempt {question_attempt_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Question attempt not found")
        
        if question_attempt.selected_answer is not None:
            db_qa.selected_answer = question_attempt.selected_answer
        if question_attempt.is_correct is not None:
            db_qa.is_correct = question_attempt.is_correct
        if question_attempt.time_spent_seconds is not None:
            db_qa.time_spent_seconds = question_attempt.time_spent_seconds
        
        db.commit()
        db.refresh(db_qa)
        logger.info(f"✅ Question attempt {question_attempt_id} updated")
        return db_qa
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating question attempt: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating question attempt: {str(e)}")


@router.delete("/question-attempts/{question_attempt_id}")
async def delete_question_attempt(
    question_attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a question attempt (only for current user's attempts)"""
    logger.info(f"Deleting question attempt {question_attempt_id} for user {current_user.id}")
    try:
        db_qa = (
            db.query(QuestionAttempt)
            .join(TestAttempt, QuestionAttempt.test_attempt_id == TestAttempt.id)
            .filter(
                QuestionAttempt.id == question_attempt_id,
                TestAttempt.user_id == current_user.id
            )
            .first()
        )
        
        if not db_qa:
            logger.warning(f"Question attempt {question_attempt_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Question attempt not found")
        
        db.delete(db_qa)
        db.commit()
        logger.info(f"✅ Question attempt {question_attempt_id} deleted")
        return {"message": "Question attempt deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting question attempt: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting question attempt: {str(e)}")
