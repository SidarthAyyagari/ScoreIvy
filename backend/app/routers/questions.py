
"""Admin question CRUD and bulk create endpoints.

Request bodies are validated via ``QuestionCreate`` (Pydantic) before handlers run.
Route handler docstrings describe each HTTP operation for OpenAPI / Swagger UI.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.db.database import get_db
from app.models.models import Question
from app.services import questions as question_service
from app.schemas.schemas import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionsBulkCreate,
    CsvUploadErrorResponse,
    CsvUploadSuccessResponse,
    CsvValidationErrorItem,
)
from app.deps.admin import require_admin
from app.services.question_csv import parse_and_validate_csv, import_questions
from app.models.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=QuestionResponse, status_code=201)
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create a single question (admin only)."""
    try:
        db_question = question_service.create_question(db, question)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(db_question)
    logger.info("Question created with ID: %s", db_question.id)
    return db_question


@router.post("/bulk", response_model=List[QuestionResponse])
async def create_questions_bulk(
    questions_data: QuestionsBulkCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create multiple questions at once (admin only)."""
    try:
        created_questions = [
            question_service.create_question(db, question_data)
            for question_data in questions_data.questions
        ]
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    for question in created_questions:
        db.refresh(question)
    return created_questions


@router.post(
    "/upload-csv",
    response_model=CsvUploadSuccessResponse,
    responses={422: {"model": CsvUploadErrorResponse}},
)
async def upload_questions_csv(
    file: UploadFile = File(...),
    exam_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
):
    """Bulk import questions from a CSV file (admin only)."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv upload")

    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")

    logger.info("Validating CSV upload: %s (%s bytes)", file.filename, len(raw))
    valid_questions, errors, total_rows = parse_and_validate_csv(content, db, default_exam_id=exam_id)

    if errors:
        error_response = CsvUploadErrorResponse(
            total_rows=total_rows,
            error_count=len(errors),
            errors=[CsvValidationErrorItem(**item.to_dict()) for item in errors],
        )
        return JSONResponse(status_code=422, content=error_response.model_dump())

    if not valid_questions:
        error_response = CsvUploadErrorResponse(
            total_rows=0,
            error_count=1,
            errors=[
                CsvValidationErrorItem(row=0, message="No valid questions found in CSV")
            ],
        )
        return JSONResponse(status_code=422, content=error_response.model_dump())

    try:
        created = import_questions(db, valid_questions)
    except Exception as exc:
        logger.error("CSV import failed: %s", exc, exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Error importing questions")

    logger.info("Imported %s questions from CSV", len(created))
    return CsvUploadSuccessResponse(
        imported_count=len(created),
        total_rows=total_rows,
        questions=created,
    )


@router.get("/", response_model=List[QuestionResponse])
async def get_questions(
    skip: int = 0,
    limit: int = 100,
    section_id: Optional[int] = None,
    exam_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get all questions with optional filtering"""
    query = db.query(Question).filter(Question.is_active == True)

    if exam_id:
        query = query.filter(Question.exam_id == exam_id)
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
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    try:
        question_service.update_question(db, db_question, question.model_dump(exclude_unset=True))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(db_question)
    logger.info("Question %s updated", question_id)
    return db_question


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
        raise HTTPException(status_code=500, detail="Error deleting question")
