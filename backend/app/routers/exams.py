from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Exam
from app.schemas.schemas import ExamResponse

router = APIRouter()


@router.get("/", response_model=List[ExamResponse])
async def list_exams(db: Session = Depends(get_db)):
    """Active exams students can buy practice for, in display order."""
    return (
        db.query(Exam)
        .filter(Exam.is_active == True)
        .order_by(Exam.display_order, Exam.name)
        .all()
    )


@router.get("/{slug}", response_model=ExamResponse)
async def get_exam(slug: str, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.slug == slug, Exam.is_active == True).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam
