"""
Transcript management endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.transcript import Transcript, TranscriptSegment, TranscriptStatus, TranscriptFormat, SpeakerRole
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


class TranscriptResponse(BaseModel):
    id: str
    matter_id: str
    media_asset_id: str
    title: str
    content: Optional[str] = None
    status: TranscriptStatus
    format: TranscriptFormat
    language: str
    confidence_score: Optional[float] = None
    word_count: int
    segment_count: int
    speaker_count: int
    processing_duration_ms: Optional[int] = None
    is_completed: bool
    has_speakers: bool
    words_per_minute: float
    duration_minutes: float
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []
    
    class Config:
        from_attributes = True
        use_enum_values = True


class TranscriptSegmentResponse(BaseModel):
    id: str
    segment_index: int
    start_time: int
    end_time: int
    duration: int
    text: str
    speaker_id: Optional[str] = None
    speaker_name: Optional[str] = None
    speaker_role: SpeakerRole
    confidence: Optional[float] = None
    word_count: int
    is_edited: bool
    start_time_formatted: str
    end_time_formatted: str
    display_speaker: str
    
    class Config:
        from_attributes = True
        use_enum_values = True


class TranscriptUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    format: Optional[TranscriptFormat] = None
    is_privileged: Optional[bool] = None
    is_confidential: Optional[bool] = None
    retention_override_days: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[dict] = None


class SegmentUpdate(BaseModel):
    text: str = Field(..., min_length=1)


class SpeakerAssignment(BaseModel):
    speaker_name: str = Field(..., min_length=1, max_length=255)
    speaker_role: Optional[SpeakerRole] = None


@router.get("/", response_model=List[TranscriptResponse])
async def list_transcripts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    matter_id: Optional[str] = None,
    status: Optional[TranscriptStatus] = None,
    language: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List transcripts for the current user's tenant."""
    if not current_user.has_permission("transcript:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read transcripts"
        )
    
    # Build query
    query = select(Transcript).where(Transcript.tenant_id == current_user.tenant_id)
    
    # Apply filters
    if matter_id:
        query = query.where(Transcript.matter_id == matter_id)
    if status:
        query = query.where(Transcript.status == status)
    if language:
        query = query.where(Transcript.language == language)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Transcript.title.ilike(search_pattern),
                Transcript.content.ilike(search_pattern),
                Transcript.notes.ilike(search_pattern)
            )
        )
    
    # Apply pagination and ordering
    query = query.order_by(Transcript.updated_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    transcripts = result.scalars().all()
    
    return [TranscriptResponse.from_orm(transcript) for transcript in transcripts]


@router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(
    transcript_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific transcript by ID."""
    if not current_user.has_permission("transcript:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read transcripts"
        )
    
    query = select(Transcript).where(
        and_(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
    ).options(
        selectinload(Transcript.segments),
        selectinload(Transcript.matter),
        selectinload(Transcript.media_asset)
    )
    
    result = await db.execute(query)
    transcript = result.scalar_one_or_none()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Increment view count
    transcript.increment_view_count()
    await db.commit()
    
    return TranscriptResponse.from_orm(transcript)


@router.put("/{transcript_id}", response_model=TranscriptResponse)
async def update_transcript(
    transcript_id: str,
    transcript_data: TranscriptUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a transcript."""
    if not current_user.has_permission("transcript:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update transcripts"
        )
    
    # Get existing transcript
    query = select(Transcript).where(
        and_(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    transcript = result.scalar_one_or_none()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Update fields
    update_data = transcript_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "tags" and value is not None:
            transcript.tags = value
        elif field == "custom_fields" and value is not None:
            transcript.custom_fields = value
        elif hasattr(transcript, field):
            setattr(transcript, field, value)
    
    transcript.updated_by_user_id = current_user.id
    
    await db.commit()
    await db.refresh(transcript)
    
    return TranscriptResponse.from_orm(transcript)


@router.get("/{transcript_id}/segments", response_model=List[TranscriptSegmentResponse])
async def get_transcript_segments(
    transcript_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    speaker_id: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get segments for a specific transcript."""
    if not current_user.has_permission("transcript:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read transcripts"
        )
    
    # Verify transcript exists and belongs to user's tenant
    transcript_query = select(Transcript).where(
        and_(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
    )
    transcript_result = await db.execute(transcript_query)
    transcript = transcript_result.scalar_one_or_none()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Build segments query
    query = select(TranscriptSegment).where(TranscriptSegment.transcript_id == transcript_id)
    
    if speaker_id:
        query = query.where(TranscriptSegment.speaker_id == speaker_id)
    
    # Apply pagination and ordering
    query = query.order_by(TranscriptSegment.segment_index).offset(skip).limit(limit)
    
    result = await db.execute(query)
    segments = result.scalars().all()
    
    return [TranscriptSegmentResponse.from_orm(segment) for segment in segments]


@router.put("/{transcript_id}/segments/{segment_id}/text")
async def update_segment_text(
    transcript_id: str,
    segment_id: str,
    segment_data: SegmentUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update the text of a transcript segment."""
    if not current_user.has_permission("transcript:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update transcripts"
        )
    
    # Get segment and verify it belongs to the transcript and tenant
    query = select(TranscriptSegment).join(Transcript).where(
        and_(
            TranscriptSegment.id == segment_id,
            TranscriptSegment.transcript_id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    segment = result.scalar_one_or_none()
    
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript segment not found"
        )
    
    # Update segment text
    segment.edit_text(segment_data.text, str(current_user.id))
    
    await db.commit()
    
    return {"message": "Segment text updated successfully"}


@router.put("/{transcript_id}/segments/{segment_id}/speaker")
async def assign_speaker(
    transcript_id: str,
    segment_id: str,
    speaker_data: SpeakerAssignment,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a speaker name to a transcript segment."""
    if not current_user.has_permission("transcript:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update transcripts"
        )
    
    # Get segment and verify it belongs to the transcript and tenant
    query = select(TranscriptSegment).join(Transcript).where(
        and_(
            TranscriptSegment.id == segment_id,
            TranscriptSegment.transcript_id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    segment = result.scalar_one_or_none()
    
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript segment not found"
        )
    
    # Assign speaker
    segment.assign_speaker(speaker_data.speaker_name, speaker_data.speaker_role)
    
    await db.commit()
    
    return {"message": "Speaker assigned successfully"}


@router.post("/{transcript_id}/approve")
async def approve_transcript(
    transcript_id: str,
    notes: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a transcript."""
    if not current_user.has_permission("transcript:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to approve transcripts"
        )
    
    # Get transcript
    query = select(Transcript).where(
        and_(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    transcript = result.scalar_one_or_none()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    if not transcript.is_reviewable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript is not in a reviewable state"
        )
    
    # Approve transcript
    transcript.approve(str(current_user.id), notes)
    
    await db.commit()
    
    return {"message": "Transcript approved successfully"}


@router.get("/{transcript_id}/export/{format}")
async def export_transcript(
    transcript_id: str,
    format: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export transcript in various formats."""
    if not current_user.has_permission("export:create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to export transcripts"
        )
    
    # Validate format
    if format not in ["txt", "pdf", "docx", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format"
        )
    
    # Get transcript with segments
    query = select(Transcript).where(
        and_(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
    ).options(selectinload(Transcript.segments))
    
    result = await db.execute(query)
    transcript = result.scalar_one_or_none()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Mark as exported
    transcript.mark_exported(format)
    transcript.increment_download_count()
    
    await db.commit()
    
    # TODO: Implement actual export generation
    # This would typically generate the file and return it or a download link
    
    return {
        "message": f"Transcript export in {format} format initiated",
        "download_url": f"/api/v1/transcripts/{transcript_id}/download/{format}"
    }