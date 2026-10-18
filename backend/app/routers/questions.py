"""Question bank API for admins and question writers.

Every change is recorded in the question's history and can be reverted. Deleting a question
that students have already been served archives it instead (see ``services.questions``).
"""

import logging
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.deps.admin import require_admin
from app.models.models import Exam, Question, QuestionRevision, Tag, User
from app.schemas.schemas import (
    CsvUploadErrorResponse,
    CsvUploadSuccessResponse,
    CsvValidationErrorItem,
    QuestionCreate,
    QuestionDetailResponse,
    QuestionPage,
    QuestionRemoveResponse,
    QuestionResponse,
    QuestionRevisionResponse,
    QuestionsBulkCreate,
    QuestionUpdate,
)
from app.services import questions as question_service
from app.services.question_csv import export_questions_csv, import_questions, parse_and_validate_csv

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_question(db: Session, question_id: int) -> Question:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


def _detail(db: Session, question: Question) -> QuestionDetailResponse:
    base = QuestionResponse.model_validate(question).model_dump()
    return QuestionDetailResponse(**base, usage=question_service.usage(db, question))


def _filtered(
    db: Session,
    exam_id: Optional[int],
    section_id: Optional[int],
    status: str,
    q: Optional[str],
    tag: Optional[str],
    question_type: Optional[str],
):
    query = db.query(Question)
    if exam_id is not None:
        query = query.filter(Question.exam_id == exam_id)
    if section_id is not None:
        query = query.filter(Question.section_id == section_id)
    if status == "active":
        query = query.filter(Question.is_active == True)  # noqa: E712
    elif status == "archived":
        query = query.filter(Question.is_active == False)  # noqa: E712
    if question_type:
        query = query.filter(Question.question_type == question_type)
    if q and q.strip():
        term = f"%{q.strip()}%"
        filters = [Question.question_text.ilike(term), Question.explanation.ilike(term)]
        if q.strip().isdigit():
            filters.append(Question.id == int(q.strip()))
        query = query.filter(or_(*filters))
    if tag:
        category, _, name = tag.partition(":")
        query = query.filter(Question.tags.any((Tag.category == category.strip()) & (Tag.name == name.strip())))
    return query


@router.get("/", response_model=QuestionPage)
def search_questions(
    exam_id: Optional[int] = None,
    section_id: Optional[int] = None,
    status: str = Query("active", pattern="^(active|archived|all)$"),
    q: Optional[str] = Query(None, max_length=200, description="Text in the stem or explanation, or a question id"),
    tag: Optional[str] = Query(None, description="category:name"),
    question_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = _filtered(db, exam_id, section_id, status, q, tag, question_type)
    total = query.count()
    items = query.options(selectinload(Question.tags)).order_by(Question.id.desc()).offset(skip).limit(limit).all()
    return QuestionPage(items=items, total=total)


@router.get("/export")
def export_questions(
    exam_id: Optional[int] = None,
    status: str = Query("all", pattern="^(active|archived|all)$"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Download questions as CSV in the upload format (a portable backup that can be re-imported)."""
    questions = (
        _filtered(db, exam_id, None, status, None, None, None)
        .options(selectinload(Question.tags))
        .order_by(Question.id)
        .all()
    )
    slugs = {exam.id: exam.slug for exam in db.query(Exam).all()}
    filename = f"scoreivy-questions-{slugs.get(exam_id, 'all')}-{date.today().isoformat()}.csv"
    return Response(
        content=export_questions_csv(questions, slugs),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/upload-csv",
    response_model=CsvUploadSuccessResponse,
    responses={422: {"model": CsvUploadErrorResponse}},
)
async def upload_questions_csv(
    file: UploadFile = File(...),
    exam_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Bulk import questions from a CSV file. Nothing is imported if any row is invalid."""
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
            errors=[CsvValidationErrorItem(row=0, message="No valid questions found in CSV")],
        )
        return JSONResponse(status_code=422, content=error_response.model_dump())

    try:
        created = import_questions(db, valid_questions, admin)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("CSV import failed: %s", exc, exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Error importing questions")

    logger.info("Imported %s questions from CSV", len(created))
    return CsvUploadSuccessResponse(imported_count=len(created), total_rows=total_rows, questions=created)


@router.post("/", response_model=QuestionResponse, status_code=201)
def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        db_question = question_service.create_question(db, question, admin)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(db_question)
    return db_question


@router.post("/bulk", response_model=List[QuestionResponse])
def create_questions_bulk(
    questions_data: QuestionsBulkCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        created = [question_service.create_question(db, q, admin) for q in questions_data.questions]
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    for question in created:
        db.refresh(question)
    return created


@router.get("/{question_id}", response_model=QuestionDetailResponse)
def get_question(question_id: int, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return _detail(db, _get_question(db, question_id))


@router.put("/{question_id}", response_model=QuestionDetailResponse)
def update_question(
    question_id: int,
    question: QuestionUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    db_question = _get_question(db, question_id)
    try:
        question_service.update_question(db, db_question, question.model_dump(exclude_unset=True), admin)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(db_question)
    return _detail(db, db_question)


@router.delete("/{question_id}", response_model=QuestionRemoveResponse)
def delete_question(question_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Delete permanently if no student has been served the question; otherwise archive it."""
    result = question_service.remove_question(db, _get_question(db, question_id), admin)
    db.commit()
    logger.info("Question %s %s by %s", question_id, result, admin.email)
    return QuestionRemoveResponse(result=result)


@router.post("/{question_id}/archive", response_model=QuestionDetailResponse)
def archive_question(question_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    question = question_service.set_active(db, _get_question(db, question_id), False, admin)
    db.commit()
    return _detail(db, question)


@router.post("/{question_id}/restore", response_model=QuestionDetailResponse)
def restore_question(question_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    question = question_service.set_active(db, _get_question(db, question_id), True, admin)
    db.commit()
    return _detail(db, question)


@router.get("/{question_id}/history", response_model=List[QuestionRevisionResponse])
def question_history(question_id: int, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Newest first. Works for deleted questions too."""
    return (
        db.query(QuestionRevision)
        .filter(QuestionRevision.question_id == question_id)
        .order_by(QuestionRevision.id.desc())
        .all()
    )


@router.post("/{question_id}/revert/{revision_id}", response_model=QuestionDetailResponse)
def revert_question(
    question_id: int,
    revision_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    question = _get_question(db, question_id)
    revision = db.get(QuestionRevision, revision_id)
    if revision is None:
        raise HTTPException(status_code=404, detail="Revision not found")
    try:
        question_service.revert_question(db, question, revision, admin)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(question)
    return _detail(db, question)
