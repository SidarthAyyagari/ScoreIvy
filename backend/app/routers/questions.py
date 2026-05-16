from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
from app.db.database import get_db
from app.models.models import Question, Section, User
from app.schemas.schemas import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionsBulkCreate
)
from app.deps.admin import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create a single question (admin only)."""
    logger.info(f"Creating question: {question.question_text[:50]}...")
    try:
        # Validate section exists if provided
        if question.section_id:
            section = db.query(Section).filter(Section.id == question.section_id).first()
            if not section:
                logger.warning(f"Section {question.section_id} not found")
                raise HTTPException(status_code=404, detail="Section not found")
        
        # Validate correct answer is in answer choices
        if question.correct_answer not in question.answer_choices:
            logger.warning(f"Correct answer '{question.correct_answer}' not found in answer choices")
            raise HTTPException(
                status_code=400,
                detail=f"Correct answer '{question.correct_answer}' not found in answer choices"
            )
        
        db_question = Question(**question.dict())
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        logger.info(f"✅ Question created with ID: {db_question.id}")
        return db_question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating question: {str(e)}", exc_info=True)
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
        # Validate section exists if provided
        if question_data.section_id:
            section = db.query(Section).filter(Section.id == question_data.section_id).first()
            if not section:
                raise HTTPException(
                    status_code=404,
                    detail=f"Section {question_data.section_id} not found"
                )
        
        # Validate correct answer is in answer choices
        if question_data.correct_answer not in question_data.answer_choices:
            raise HTTPException(
                status_code=400,
                detail=f"Correct answer '{question_data.correct_answer}' not found in answer choices for question: {question_data.question_text[:50]}"
            )
        
        db_question = Question(**question_data.dict())
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
    section_id: int = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get all questions with optional filtering (admin only)."""
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
    """Get a single question by ID (admin only)."""
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
    logger.info(f"Updating question {question_id}")
    try:
        db_question = db.query(Question).filter(Question.id == question_id).first()
        if not db_question:
            logger.warning(f"Question {question_id} not found")
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Update fields if provided
        if question.section_id is not None:
            if question.section_id:
                section = db.query(Section).filter(Section.id == question.section_id).first()
                if not section:
                    raise HTTPException(status_code=404, detail="Section not found")
            db_question.section_id = question.section_id
        if question.question_text is not None:
            db_question.question_text = question.question_text
        if question.image_url is not None:
            db_question.image_url = question.image_url
        if question.answer_choices is not None:
            # Validate correct answer if provided
            if question.correct_answer and question.correct_answer not in question.answer_choices:
                raise HTTPException(
                    status_code=400,
                    detail=f"Correct answer '{question.correct_answer}' not found in answer choices"
                )
            db_question.answer_choices = question.answer_choices
        if question.correct_answer is not None:
            # Validate correct answer is in answer choices
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
        logger.info(f"✅ Question {question_id} updated")
        return db_question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating question: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating question: {str(e)}")


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Soft delete a question (admin only)."""
    logger.info(f"Deleting question {question_id}")
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            logger.warning(f"Question {question_id} not found")
            raise HTTPException(status_code=404, detail="Question not found")
        
        question.is_active = False
        db.commit()
        logger.info(f"✅ Question {question_id} soft deleted")
        return {"message": "Question deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting question: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting question: {str(e)}")
