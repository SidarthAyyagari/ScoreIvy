from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import logging
from app.db.database import get_db
from app.models.models import Exam, Package, UserPackage, User
from app.schemas.schemas import PackageResponse, PackageCreate, PackageUpdate
from app.routers.auth import get_current_user
from app.deps.admin import require_admin
from app.services.entitlements import is_expired

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[PackageResponse])
async def get_packages(
    exam: Optional[str] = Query(None, description="Exam slug to filter by"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get active packages, optionally for one exam"""
    query = db.query(Package).filter(Package.is_active == True)
    if exam:
        query = query.join(Exam, Package.exam_id == Exam.id).filter(Exam.slug == exam)
    return query.order_by(Package.price).offset(skip).limit(limit).all()


@router.get("/{package_id}", response_model=PackageResponse)
async def get_package(
    package_id: int,
    db: Session = Depends(get_db)
):
    """Get a package by ID"""
    package = db.query(Package).filter(Package.id == package_id, Package.is_active == True).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


@router.get("/user/purchased")
async def get_user_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all packages purchased by current user with package details"""
    user_packages = (
        db.query(UserPackage)
        .options(joinedload(UserPackage.package))
        .filter(UserPackage.user_id == current_user.id)
        .order_by(UserPackage.purchased_at.desc())
        .all()
    )

    result = []
    for user_pkg in user_packages:
        result.append({
            "id": user_pkg.id,
            "package_id": user_pkg.package_id,
            "tests_remaining": user_pkg.tests_remaining,
            "purchased_at": user_pkg.purchased_at,
            "expires_at": user_pkg.expires_at,
            "is_expired": is_expired(user_pkg),
            "exam": {
                "id": user_pkg.package.exam.id,
                "slug": user_pkg.package.exam.slug,
                "name": user_pkg.package.exam.name,
            } if user_pkg.package and user_pkg.package.exam else None,
            "package": {
                "id": user_pkg.package.id,
                "name": user_pkg.package.name,
                "description": user_pkg.package.description,
                "test_count": user_pkg.package.test_count,
                "price": user_pkg.package.price,
                "validity_days": user_pkg.package.validity_days,
                "is_active": user_pkg.package.is_active
            } if user_pkg.package else None
        })

    return result


@router.post("/", response_model=PackageResponse)
async def create_package(
    package: PackageCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create a new package"""
    db_package = Package(**package.model_dump())
    db.add(db_package)
    db.commit()
    db.refresh(db_package)
    logger.info(f"✅ Package created with ID: {db_package.id}")
    return db_package


@router.put("/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: int,
    package: PackageUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Update a package"""
    db_package = db.query(Package).filter(Package.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="Package not found")

    for key, value in package.model_dump(exclude_unset=True).items():
        # validity_days=None is meaningful ("never expires"); other None values mean "unchanged".
        if value is not None or key == "validity_days":
            setattr(db_package, key, value)

    db.commit()
    db.refresh(db_package)
    logger.info(f"✅ Package {package_id} updated")
    return db_package


@router.delete("/{package_id}")
async def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Delete a package (soft delete by setting is_active=False)"""
    db_package = db.query(Package).filter(Package.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="Package not found")

    db_package.is_active = False
    db.commit()
    logger.info(f"✅ Package {package_id} soft deleted")
    return {"message": "Package deleted successfully"}
