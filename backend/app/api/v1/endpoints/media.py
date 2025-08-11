"""
Media asset management endpoints for file uploads and processing.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.media import MediaAsset, MediaStatus, MediaType
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


class MediaAssetResponse(BaseModel):
    id: str
    matter_id: str
    original_filename: str
    file_type: MediaType
    mime_type: str
    file_size: int
    file_size_mb: float
    duration_seconds: float
    status: MediaStatus
    language: str
    speaker_diarization: bool
    is_confidential: bool
    can_transcribe: bool
    is_processed: bool
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []
    
    class Config:
        from_attributes = True
        use_enum_values = True


class MediaAssetUpdate(BaseModel):
    language: Optional[str] = Field(None, max_length=10)
    speaker_diarization: Optional[bool] = None
    is_confidential: Optional[bool] = None
    delete_after_transcription: Optional[bool] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[dict] = None


class TranscriptionRequest(BaseModel):
    language: Optional[str] = Field(None, max_length=10)
    auto_detect_language: bool = True
    speaker_diarization: bool = True
    model: Optional[str] = Field("whisper-large-v3", max_length=100)


@router.get("/", response_model=List[MediaAssetResponse])
async def list_media_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    matter_id: Optional[str] = None,
    file_type: Optional[MediaType] = None,
    status: Optional[MediaStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List media assets for the current user's tenant."""
    if not current_user.has_permission("transcript:read"):  # Media is part of transcription workflow
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read media assets"
        )
    
    # Build query
    query = select(MediaAsset).where(MediaAsset.tenant_id == current_user.tenant_id)
    
    # Apply filters
    if matter_id:
        query = query.where(MediaAsset.matter_id == matter_id)
    if file_type:
        query = query.where(MediaAsset.file_type == file_type)
    if status:
        query = query.where(MediaAsset.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(MediaAsset.original_filename.ilike(search_pattern))
    
    # Apply pagination and ordering
    query = query.order_by(MediaAsset.updated_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    media_assets = result.scalars().all()
    
    return [MediaAssetResponse.from_orm(asset) for asset in media_assets]


@router.post("/upload", response_model=MediaAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_media_file(
    matter_id: str,
    file: UploadFile = File(...),
    language: str = "en",
    speaker_diarization: bool = True,
    is_confidential: bool = False,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a media file for transcription."""
    if not current_user.has_permission("transcript:create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to upload media files"
        )
    
    # Verify matter exists and belongs to user's tenant
    from app.models.matter import Matter
    matter_query = select(Matter).where(
        and_(
            Matter.id == matter_id,
            Matter.tenant_id == current_user.tenant_id
        )
    )
    matter_result = await db.execute(matter_query)
    matter = matter_result.scalar_one_or_none()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found"
        )
    
    # Validate file type
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is required"
        )
    
    # Determine media type
    if file.content_type.startswith("audio/"):
        media_type = MediaType.AUDIO
    elif file.content_type.startswith("video/"):
        media_type = MediaType.VIDEO
    elif file.content_type in ["application/pdf", "text/plain", "application/msword"]:
        media_type = MediaType.DOCUMENT
    elif file.content_type.startswith("image/"):
        media_type = MediaType.IMAGE
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type"
        )
    
    # Read file content for hashing
    file_content = await file.read()
    file_size = len(file_content)
    
    # Generate content hash
    import hashlib
    content_hash = hashlib.sha256(file_content).hexdigest()
    
    # Check for duplicate files
    duplicate_query = select(MediaAsset).where(
        and_(
            MediaAsset.tenant_id == current_user.tenant_id,
            MediaAsset.content_hash == content_hash
        )
    )
    duplicate_result = await db.execute(duplicate_query)
    duplicate_asset = duplicate_result.scalar_one_or_none()
    
    if duplicate_asset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file with identical content already exists"
        )
    
    # TODO: Implement actual file storage (local, S3, etc.)
    # For now, we'll just simulate the storage path
    storage_path = f"uploads/{current_user.tenant_id}/{matter_id}/{file.filename}"
    
    # Create media asset record
    media_asset = MediaAsset(
        tenant_id=current_user.tenant_id,
        matter_id=matter_id,
        original_filename=file.filename,
        file_type=media_type,
        mime_type=file.content_type,
        file_size=file_size,
        storage_path=storage_path,
        content_hash=content_hash,
        language=language,
        speaker_diarization=speaker_diarization,
        is_confidential=is_confidential,
        status=MediaStatus.UPLOADED,
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id
    )
    
    db.add(media_asset)
    await db.commit()
    await db.refresh(media_asset)
    
    # TODO: Trigger background transcription task for audio/video files
    if media_asset.can_transcribe:
        # This would typically trigger a Celery task
        pass
    
    return MediaAssetResponse.from_orm(media_asset)


@router.get("/{media_id}", response_model=MediaAssetResponse)
async def get_media_asset(
    media_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific media asset by ID."""
    if not current_user.has_permission("transcript:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read media assets"
        )
    
    query = select(MediaAsset).where(
        and_(
            MediaAsset.id == media_id,
            MediaAsset.tenant_id == current_user.tenant_id
        )
    )
    
    result = await db.execute(query)
    media_asset = result.scalar_one_or_none()
    
    if not media_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media asset not found"
        )
    
    return MediaAssetResponse.from_orm(media_asset)


@router.put("/{media_id}", response_model=MediaAssetResponse)
async def update_media_asset(
    media_id: str,
    media_data: MediaAssetUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a media asset."""
    if not current_user.has_permission("transcript:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update media assets"
        )
    
    # Get existing media asset
    query = select(MediaAsset).where(
        and_(
            MediaAsset.id == media_id,
            MediaAsset.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    media_asset = result.scalar_one_or_none()
    
    if not media_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media asset not found"
        )
    
    # Update fields
    update_data = media_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "tags" and value is not None:
            media_asset.tags = value
        elif field == "custom_fields" and value is not None:
            media_asset.custom_fields = value
        elif hasattr(media_asset, field):
            setattr(media_asset, field, value)
    
    media_asset.updated_by_user_id = current_user.id
    
    await db.commit()
    await db.refresh(media_asset)
    
    return MediaAssetResponse.from_orm(media_asset)


@router.post("/{media_id}/transcribe")
async def start_transcription(
    media_id: str,
    transcription_request: TranscriptionRequest,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start transcription for a media asset."""
    if not current_user.has_permission("transcript:create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to start transcription"
        )
    
    # Get media asset
    query = select(MediaAsset).where(
        and_(
            MediaAsset.id == media_id,
            MediaAsset.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    media_asset = result.scalar_one_or_none()
    
    if not media_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media asset not found"
        )
    
    if not media_asset.can_transcribe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media asset cannot be transcribed (not audio or video)"
        )
    
    if media_asset.status == MediaStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcription is already in progress"
        )
    
    if media_asset.status == MediaStatus.TRANSCRIBED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media asset has already been transcribed"
        )
    
    # Update media asset with transcription settings
    media_asset.language = transcription_request.language or media_asset.language
    media_asset.auto_detect_language = transcription_request.auto_detect_language
    media_asset.speaker_diarization = transcription_request.speaker_diarization
    media_asset.set_processing_status(MediaStatus.PROCESSING)
    
    await db.commit()
    
    # TODO: Trigger background transcription task
    # This would typically trigger a Celery task with the media_asset.id
    
    return {"message": "Transcription started successfully", "media_id": media_id}


@router.delete("/{media_id}")
async def delete_media_asset(
    media_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a media asset."""
    if not current_user.has_permission("transcript:delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete media assets"
        )
    
    # Get existing media asset
    query = select(MediaAsset).where(
        and_(
            MediaAsset.id == media_id,
            MediaAsset.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    media_asset = result.scalar_one_or_none()
    
    if not media_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media asset not found"
        )
    
    # Check if media has associated transcripts
    if media_asset.transcripts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete media asset with associated transcripts"
        )
    
    # TODO: Delete actual file from storage
    
    await db.delete(media_asset)
    await db.commit()
    
    return {"message": "Media asset deleted successfully"}


@router.get("/{media_id}/download")
async def download_media_file(
    media_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download a media file."""
    if not current_user.has_permission("transcript:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to download media files"
        )
    
    # Get media asset
    query = select(MediaAsset).where(
        and_(
            MediaAsset.id == media_id,
            MediaAsset.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    media_asset = result.scalar_one_or_none()
    
    if not media_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media asset not found"
        )
    
    # TODO: Implement actual file streaming/download
    # This would typically return a FileResponse or generate a signed URL
    
    return {
        "download_url": media_asset.get_storage_url(signed=True),
        "filename": media_asset.original_filename,
        "content_type": media_asset.mime_type
    }