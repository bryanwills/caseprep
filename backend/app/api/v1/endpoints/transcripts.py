"""
Transcript management endpoints.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import User
from app.models.transcript import Transcript, TranscriptSegment, TranscriptStatus
from app.models.matter import Matter
from app.models.media import MediaAsset
from app.services.auth_service import AuthService
from app.services.transcription_service import TranscriptionService, TranscriptionConfig
from app.services.export_service import ExportService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
transcription_service = TranscriptionService()
export_service = ExportService()


class TranscriptResponse(BaseModel):
    """Transcript response model."""
    id: str
    matterId: str
    title: Optional[str] = None
    language: str
    asrModel: str
    diarizationModel: Optional[str] = None
    totalDurationMs: int
    version: int
    encrypted: bool
    segments: List[dict]
    speakerMap: dict
    mediaUrl: Optional[str] = None
    createdAt: str
    updatedAt: str

    class Config:
        from_attributes = True


class TranscriptCreate(BaseModel):
    """Transcript creation model."""
    matterId: str
    title: Optional[str] = None
    language: str = "en"
    enableDiarization: bool = True
    enableWordTiming: bool = True
    customDictionary: Optional[dict] = None


class TranscriptUpdate(BaseModel):
    """Transcript update model."""
    title: Optional[str] = None
    segments: Optional[List[dict]] = None
    speakerMap: Optional[dict] = None


class ExportRequest(BaseModel):
    """Export request model."""
    format: str
    options: dict = Field(default_factory=dict)


class ClipRequest(BaseModel):
    """Clip creation request model."""
    startMs: int
    endMs: int
    title: Optional[str] = None
    description: Optional[str] = None
    includeVideo: bool = True
    includeAudio: bool = True
    includeTranscript: bool = True


@router.get("/", response_model=List[TranscriptResponse])
async def list_transcripts(
    matter_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List transcripts for the current user's tenant."""
    try:
        # Build query
        query = select(Transcript).where(Transcript.tenant_id == current_user.tenant_id)

        if matter_id:
            query = query.where(Transcript.matter_id == matter_id)

        if status:
            query = query.where(Transcript.status == status)

        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        transcripts = result.scalars().all()

        return [TranscriptResponse.from_orm(t) for t in transcripts]

    except Exception as e:
        logger.error(f"Failed to list transcripts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transcripts"
        )


@router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(
    transcript_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific transcript by ID."""
    try:
        query = select(Transcript).where(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
        result = await db.execute(query)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )

        return TranscriptResponse.from_orm(transcript)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transcript {transcript_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transcript"
        )


@router.post("/", response_model=TranscriptResponse)
async def create_transcript(
    transcript_data: TranscriptCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new transcript."""
    try:
        # Verify matter exists and user has access
        matter_query = select(Matter).where(
            Matter.id == transcript_data.matterId,
            Matter.tenant_id == current_user.tenant_id
        )
        matter_result = await db.execute(matter_query)
        matter = matter_result.scalar_one_or_none()

        if not matter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matter not found"
            )

        # Create transcript record
        transcript = Transcript(
            tenant_id=current_user.tenant_id,
            matter_id=transcript_data.matterId,
            title=transcript_data.title,
            language=transcript_data.language,
            asr_model=settings.WHISPER_MODEL_SIZE,
            diarization_model=settings.PYANNOTE_MODEL if transcript_data.enableDiarization else None,
            total_duration_ms=0,
            version=1,
            encrypted=False,
            segments=[],
            speaker_map={}
        )

        db.add(transcript)
        await db.commit()
        await db.refresh(transcript)

        return TranscriptResponse.from_orm(transcript)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create transcript: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transcript"
        )


