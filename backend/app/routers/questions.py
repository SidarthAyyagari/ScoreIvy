from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import Question, Section
from app.schemas.schemas import QuestionCreate, QuestionResponse, QuestionsBulkCreate

router = APIRouter()


@router.post("/", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db)
):
    """Create a single question"""
    # Validate section exists if provided
    if question.section_id:
        section = db.query(Section).filter(Section.id == question.section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
    
    # Validate correct answer is in answer choices
    if question.correct_answer not in question.answer_choices:
        raise HTTPException(
            status_code=400,
            detail=f"Correct answer '{question.correct_answer}' not found in answer choices"
        )
    
    db_question = Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


@router.post("/bulk", response_model=List[QuestionResponse])
async def create_questions_bulk(
    questions_data: QuestionsBulkCreate,
    db: Session = Depends(get_db)
):
    """Create multiple questions at once"""
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """Get a single question by ID"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """Soft delete a question (set is_active to False)"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    question.is_active = False
    db.commit()
    return {"message": "Question deleted successfully"}

