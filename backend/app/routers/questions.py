from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.db.database import get_db
from app.models.models import Question, Section, User
from app.schemas.schemas import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionsBulkCreate,
)
from app.deps.admin import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


def _assert_section_exists(db: Session, section_id: int) -> None:
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")


@router.post("/", response_model=QuestionResponse, status_code=201)
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create a single MCQ question (admin only)."""
    logger.info("Creating question: %s...", question.question_text[:50])
    try:
        if question.section_id is not None:
            _assert_section_exists(db, question.section_id)

        db_question = Question(**question.model_dump())
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        logger.info("Question created with ID: %s", db_question.id)
        return db_question
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating question: %s", str(e), exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating question: {str(e)}")


@router.post("/bulk", response_model=List[QuestionResponse])
async def create_questions_bulk(
    questions_data: QuestionsBulkCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create multiple questions at once (admin only)."""
    created_questions = []

    for question_data in questions_data.questions:
        if question_data.section_id is not None:
            _assert_section_exists(db, question_data.section_id)

        db_question = Question(**question_data.model_dump())
        db.add(db_question)
        created_questions.append(db_question)

    db.commit()

    for question in created_questions:
        db.refresh(question)

    return created_questions


@router.get("/", response_model=List[QuestionResponse])
async def get_questions(
    skip: int = 0,
    limit: int = 100,
    section_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get all questions with optional filtering"""
    query = db.query(Question).filter(Question.is_active == True)

    if section_id:
        query = query.filter(Question.section_id == section_id)

    questions = query.offset(skip).limit(limit).all()
    return questions


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get a single question by ID"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question: QuestionUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Update a question (admin only)."""
    logger.info("Updating question %s", question_id)
    try:
        db_question = db.query(Question).filter(Question.id == question_id).first()
        if not db_question:
            logger.warning("Question %s not found", question_id)
            raise HTTPException(status_code=404, detail="Question not found")

        if question.section_id is not None:
            if question.section_id:
                _assert_section_exists(db, question.section_id)
            db_question.section_id = question.section_id
        if question.question_text is not None:
            db_question.question_text = question.question_text
        if question.image_url is not None:
            db_question.image_url = question.image_url
        if question.answer_choices is not None:
            if question.correct_answer and question.correct_answer not in question.answer_choices:
                raise HTTPException(
                    status_code=400,
                    detail=f"Correct answer '{question.correct_answer}' not found in answer choices"
                )
            db_question.answer_choices = question.answer_choices
        if question.correct_answer is not None:
            current_choices = question.answer_choices if question.answer_choices else db_question.answer_choices
            if question.correct_answer not in current_choices:
                raise HTTPException(
                    status_code=400,
                    detail=f"Correct answer '{question.correct_answer}' not found in answer choices"
                )
            db_question.correct_answer = question.correct_answer
        if question.explanation is not None:
            db_question.explanation = question.explanation
        if question.difficulty is not None:
            db_question.difficulty = question.difficulty
        if question.is_active is not None:
            db_question.is_active = question.is_active

        db.commit()
        db.refresh(db_question)
        logger.info("Question %s updated", question_id)
        return db_question
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating question: %s", str(e), exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating question: {str(e)}")


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Soft delete a question (admin only)."""
    logger.info("Deleting question %s", question_id)
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            logger.warning("Question %s not found", question_id)
            raise HTTPException(status_code=404, detail="Question not found")

        question.is_active = False
        db.commit()
        logger.info("Question %s soft deleted", question_id)
        return {"message": "Question deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting question: %s", str(e), exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting question: {str(e)}")
