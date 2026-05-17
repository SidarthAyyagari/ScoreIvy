"""Admin-only CRUD API for all database tables."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Type, TypeVar, Any, Optional
import logging

from app.db.database import get_db
from app.deps.admin import require_admin
from app.models.models import (
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
    QuestionCreate,
    QuestionUpdate,
)
from app.schemas.admin_schemas import (
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
    AdminQuestionResponse,
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


# --- Questions ---


@router.get("/questions", response_model=List[AdminQuestionResponse])
def list_questions(
    skip: int = 0,
    limit: int = 200,
    section_id: Optional[int] = None,
    include_inactive: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Question)
    if section_id is not None:
        query = query.filter(Question.section_id == section_id)
    if not include_inactive:
        query = query.filter(Question.is_active == True)
    return query.offset(skip).limit(limit).all()


@router.get("/questions/{question_id}", response_model=AdminQuestionResponse)
def get_question(question_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Question, question_id)


@router.post("/questions", response_model=AdminQuestionResponse, status_code=201)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    if payload.section_id is not None:
        _get_or_404(db, Section, payload.section_id)
    item = Question(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/questions/{question_id}", response_model=AdminQuestionResponse)
def update_question(question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, Question, question_id)
    data = payload.model_dump(exclude_unset=True)
    if "section_id" in data and data["section_id"] is not None:
        _get_or_404(db, Section, data["section_id"])
    _apply_updates(item, data)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, Question, question_id)
    item.is_active = False
    db.commit()
    return {"message": "Question deactivated"}


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
