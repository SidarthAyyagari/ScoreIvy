from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import Package
from app.schemas.schemas import PackageResponse

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

