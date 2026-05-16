from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
from app.db.database import get_db
from app.models.models import Package, UserPackage, User
from app.schemas.schemas import (
    PackageResponse, PackageCreate, PackageUpdate,
    UserPackageResponse, UserPackageUpdate
)
from app.routers.auth import get_current_user
from app.deps.admin import require_admin

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


@router.post("/", response_model=PackageResponse)
async def create_package(
    package: PackageCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create a new package"""
    logger.info(f"Creating package: {package.name}")
    try:
        db_package = Package(
            name=package.name,
            description=package.description,
            test_count=package.test_count,
            price=package.price,
            is_active=package.is_active
        )
        db.add(db_package)
        db.commit()
        db.refresh(db_package)
        logger.info(f"✅ Package created with ID: {db_package.id}")
        return db_package
    except Exception as e:
        logger.error(f"Error creating package: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating package: {str(e)}")


@router.put("/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: int,
    package: PackageUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Update a package"""
    logger.info(f"Updating package {package_id}")
    try:
        db_package = db.query(Package).filter(Package.id == package_id).first()
        if not db_package:
            logger.warning(f"Package {package_id} not found")
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Update fields if provided
        if package.name is not None:
            db_package.name = package.name
        if package.description is not None:
            db_package.description = package.description
        if package.test_count is not None:
            db_package.test_count = package.test_count
        if package.price is not None:
            db_package.price = package.price
        if package.is_active is not None:
            db_package.is_active = package.is_active
        
        db.commit()
        db.refresh(db_package)
        logger.info(f"✅ Package {package_id} updated")
        return db_package
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating package: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating package: {str(e)}")


@router.delete("/{package_id}")
async def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Delete a package (soft delete by setting is_active=False)"""
    logger.info(f"Deleting package {package_id}")
    try:
        db_package = db.query(Package).filter(Package.id == package_id).first()
        if not db_package:
            logger.warning(f"Package {package_id} not found")
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Soft delete
        db_package.is_active = False
        db.commit()
        logger.info(f"✅ Package {package_id} soft deleted")
        return {"message": "Package deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting package: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting package: {str(e)}")


@router.put("/user-packages/{user_package_id}", response_model=UserPackageResponse)
async def update_user_package(
    user_package_id: int,
    user_package: UserPackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a user package (only for current user's packages)"""
    logger.info(f"Updating user package {user_package_id} for user {current_user.id}")
    try:
        db_user_package = db.query(UserPackage).filter(
            UserPackage.id == user_package_id,
            UserPackage.user_id == current_user.id
        ).first()
        
        if not db_user_package:
            logger.warning(f"User package {user_package_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="User package not found")
        
        if user_package.tests_remaining is not None:
            db_user_package.tests_remaining = user_package.tests_remaining
        if user_package.expires_at is not None:
            db_user_package.expires_at = user_package.expires_at
        
        db.commit()
        db.refresh(db_user_package)
        logger.info(f"✅ User package {user_package_id} updated")
        return db_user_package
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user package: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating user package: {str(e)}")


@router.delete("/user-packages/{user_package_id}")
async def delete_user_package(
    user_package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a user package (only for current user's packages)"""
    logger.info(f"Deleting user package {user_package_id} for user {current_user.id}")
    try:
        db_user_package = db.query(UserPackage).filter(
            UserPackage.id == user_package_id,
            UserPackage.user_id == current_user.id
        ).first()
        
        if not db_user_package:
            logger.warning(f"User package {user_package_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="User package not found")
        
        db.delete(db_user_package)
        db.commit()
        logger.info(f"✅ User package {user_package_id} deleted")
        return {"message": "User package deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user package: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting user package: {str(e)}")

