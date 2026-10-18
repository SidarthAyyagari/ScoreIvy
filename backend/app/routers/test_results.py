from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from app.db.database import get_db
from app.models.models import Exam, TestAttempt, TestQuestion, QuestionAttempt, Question, User
from app.schemas.schemas import QuestionAttemptResponse
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/attempts/{attempt_id}/results")
async def get_test_attempt_results(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed results for a completed attempt (correct answers and explanations)."""
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Test attempt not found")
    if attempt.completed_at is None:
        raise HTTPException(status_code=409, detail="Results are available after the test is submitted")

    question_attempts = (
        db.query(QuestionAttempt, Question)
        .join(Question, QuestionAttempt.question_id == Question.id)
        .outerjoin(
            TestQuestion,
            (TestQuestion.test_id == attempt.test_id) & (TestQuestion.question_id == Question.id),
        )
        .filter(QuestionAttempt.test_attempt_id == attempt_id)
        .order_by(TestQuestion.question_order, QuestionAttempt.id)
        .all()
    )

    questions_data = []
    for qa, question in question_attempts:
        questions_data.append({
            "id": question.id,
            "question_type": question.question_type,
            "question_text": question.question_text,
            "image_url": question.image_url,
            "answer_choices": question.answer_choices,
            "correct_answer": question.correct_answer,
            "accepted_answers": question.accepted_answers,
            "explanation": question.explanation,
            "section_id": question.section_id,
            "tags": [f"{tag.category}:{tag.name}" for tag in question.tags],
            "selected_answer": qa.selected_answer,
            "is_correct": qa.is_correct,
            "time_spent_seconds": qa.time_spent_seconds
        })

    test = attempt.test
    exam = test.exam_id and db.get(Exam, test.exam_id)
    return {
        "attempt": {
            "id": attempt.id,
            "test_id": attempt.test_id,
            "test_name": test.name,
            "exam": {"slug": exam.slug, "name": exam.name} if exam else None,
            "score": attempt.score,
            "scaled_score": attempt.scaled_score,
            "section_scores": attempt.section_scores or [],
            "total_questions": attempt.total_questions,
            "correct_answers": attempt.correct_answers,
            "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None
        },
        "questions": questions_data
    }


@router.get("/question-attempts/{question_attempt_id}", response_model=QuestionAttemptResponse)
async def get_question_attempt(
    question_attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a question attempt by ID (must belong to current user)"""
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
        raise HTTPException(status_code=404, detail="Question attempt not found")
    return qa
