from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import TestAttempt, QuestionAttempt, Question, User
from app.routers.auth import get_current_user

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
