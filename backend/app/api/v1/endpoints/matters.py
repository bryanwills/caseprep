"""
Matter management endpoints for legal case organization.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import ValidationError, PermissionError
from app.models.matter import Matter, MatterParticipant, MatterNote, MatterDocument, MatterStatus, MatterPriority
from app.models.user import User
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


# Pydantic schemas for matter endpoints
from pydantic import BaseModel, Field
from datetime import datetime


class MatterCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    case_number: Optional[str] = Field(None, max_length=100)
    client_name: Optional[str] = Field(None, max_length=255)
    client_contact: Optional[str] = None
    opposing_party: Optional[str] = Field(None, max_length=255)
    opposing_counsel: Optional[str] = Field(None, max_length=255)
    priority: MatterPriority = MatterPriority.MEDIUM
    practice_area: Optional[str] = Field(None, max_length=100)
    court_name: Optional[str] = Field(None, max_length=255)
    judge_name: Optional[str] = Field(None, max_length=255)
    billing_rate: Optional[float] = None
    estimated_value: Optional[float] = None
    budget_limit: Optional[float] = None
    custom_fields: dict = {}
    tags: List[str] = []


class MatterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    case_number: Optional[str] = Field(None, max_length=100)
    client_name: Optional[str] = Field(None, max_length=255)
    client_contact: Optional[str] = None
    opposing_party: Optional[str] = Field(None, max_length=255)
    opposing_counsel: Optional[str] = Field(None, max_length=255)
    status: Optional[MatterStatus] = None
    priority: Optional[MatterPriority] = None
    practice_area: Optional[str] = Field(None, max_length=100)
    court_name: Optional[str] = Field(None, max_length=255)
    judge_name: Optional[str] = Field(None, max_length=255)
    billing_rate: Optional[float] = None
    estimated_value: Optional[float] = None
    budget_limit: Optional[float] = None
    custom_fields: Optional[dict] = None
    tags: Optional[List[str]] = None


class MatterResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    case_number: Optional[str] = None
    client_name: Optional[str] = None
    status: MatterStatus
    priority: MatterPriority
    practice_area: Optional[str] = None
    total_transcripts: int
    total_duration_hours: float
    total_storage_mb: float
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []
    
    class Config:
        from_attributes = True
        use_enum_values = True


@router.get("/", response_model=List[MatterResponse])
async def list_matters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[MatterStatus] = None,
    priority: Optional[MatterPriority] = None,
    practice_area: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all matters for the current user's tenant."""
    if not current_user.has_permission("matter:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read matters"
        )
    
    # Build query
    query = select(Matter).where(Matter.tenant_id == current_user.tenant_id)
    
    # Apply filters
    if status:
        query = query.where(Matter.status == status)
    if priority:
        query = query.where(Matter.priority == priority)
    if practice_area:
        query = query.where(Matter.practice_area == practice_area)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Matter.title.ilike(search_pattern),
                Matter.description.ilike(search_pattern),
                Matter.case_number.ilike(search_pattern),
                Matter.client_name.ilike(search_pattern)
            )
        )
    
    # Apply pagination and ordering
    query = query.order_by(Matter.updated_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    matters = result.scalars().all()
    
    return [MatterResponse.from_orm(matter) for matter in matters]


@router.post("/", response_model=MatterResponse, status_code=status.HTTP_201_CREATED)
async def create_matter(
    matter_data: MatterCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new matter."""
    if not current_user.has_permission("matter:create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create matters"
        )
    
    # Create new matter
    matter = Matter(
        tenant_id=current_user.tenant_id,
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
        **matter_data.dict()
    )
    
    db.add(matter)
    await db.commit()
    await db.refresh(matter)
    
    return MatterResponse.from_orm(matter)


@router.get("/{matter_id}", response_model=MatterResponse)
async def get_matter(
    matter_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific matter by ID."""
    if not current_user.has_permission("matter:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read matters"
        )
    
    query = select(Matter).where(
        and_(
            Matter.id == matter_id,
            Matter.tenant_id == current_user.tenant_id
        )
    ).options(
        selectinload(Matter.matter_participants),
        selectinload(Matter.media_assets),
        selectinload(Matter.transcripts)
    )
    
    result = await db.execute(query)
    matter = result.scalar_one_or_none()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found"
        )
    
    return MatterResponse.from_orm(matter)


@router.put("/{matter_id}", response_model=MatterResponse)
async def update_matter(
    matter_id: str,
    matter_data: MatterUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a matter."""
    if not current_user.has_permission("matter:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update matters"
        )
    
    # Get existing matter
    query = select(Matter).where(
        and_(
            Matter.id == matter_id,
            Matter.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    matter = result.scalar_one_or_none()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found"
        )
    
    # Update fields
    update_data = matter_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(matter, field, value)
    
    matter.updated_by_user_id = current_user.id
    
    await db.commit()
    await db.refresh(matter)
    
    return MatterResponse.from_orm(matter)


@router.delete("/{matter_id}")
async def delete_matter(
    matter_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a matter."""
    if not current_user.has_permission("matter:delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete matters"
        )
    
    # Get existing matter
    query = select(Matter).where(
        and_(
            Matter.id == matter_id,
            Matter.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    matter = result.scalar_one_or_none()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found"
        )
    
    # Check if matter has associated data
    if matter.total_transcripts > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete matter with associated transcripts. Archive it instead."
        )
    
    await db.delete(matter)
    await db.commit()
    
    return {"message": "Matter deleted successfully"}


@router.post("/{matter_id}/archive")
async def archive_matter(
    matter_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive a matter."""
    if not current_user.has_permission("matter:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to archive matters"
        )
    
    # Get existing matter
    query = select(Matter).where(
        and_(
            Matter.id == matter_id,
            Matter.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    matter = result.scalar_one_or_none()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found"
        )
    
    matter.status = MatterStatus.ARCHIVED
    matter.updated_by_user_id = current_user.id
    
    await db.commit()
    
    return {"message": "Matter archived successfully"}


@router.get("/stats/summary")
async def get_matter_stats(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get matter statistics summary."""
    if not current_user.has_permission("matter:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read matter statistics"
        )
    
    # Count matters by status
    status_query = select(
        Matter.status,
        func.count(Matter.id).label("count")
    ).where(
        Matter.tenant_id == current_user.tenant_id
    ).group_by(Matter.status)
    
    status_result = await db.execute(status_query)
    status_counts = {row.status: row.count for row in status_result}
    
    # Get totals
    totals_query = select(
        func.count(Matter.id).label("total_matters"),
        func.sum(Matter.total_transcripts).label("total_transcripts"),
        func.sum(Matter.total_duration_ms).label("total_duration_ms"),
        func.sum(Matter.total_storage_bytes).label("total_storage_bytes")
    ).where(Matter.tenant_id == current_user.tenant_id)
    
    totals_result = await db.execute(totals_query)
    totals = totals_result.first()
    
    return {
        "status_counts": status_counts,
        "total_matters": totals.total_matters or 0,
        "total_transcripts": totals.total_transcripts or 0,
        "total_duration_hours": (totals.total_duration_ms or 0) / (1000 * 60 * 60),
        "total_storage_gb": (totals.total_storage_bytes or 0) / (1024 * 1024 * 1024)
    }