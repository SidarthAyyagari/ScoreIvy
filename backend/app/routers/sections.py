from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
from app.db.database import get_db
from app.models.models import Section
from app.schemas.schemas import SectionCreate, SectionUpdate, SectionResponse
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[SectionResponse])
async def get_sections(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all sections"""
    logger.info(f"Fetching sections (skip={skip}, limit={limit})")
    sections = db.query(Section).offset(skip).limit(limit).all()
    return sections


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: int,
    db: Session = Depends(get_db)
):
    """Get a section by ID"""
    logger.info(f"Fetching section {section_id}")
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        logger.warning(f"Section {section_id} not found")
        raise HTTPException(status_code=404, detail="Section not found")
    return section


@router.post("/", response_model=SectionResponse)
async def create_section(
    section: SectionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new section"""
    logger.info(f"Creating section: {section.name}")
    try:
        db_section = Section(
            name=section.name,
            description=section.description
        )
        db.add(db_section)
        db.commit()
        db.refresh(db_section)
        logger.info(f"✅ Section created with ID: {db_section.id}")
        return db_section
    except Exception as e:
        logger.error(f"Error creating section: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating section: {str(e)}")


@router.put("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: int,
    section: SectionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a section"""
    logger.info(f"Updating section {section_id}")
    try:
        db_section = db.query(Section).filter(Section.id == section_id).first()
        if not db_section:
            logger.warning(f"Section {section_id} not found")
            raise HTTPException(status_code=404, detail="Section not found")
        
        if section.name is not None:
            db_section.name = section.name
        if section.description is not None:
            db_section.description = section.description
        
        db.commit()
        db.refresh(db_section)
        logger.info(f"✅ Section {section_id} updated")
        return db_section
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating section: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating section: {str(e)}")


@router.delete("/{section_id}")
async def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a section"""
    logger.info(f"Deleting section {section_id}")
    try:
        db_section = db.query(Section).filter(Section.id == section_id).first()
        if not db_section:
            logger.warning(f"Section {section_id} not found")
            raise HTTPException(status_code=404, detail="Section not found")
        
        db.delete(db_section)
        db.commit()
        logger.info(f"✅ Section {section_id} deleted")
        return {"message": "Section deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting section: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting section: {str(e)}")

