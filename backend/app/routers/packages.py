from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
from app.db.database import get_db
from app.models.models import Package, UserPackage, User
from app.schemas.schemas import PackageResponse, UserPackageResponse
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[PackageResponse])
async def get_packages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all active packages"""
    packages = db.query(Package).filter(Package.is_active == True).offset(skip).limit(limit).all()
    return packages


@router.get("/{package_id}", response_model=PackageResponse)
async def get_package(
    package_id: int,
    db: Session = Depends(get_db)
):
    """Get a package by ID"""
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


@router.get("/user/purchased")
async def get_user_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all packages purchased by current user with package details"""
    from sqlalchemy.orm import joinedload
    user_packages = (
        db.query(UserPackage)
        .options(joinedload(UserPackage.package))
        .filter(UserPackage.user_id == current_user.id)
        .all()
    )
    
    # Convert to response format
    result = []
    for user_pkg in user_packages:
        result.append({
            "id": user_pkg.id,
            "package_id": user_pkg.package_id,
            "tests_remaining": user_pkg.tests_remaining,
            "purchased_at": user_pkg.purchased_at,
            "expires_at": user_pkg.expires_at,
            "package": {
                "id": user_pkg.package.id,
                "name": user_pkg.package.name,
                "description": user_pkg.package.description,
                "test_count": user_pkg.package.test_count,
                "price": user_pkg.package.price,
                "is_active": user_pkg.package.is_active
            } if user_pkg.package else None
        })
    
    return result


@router.post("/{package_id}/purchase", response_model=UserPackageResponse)
async def purchase_package(
    package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Purchase a package for the current user"""
    try:
        logger.info(f"Purchase attempt: User {current_user.id} attempting to purchase package {package_id}")
        
        # Get package
        package = db.query(Package).filter(Package.id == package_id).first()
        if not package:
            logger.warning(f"Package {package_id} not found")
            raise HTTPException(status_code=404, detail="Package not found")
        
        if not package.is_active:
            logger.warning(f"Package {package_id} is not active")
            raise HTTPException(status_code=400, detail="Package is not available")
        
        # Create user package
        user_package = UserPackage(
            user_id=current_user.id,
            package_id=package.id,
            tests_remaining=package.test_count
        )
        db.add(user_package)
        db.commit()
        db.refresh(user_package)
        
        logger.info(f"Successfully purchased package {package_id} for user {current_user.id}, user_package_id: {user_package.id}")
        return user_package
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing package: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