@router.put("/{transcript_id}", response_model=TranscriptResponse)
async def update_transcript(
    transcript_id: str,
    transcript_data: TranscriptUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a transcript."""
    try:
        # Get transcript
        query = select(Transcript).where(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
        result = await db.execute(query)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )

        # Update fields
        if transcript_data.title is not None:
            transcript.title = transcript_data.title

        if transcript_data.segments is not None:
            transcript.segments = transcript_data.segments

        if transcript_data.speakerMap is not None:
            transcript.speaker_map = transcript_data.speakerMap

        await db.commit()
        await db.refresh(transcript)

        return TranscriptResponse.from_orm(transcript)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update transcript {transcript_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transcript"
        )


@router.delete("/{transcript_id}")
async def delete_transcript(
    transcript_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a transcript."""
    try:
        # Get transcript
        query = select(Transcript).where(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
        result = await db.execute(query)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )

        # Delete transcript
        await db.delete(transcript)
        await db.commit()

        return {"message": "Transcript deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete transcript {transcript_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete transcript"
        )


@router.post("/{transcript_id}/transcribe")
async def start_transcription(
    transcript_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start transcription for a transcript."""
    try:
        # Get transcript
        query = select(Transcript).where(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
        result = await db.execute(query)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )

        # Get associated media
        media_query = select(MediaAsset).where(
            MediaAsset.matter_id == transcript.matter_id,
            MediaAsset.tenant_id == current_user.tenant_id
        )
        media_result = await db.execute(media_query)
        media = media_result.scalar_one_or_none()

        if not media:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No media found for this transcript"
            )

        # Update transcript status
        transcript.status = TranscriptStatus.PROCESSING
        await db.commit()

        # Start transcription in background
        background_tasks.add_task(
            _process_transcription,
            transcript_id,
            media.storage_uri,
            current_user.tenant_id
        )

        return {"message": "Transcription started successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start transcription for {transcript_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start transcription"
        )


@router.post("/{transcript_id}/export")
async def export_transcript(
    transcript_id: str,
    export_request: ExportRequest,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export transcript in the specified format."""
    try:
        # Get transcript
        query = select(Transcript).where(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
        result = await db.execute(query)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )

        # Get associated matter
        matter_query = select(Matter).where(
            Matter.id == transcript.matter_id,
            Matter.tenant_id == current_user.tenant_id
        )
        matter_result = await db.execute(matter_query)
        matter = matter_result.scalar_one_or_none()

        # Export transcript
        export_path = await export_service.export_transcript(
            transcript=transcript,
            format=export_request.format,
            options=export_request.options,
            matter=matter
        )

        # In production, this would return a download URL
        return {
            "message": "Export completed successfully",
            "format": export_request.format,
            "file_path": export_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export transcript {transcript_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export transcript"
        )


@router.post("/{transcript_id}/clips")
async def create_clip(
    transcript_id: str,
    clip_request: ClipRequest,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a clip from the transcript."""
    try:
        # Get transcript
        query = select(Transcript).where(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
        result = await db.execute(query)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )

        # Validate time range
        if clip_request.startMs >= clip_request.endMs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time"
            )

        if clip_request.startMs < 0 or clip_request.endMs > transcript.totalDurationMs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time range out of bounds"
            )

        # Create clip
        clip_path = await transcription_service.create_clip(
            transcript=transcript,
            start_ms=clip_request.startMs,
            end_ms=clip_request.endMs,
            include_video=clip_request.includeVideo,
            include_audio=clip_request.includeAudio
        )

        return {
            "message": "Clip created successfully",
            "clip_path": clip_path,
            "start_ms": clip_request.startMs,
            "end_ms": clip_request.endMs,
            "duration_ms": clip_request.endMs - clip_request.startMs
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create clip for {transcript_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create clip"
        )


@router.get("/{transcript_id}/status")
async def get_transcript_status(
    transcript_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the status of a transcript."""
    try:
        query = select(Transcript).where(
            Transcript.id == transcript_id,
            Transcript.tenant_id == current_user.tenant_id
        )
        result = await db.execute(query)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )

        return {
            "id": transcript.id,
            "status": transcript.status,
            "progress": getattr(transcript, 'progress', 0),
            "error": getattr(transcript, 'error', None),
            "created_at": transcript.created_at,
            "updated_at": transcript.updated_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for {transcript_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transcript status"
        )


async def _process_transcription(
    transcript_id: str,
    media_path: str,
    tenant_id: str
):
    """Background task to process transcription."""
    try:
        logger.info(f"Starting transcription for {transcript_id}")

        # Configure transcription
        config = TranscriptionConfig(
            language="en",
            model_size=settings.WHISPER_MODEL_SIZE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
            device=settings.WHISPER_DEVICE,
            enable_diarization=settings.ENABLE_DIARIZATION,
            enable_word_timing=True
        )

        # Run transcription
        result = await transcription_service.transcribe_media(media_path, config)

        # Update transcript in database
        # This would require a database session, so we'd need to handle this differently
        # For now, just log the result
        logger.info(f"Transcription completed for {transcript_id}: {len(result.segments)} segments")

    except Exception as e:
        logger.error(f"Transcription failed for {transcript_id}: {e}")
        # Update transcript status to failed
        # This would also require database access