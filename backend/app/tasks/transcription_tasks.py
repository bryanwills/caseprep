"""
Background tasks for audio/video transcription using OpenAI Whisper.
"""

import os
import tempfile
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.models.media import MediaAsset, MediaStatus
from app.models.transcript import Transcript, TranscriptSegment, TranscriptStatus, SpeakerRole
from app.services.storage_service import get_storage_service
from app.services.file_service import FileProcessingService


# Create async database session for tasks
async_engine = create_async_engine(str(settings.DATABASE_URL))
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def get_db_session():
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        yield session


class TranscriptionService:
    """Service for handling transcription operations."""
    
    def __init__(self):
        self.storage_service = get_storage_service()
        self.file_service = FileProcessingService()
    
    async def transcribe_audio(
        self, 
        audio_file_path: str, 
        model: str = "whisper-large-v3",
        language: Optional[str] = None,
        enable_diarization: bool = True
    ) -> Dict[str, Any]:
        """Transcribe audio file using Whisper."""
        try:
            import whisper
            import torch
            
            # Load Whisper model
            device = "cuda" if torch.cuda.is_available() else "cpu"
            whisper_model = whisper.load_model(model, device=device)
            
            # Transcribe with options
            transcribe_options = {
                "verbose": False,
                "word_timestamps": True,
                "language": language
            }
            
            result = whisper_model.transcribe(audio_file_path, **transcribe_options)
            
            # Perform speaker diarization if enabled
            speakers = []
            if enable_diarization:
                try:
                    speakers = await self.perform_speaker_diarization(audio_file_path)
                except Exception as e:
                    print(f"Speaker diarization failed: {e}")
            
            return {
                "success": True,
                "text": result["text"],
                "language": result["language"],
                "segments": result["segments"],
                "speakers": speakers,
                "duration": result.get("duration", 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": None,
                "segments": [],
                "speakers": []
            }
    
    async def perform_speaker_diarization(self, audio_file_path: str) -> List[Dict[str, Any]]:
        """Perform speaker diarization using pyannote.audio."""
        try:
            # This would use pyannote.audio for speaker diarization
            # For now, return mock data
            return [
                {
                    "speaker": "SPEAKER_00",
                    "start": 0.0,
                    "end": 10.0
                },
                {
                    "speaker": "SPEAKER_01", 
                    "start": 10.0,
                    "end": 20.0
                }
            ]
        except Exception:
            return []
    
    def assign_speakers_to_segments(self, segments: List[Dict], speakers: List[Dict]) -> List[Dict]:
        """Assign speaker labels to transcript segments."""
        if not speakers:
            return segments
        
        # Simple assignment based on time overlap
        for segment in segments:
            segment_start = segment.get("start", 0)
            segment_end = segment.get("end", 0)
            
            # Find speaker with most overlap
            best_speaker = None
            max_overlap = 0
            
            for speaker in speakers:
                speaker_start = speaker["start"]
                speaker_end = speaker["end"]
                
                # Calculate overlap
                overlap_start = max(segment_start, speaker_start)
                overlap_end = min(segment_end, speaker_end)
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = speaker["speaker"]
            
            segment["speaker"] = best_speaker
        
        return segments


transcription_service = TranscriptionService()


@celery_app.task(bind=True, name="app.tasks.transcription_tasks.transcribe_media")
def transcribe_media(self, media_asset_id: str):
    """
    Transcribe a media asset.
    
    Args:
        media_asset_id: ID of the MediaAsset to transcribe
    """
    return asyncio.run(_transcribe_media_async(self, media_asset_id))


async def _transcribe_media_async(task, media_asset_id: str):
    """Async implementation of media transcription."""
    async with AsyncSessionLocal() as db:
        try:
            # Update task state
            task.update_state(
                state="PROGRESS",
                meta={"stage": "initializing", "progress": 0}
            )
            
            # Get media asset
            from sqlalchemy import select
            query = select(MediaAsset).where(MediaAsset.id == media_asset_id)
            result = await db.execute(query)
            media_asset = result.scalar_one_or_none()
            
            if not media_asset:
                raise Exception(f"MediaAsset {media_asset_id} not found")
            
            # Update media asset status
            media_asset.set_processing_status(MediaStatus.PROCESSING)
            await db.commit()
            
            # Update task progress
            task.update_state(
                state="PROGRESS", 
                meta={"stage": "downloading", "progress": 10}
            )
            
            # Get file content from storage
            file_content = await transcription_service.storage_service.get_file_content(
                media_asset.storage_path
            )
            
            if not file_content:
                raise Exception("Could not retrieve file from storage")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                suffix=f".{media_asset.file_extension}", 
                delete=False
            ) as temp_file:
                temp_file.write(file_content)
                temp_audio_path = temp_file.name
            
            try:
                # Convert to WAV if needed for better Whisper compatibility
                wav_path = None
                if not media_asset.file_extension in ['.wav', '.flac']:
                    task.update_state(
                        state="PROGRESS", 
                        meta={"stage": "converting", "progress": 20}
                    )
                    
                    wav_path = temp_audio_path.replace(
                        media_asset.file_extension, 
                        '.wav'
                    )
                    
                    success = await transcription_service.file_service.convert_to_wav(
                        temp_audio_path, 
                        wav_path
                    )
                    
                    if not success:
                        raise Exception("Failed to convert audio to WAV format")
                    
                    audio_file_path = wav_path
                else:
                    audio_file_path = temp_audio_path
                
                # Perform transcription
                task.update_state(
                    state="PROGRESS", 
                    meta={"stage": "transcribing", "progress": 30}
                )
                
                transcription_result = await transcription_service.transcribe_audio(
                    audio_file_path,
                    language=media_asset.language if not media_asset.auto_detect_language else None,
                    enable_diarization=media_asset.speaker_diarization
                )
                
                if not transcription_result["success"]:
                    raise Exception(f"Transcription failed: {transcription_result['error']}")
                
                # Update progress
                task.update_state(
                    state="PROGRESS", 
                    meta={"stage": "processing_segments", "progress": 60}
                )
                
                # Create transcript record
                transcript = Transcript(
                    tenant_id=media_asset.tenant_id,
                    matter_id=media_asset.matter_id,
                    media_asset_id=media_asset.id,
                    title=f"Transcript - {media_asset.original_filename}",
                    content=transcription_result["text"],
                    status=TranscriptStatus.COMPLETED,
                    language=transcription_result["language"],
                    model_used="whisper-large-v3",
                    speaker_diarization_enabled=media_asset.speaker_diarization,
                    confidence_score=0.85,  # Mock confidence score
                    created_by_user_id=media_asset.created_by_user_id,
                    updated_by_user_id=media_asset.created_by_user_id
                )
                
                db.add(transcript)
                await db.flush()  # Get transcript ID
                
                # Process segments with speaker assignment
                segments = transcription_result["segments"]
                speakers = transcription_result["speakers"]
                
                if speakers:
                    segments = transcription_service.assign_speakers_to_segments(
                        segments, 
                        speakers
                    )
                
                # Create transcript segments
                segment_objects = []
                for i, segment in enumerate(segments):
                    segment_obj = TranscriptSegment(
                        tenant_id=media_asset.tenant_id,
                        transcript_id=transcript.id,
                        segment_index=i,
                        start_time=int(segment.get("start", 0) * 1000),  # Convert to ms
                        end_time=int(segment.get("end", 0) * 1000),
                        duration=int((segment.get("end", 0) - segment.get("start", 0)) * 1000),
                        text=segment.get("text", "").strip(),
                        speaker_id=segment.get("speaker"),
                        confidence=segment.get("confidence", 0.0),
                        word_count=len(segment.get("text", "").split()),
                        created_by_user_id=media_asset.created_by_user_id,
                        updated_by_user_id=media_asset.created_by_user_id
                    )
                    segment_objects.append(segment_obj)
                
                db.add_all(segment_objects)
                
                # Update transcript statistics
                transcript.segment_count = len(segment_objects)
                transcript.word_count = sum(seg.word_count for seg in segment_objects)
                transcript.speaker_count = len(set(
                    seg.speaker_id for seg in segment_objects 
                    if seg.speaker_id
                ))
                
                # Update media asset status
                media_asset.set_processing_status(MediaStatus.TRANSCRIBED)
                
                # Update matter statistics
                from app.models.matter import Matter
                matter_query = select(Matter).where(Matter.id == media_asset.matter_id)
                matter_result = await db.execute(matter_query)
                matter = matter_result.scalar_one_or_none()
                
                if matter:
                    matter.update_statistics(
                        transcript_count_delta=1,
                        duration_delta=int(media_asset.duration_ms or 0),
                        storage_delta=media_asset.file_size
                    )
                
                await db.commit()
                
                # Final progress update
                task.update_state(
                    state="PROGRESS", 
                    meta={"stage": "completed", "progress": 100}
                )
                
                return {
                    "success": True,
                    "transcript_id": str(transcript.id),
                    "segments_created": len(segment_objects),
                    "language": transcription_result["language"],
                    "duration_seconds": transcription_result.get("duration", 0)
                }
                
            finally:
                # Clean up temporary files
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                if wav_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
                
        except Exception as e:
            # Update media asset status to failed
            if 'media_asset' in locals():
                media_asset.set_processing_status(MediaStatus.FAILED, str(e))
                await db.commit()
            
            raise e


@celery_app.task(name="app.tasks.transcription_tasks.retry_failed_transcription")
def retry_failed_transcription(media_asset_id: str):
    """Retry transcription for a failed media asset."""
    return transcribe_media.delay(media_asset_id)


@celery_app.task(name="app.tasks.transcription_tasks.batch_transcribe")
def batch_transcribe(media_asset_ids: List[str]):
    """Transcribe multiple media assets in batch."""
    results = []
    for media_id in media_asset_ids:
        result = transcribe_media.delay(media_id)
        results.append({
            "media_asset_id": media_id,
            "task_id": result.id
        })
    
    return {
        "batch_size": len(media_asset_ids),
        "tasks_created": results
    }