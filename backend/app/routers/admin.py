"""Admin-only CRUD API for all database tables."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Type, TypeVar, Any, Optional
import logging

from app.db.database import get_db
from app.deps.admin import require_admin
from app.services import test_builder
from app.models.models import (
    AttemptSection,
    Exam,
    Order,
    QuestionTag,
    Tag,
    User,
    Package,
    PackageTest,
    UserPackage,
    Section,
    Question,
    Test,
    TestSection,
    TestQuestion,
    TestAttempt,
    QuestionAttempt,
)
from app.schemas.schemas import (
    SectionCreate,
    SectionUpdate,
)
from app.schemas.admin_schemas import (
    BuildTestRequest,
    BuildTestResult,
    AdminAttemptSectionResponse,
    AdminOrderResponse,
    AdminExamCreate,
    AdminExamResponse,
    AdminExamUpdate,
    AdminQuestionTagCreate,
    AdminQuestionTagResponse,
    AdminTagCreate,
    AdminTagResponse,
    AdminTagUpdate,
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    AdminPackageCreate,
    AdminPackageUpdate,
    AdminPackageResponse,
    AdminPackageTestCreate,
    AdminPackageTestUpdate,
    AdminPackageTestResponse,
    AdminUserPackageCreate,
    AdminUserPackageUpdate,
    AdminUserPackageResponse,
    AdminTestCreate,
    AdminTestUpdate,
    AdminTestResponse,
    AdminTestSectionCreate,
    AdminTestSectionUpdate,
    AdminTestSectionResponse,
    AdminTestQuestionCreate,
    AdminTestQuestionUpdate,
    AdminTestQuestionResponse,
    AdminTestAttemptCreate,
    AdminTestAttemptUpdate,
    AdminTestAttemptResponse,
    AdminQuestionAttemptCreate,
    AdminQuestionAttemptUpdate,
    AdminQuestionAttemptResponse,
    AdminSectionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_admin)])

ModelT = TypeVar("ModelT")


def _get_or_404(db: Session, model: Type[ModelT], item_id: int) -> ModelT:
    item = db.query(model).filter(model.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"{model.__tablename__} not found")
    return item


def _apply_updates(item: Any, data: dict) -> None:
    for key, value in data.items():
        if value is not None:
            setattr(item, key, value)


# --- Exams ---


@router.get("/exams", response_model=List[AdminExamResponse])
def list_exams(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(Exam).order_by(Exam.display_order, Exam.id).offset(skip).limit(limit).all()


@router.get("/exams/{exam_id}", response_model=AdminExamResponse)
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Exam, exam_id)


@router.post("/exams", response_model=AdminExamResponse, status_code=201)
def create_exam(payload: AdminExamCreate, db: Session = Depends(get_db)):
    if db.query(Exam).filter(Exam.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail="An exam with this slug already exists")
    item = Exam(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/exams/{exam_id}", response_model=AdminExamResponse)
def update_exam(exam_id: int, payload: AdminExamUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, Exam, exam_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/exams/{exam_id}")
def delete_exam(exam_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, Exam, exam_id)
    item.is_active = False
    db.commit()
    return {"message": "Exam deactivated"}


# --- Tags ---


@router.get("/tags", response_model=List[AdminTagResponse])
def list_tags(skip: int = 0, limit: int = 500, exam_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Tag)
    if exam_id is not None:
        query = query.filter(Tag.exam_id == exam_id)
    return query.order_by(Tag.category, Tag.name).offset(skip).limit(limit).all()


@router.get("/tags/{tag_id}", response_model=AdminTagResponse)
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Tag, tag_id)


@router.post("/tags", response_model=AdminTagResponse, status_code=201)
def create_tag(payload: AdminTagCreate, db: Session = Depends(get_db)):
    item = Tag(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/tags/{tag_id}", response_model=AdminTagResponse)
def update_tag(tag_id: int, payload: AdminTagUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, Tag, tag_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, Tag, tag_id)
    db.delete(item)
    db.commit()
    return {"message": "Tag deleted"}


@router.get("/question-tags", response_model=List[AdminQuestionTagResponse])
def list_question_tags(
    skip: int = 0, limit: int = 500, question_id: Optional[int] = None, db: Session = Depends(get_db)
):
    query = db.query(QuestionTag)
    if question_id is not None:
        query = query.filter(QuestionTag.question_id == question_id)
    return query.offset(skip).limit(limit).all()


@router.post("/question-tags", response_model=AdminQuestionTagResponse, status_code=201)
def create_question_tag(payload: AdminQuestionTagCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Question, payload.question_id)
    _get_or_404(db, Tag, payload.tag_id)
    existing = db.get(QuestionTag, (payload.question_id, payload.tag_id))
    if existing:
        return existing
    item = QuestionTag(**payload.model_dump())
    db.add(item)
    db.commit()
    return item


@router.delete("/question-tags/{question_id}/{tag_id}")
def delete_question_tag(question_id: int, tag_id: int, db: Session = Depends(get_db)):
    item = db.get(QuestionTag, (question_id, tag_id))
    if not item:
        raise HTTPException(status_code=404, detail="question_tags not found")
    db.delete(item)
    db.commit()
    return {"message": "Question tag deleted"}


@router.get("/attempt-sections", response_model=List[AdminAttemptSectionResponse])
def list_attempt_sections(
    skip: int = 0, limit: int = 200, test_attempt_id: Optional[int] = None, db: Session = Depends(get_db)
):
    query = db.query(AttemptSection)
    if test_attempt_id is not None:
        query = query.filter(AttemptSection.test_attempt_id == test_attempt_id)
    return query.order_by(AttemptSection.test_attempt_id, AttemptSection.section_order).offset(skip).limit(limit).all()


@router.get("/test-builder/pool")
def test_builder_pool(exam_id: int, exclude_used: bool = True, db: Session = Depends(get_db)):
    """How many questions the builder can draw from, per subject section."""
    pool = test_builder.question_pool(db, exam_id, exclude_used)
    names = {s.id: s.name for s in db.query(Section).filter(Section.exam_id == exam_id)}
    counts: dict = {}
    for question in pool:
        counts[question.section_id] = counts.get(question.section_id, 0) + 1
    return {
        "total": len(pool),
        "by_section": [
            {"section_id": key, "name": names.get(key, "No section"), "count": value}
            for key, value in sorted(counts.items(), key=lambda item: names.get(item[0], ""))
        ],
    }


@router.post("/test-builder", response_model=BuildTestResult)
def build_test(payload: BuildTestRequest, db: Session = Depends(get_db)):
    """Assemble a test from unused bank questions. With ``dry_run`` nothing is saved."""
    if not db.get(Exam, payload.exam_id):
        raise HTTPException(status_code=404, detail="Exam not found")
    try:
        result = test_builder.build_test(db, payload)
    except test_builder.BuildError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    if payload.dry_run:
        db.rollback()
    else:
        db.commit()
        logger.info("Built test %s (%s questions)", result.test_id, sum(p.question_count for p in result.parts))
    return result


@router.get("/orders", response_model=List[AdminOrderResponse])
def list_orders(skip: int = 0, limit: int = 200, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


# --- Users ---


@router.get("/users", response_model=List[AdminUserResponse])
def list_users(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, User, user_id)


@router.post("/users", response_model=AdminUserResponse, status_code=201)
def create_user(payload: AdminUserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    item = User(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_user(user_id: int, payload: AdminUserUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, User, user_id)
    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"] != item.email:
        if db.query(User).filter(User.email == data["email"]).first():
            raise HTTPException(status_code=400, detail="Email already registered")
    _apply_updates(item, data)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, User, user_id)
    db.delete(item)
    db.commit()
    return {"message": "User deleted"}


# --- Packages ---


@router.get("/packages", response_model=List[AdminPackageResponse])
def list_packages(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(Package).offset(skip).limit(limit).all()


@router.get("/packages/{package_id}", response_model=AdminPackageResponse)
def get_package(package_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Package, package_id)


@router.post("/packages", response_model=AdminPackageResponse, status_code=201)
def create_package(payload: AdminPackageCreate, db: Session = Depends(get_db)):
    item = Package(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/packages/{package_id}", response_model=AdminPackageResponse)
def update_package(package_id: int, payload: AdminPackageUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, Package, package_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/packages/{package_id}")
def delete_package(package_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, Package, package_id)
    db.delete(item)
    db.commit()
    return {"message": "Package deleted"}


# --- Package tests ---


@router.get("/package-tests", response_model=List[AdminPackageTestResponse])
def list_package_tests(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(PackageTest).offset(skip).limit(limit).all()


@router.get("/package-tests/{item_id}", response_model=AdminPackageTestResponse)
def get_package_test(item_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, PackageTest, item_id)


@router.post("/package-tests", response_model=AdminPackageTestResponse, status_code=201)
def create_package_test(payload: AdminPackageTestCreate, db: Session = Depends(get_db)):
    item = PackageTest(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/package-tests/{item_id}", response_model=AdminPackageTestResponse)
def update_package_test(item_id: int, payload: AdminPackageTestUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, PackageTest, item_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/package-tests/{item_id}")
def delete_package_test(item_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, PackageTest, item_id)
    db.delete(item)
    db.commit()
    return {"message": "Package test deleted"}


# --- User packages ---


@router.get("/user-packages", response_model=List[AdminUserPackageResponse])
def list_user_packages(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(UserPackage).offset(skip).limit(limit).all()


@router.get("/user-packages/{item_id}", response_model=AdminUserPackageResponse)
def get_user_package(item_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, UserPackage, item_id)


@router.post("/user-packages", response_model=AdminUserPackageResponse, status_code=201)
def create_user_package(payload: AdminUserPackageCreate, db: Session = Depends(get_db)):
    item = UserPackage(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/user-packages/{item_id}", response_model=AdminUserPackageResponse)
def update_user_package(item_id: int, payload: AdminUserPackageUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, UserPackage, item_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/user-packages/{item_id}")
def delete_user_package(item_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, UserPackage, item_id)
    db.delete(item)
    db.commit()
    return {"message": "User package deleted"}


# --- Sections ---


@router.get("/sections", response_model=List[AdminSectionResponse])
def list_sections(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(Section).offset(skip).limit(limit).all()


@router.get("/sections/{section_id}", response_model=AdminSectionResponse)
def get_section(section_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Section, section_id)


@router.post("/sections", response_model=AdminSectionResponse, status_code=201)
def create_section(payload: SectionCreate, db: Session = Depends(get_db)):
    item = Section(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/sections/{section_id}", response_model=AdminSectionResponse)
def update_section(section_id: int, payload: SectionUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, Section, section_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/sections/{section_id}")
def delete_section(section_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, Section, section_id)
    db.delete(item)
    db.commit()
    return {"message": "Section deleted"}


# --- Tests ---


@router.get("/tests", response_model=List[AdminTestResponse])
def list_tests(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(Test).offset(skip).limit(limit).all()


@router.get("/tests/{test_id}", response_model=AdminTestResponse)
def get_test(test_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Test, test_id)


@router.post("/tests", response_model=AdminTestResponse, status_code=201)
def create_test(payload: AdminTestCreate, db: Session = Depends(get_db)):
    item = Test(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/tests/{test_id}", response_model=AdminTestResponse)
def update_test(test_id: int, payload: AdminTestUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, Test, test_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/tests/{test_id}")
def delete_test(test_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, Test, test_id)
    item.is_active = False
    db.commit()
    return {"message": "Test deactivated"}


# --- Test sections ---


@router.get("/test-sections", response_model=List[AdminTestSectionResponse])
def list_test_sections(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(TestSection).offset(skip).limit(limit).all()


@router.get("/test-sections/{item_id}", response_model=AdminTestSectionResponse)
def get_test_section(item_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, TestSection, item_id)


@router.post("/test-sections", response_model=AdminTestSectionResponse, status_code=201)
def create_test_section(payload: AdminTestSectionCreate, db: Session = Depends(get_db)):
    item = TestSection(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/test-sections/{item_id}", response_model=AdminTestSectionResponse)
def update_test_section(item_id: int, payload: AdminTestSectionUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, TestSection, item_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/test-sections/{item_id}")
def delete_test_section(item_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, TestSection, item_id)
    db.delete(item)
    db.commit()
    return {"message": "Test section deleted"}


# --- Test questions ---


@router.get("/test-questions", response_model=List[AdminTestQuestionResponse])
def list_test_questions(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(TestQuestion).offset(skip).limit(limit).all()


@router.get("/test-questions/{item_id}", response_model=AdminTestQuestionResponse)
def get_test_question(item_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, TestQuestion, item_id)


@router.post("/test-questions", response_model=AdminTestQuestionResponse, status_code=201)
def create_test_question(payload: AdminTestQuestionCreate, db: Session = Depends(get_db)):
    item = TestQuestion(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/test-questions/{item_id}", response_model=AdminTestQuestionResponse)
def update_test_question(item_id: int, payload: AdminTestQuestionUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, TestQuestion, item_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/test-questions/{item_id}")
def delete_test_question(item_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, TestQuestion, item_id)
    db.delete(item)
    db.commit()
    return {"message": "Test question deleted"}


# --- Test attempts ---


@router.get("/test-attempts", response_model=List[AdminTestAttemptResponse])
def list_test_attempts(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(TestAttempt).offset(skip).limit(limit).all()


@router.get("/test-attempts/{item_id}", response_model=AdminTestAttemptResponse)
def get_test_attempt(item_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, TestAttempt, item_id)


@router.post("/test-attempts", response_model=AdminTestAttemptResponse, status_code=201)
def create_test_attempt(payload: AdminTestAttemptCreate, db: Session = Depends(get_db)):
    item = TestAttempt(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/test-attempts/{item_id}", response_model=AdminTestAttemptResponse)
def update_test_attempt(item_id: int, payload: AdminTestAttemptUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, TestAttempt, item_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/test-attempts/{item_id}")
def delete_test_attempt(item_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, TestAttempt, item_id)
    db.delete(item)
    db.commit()
    return {"message": "Test attempt deleted"}


# --- Question attempts ---


@router.get("/question-attempts", response_model=List[AdminQuestionAttemptResponse])
def list_question_attempts(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(QuestionAttempt).offset(skip).limit(limit).all()


@router.get("/question-attempts/{item_id}", response_model=AdminQuestionAttemptResponse)
def get_question_attempt(item_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, QuestionAttempt, item_id)


@router.post("/question-attempts", response_model=AdminQuestionAttemptResponse, status_code=201)
def create_question_attempt(payload: AdminQuestionAttemptCreate, db: Session = Depends(get_db)):
    item = QuestionAttempt(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/question-attempts/{item_id}", response_model=AdminQuestionAttemptResponse)
def update_question_attempt(item_id: int, payload: AdminQuestionAttemptUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, QuestionAttempt, item_id)
    _apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/question-attempts/{item_id}")
def delete_question_attempt(item_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, QuestionAttempt, item_id)
    db.delete(item)
    db.commit()
    return {"message": "Question attempt deleted"}
