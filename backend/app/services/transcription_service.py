"""
Transcription service for CasePrep backend.
Handles audio/video transcription using AI models.
"""

import asyncio
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

from faster_whisper import WhisperModel
import whisperx
import torch
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook

from app.models.transcript import Transcript, TranscriptSegment
from app.models.media import MediaAsset
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """Result of transcription process."""
    segments: List[TranscriptSegment]
    language: str
    duration_seconds: float
    word_timings: Optional[List[Dict]] = None
    speaker_labels: Optional[List[str]] = None

@dataclass
class TranscriptionConfig:
    """Configuration for transcription process."""
    language: str = "en"
    model_size: str = "large-v3"
    compute_type: str = "float16"  # or "int8" for CPU
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    enable_diarization: bool = True
    enable_word_timing: bool = True
    custom_dictionary: Optional[Dict[str, str]] = None

class TranscriptionService:
    """Service for handling transcription of audio/video files."""

    def __init__(self):
        self.whisper_model: Optional[WhisperModel] = None
        self.diarization_pipeline: Optional[Pipeline] = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize AI models for transcription."""
        try:
            # Initialize Whisper model
            logger.info(f"Initializing Whisper model: {settings.WHISPER_MODEL_SIZE}")
            self.whisper_model = WhisperModel(
                model_size_or_path=settings.WHISPER_MODEL_SIZE,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
                download_root=settings.WHISPER_MODEL_CACHE_DIR
            )
            logger.info("Whisper model initialized successfully")

            # Initialize diarization pipeline if enabled
            if settings.ENABLE_DIARIZATION and settings.PYANNOTE_AUTH_TOKEN:
                logger.info("Initializing Pyannote diarization pipeline")
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=settings.PYANNOTE_AUTH_TOKEN
                )
                logger.info("Diarization pipeline initialized successfully")
            else:
                logger.info("Diarization disabled or no auth token provided")

        except Exception as e:
            logger.error(f"Failed to initialize transcription models: {e}")
            raise

    async def transcribe_media(
        self,
        media_path: str,
        config: TranscriptionConfig
    ) -> TranscriptionResult:
        """
        Transcribe media file using the full pipeline.

        Args:
            media_path: Path to the media file
            config: Transcription configuration

        Returns:
            TranscriptionResult with segments and metadata
        """
        try:
            logger.info(f"Starting transcription of {media_path}")

            # Step 1: Basic transcription with faster-whisper
            logger.info("Step 1: Running basic transcription")
            basic_result = await self._run_basic_transcription(media_path, config)

            # Step 2: Word-level alignment with WhisperX
            if config.enable_word_timing:
                logger.info("Step 2: Running word-level alignment")
                aligned_result = await self._run_word_alignment(
                    media_path,
                    basic_result,
                    config
                )
            else:
                aligned_result = basic_result

            # Step 3: Speaker diarization
            if config.enable_diarization and self.diarization_pipeline:
                logger.info("Step 3: Running speaker diarization")
                diarized_result = await self._run_speaker_diarization(
                    media_path,
                    aligned_result,
                    config
                )
            else:
                diarized_result = aligned_result

            # Step 4: Apply custom dictionary corrections
            if config.custom_dictionary:
                logger.info("Step 4: Applying custom dictionary")
                final_result = await self._apply_custom_dictionary(
                    diarized_result,
                    config.custom_dictionary
                )
            else:
                final_result = diarized_result

            logger.info("Transcription completed successfully")
            return final_result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    async def _run_basic_transcription(
        self,
        media_path: str,
        config: TranscriptionConfig
    ) -> TranscriptionResult:
        """Run basic transcription using faster-whisper."""
        try:
            # Run transcription
            segments, info = self.whisper_model.transcribe(
                media_path,
                language=config.language if config.language != "auto" else None,
                task="transcribe",
                beam_size=5,
                best_of=5,
                temperature=0.0,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                condition_on_previous_text=True,
                initial_prompt=None
            )

            # Convert to our format
            transcript_segments = []
            for segment in segments:
                transcript_segment = TranscriptSegment(
                    id=f"seg_{len(transcript_segments)}",
                    transcript_id="",  # Will be set by caller
                    speaker="Unknown",  # Will be set by diarization
                    start_ms=int(segment.start * 1000),
                    end_ms=int(segment.end * 1000),
                    text=segment.text.strip(),
                    confidence=segment.avg_logprob,
                    words=None,  # Will be set by word alignment
                    created_at=""
                )
                transcript_segments.append(transcript_segment)

            return TranscriptionResult(
                segments=transcript_segments,
                language=info.language,
                duration_seconds=info.duration
            )

        except Exception as e:
            logger.error(f"Basic transcription failed: {e}")
            raise

    async def _run_word_alignment(
        self,
        media_path: str,
        basic_result: TranscriptionResult,
        config: TranscriptionConfig
    ) -> TranscriptionResult:
        """Run word-level alignment using WhisperX."""
        try:
            # Prepare segments for WhisperX
            whisperx_segments = []
            for segment in basic_result.segments:
                whisperx_segments.append({
                    "start": segment.start_ms / 1000.0,
                    "end": segment.end_ms / 1000.0,
                    "text": segment.text
                })

            # Run WhisperX alignment
            model = whisperx.load_model(
                "large-v3",
                device=config.device,
                compute_type=config.compute_type
            )

            # Load audio
            audio = whisperx.load_audio(media_path)

            # Align segments
            result = model.align(
                whisperx_segments,
                model,
                audio,
                config.device,
                return_char_alignments=False
            )

            # Update segments with word timings
            updated_segments = []
            for i, segment in enumerate(basic_result.segments):
                if i < len(result["segments"]):
                    wx_segment = result["segments"][i]
                    words = []

                    if "words" in wx_segment:
                        for word_info in wx_segment["words"]:
                            words.append({
                                "word": word_info["word"],
                                "startMs": int(word_info["start"] * 1000),
                                "endMs": int(word_info["end"] * 1000),
                                "confidence": word_info.get("score", 0.0)
                            })

                    updated_segment = TranscriptSegment(
                        id=segment.id,
                        transcript_id=segment.transcript_id,
                        speaker=segment.speaker,
                        start_ms=segment.start_ms,
                        end_ms=segment.end_ms,
                        text=segment.text,
                        confidence=segment.confidence,
                        words=words,
                        created_at=segment.created_at
                    )
                    updated_segments.append(updated_segment)
                else:
                    updated_segments.append(segment)

            return TranscriptionResult(
                segments=updated_segments,
                language=basic_result.language,
                duration_seconds=basic_result.duration_seconds,
                word_timings=[seg.words for seg in updated_segments if seg.words]
            )

        except Exception as e:
            logger.error(f"Word alignment failed: {e}")
            # Return basic result if alignment fails
            return basic_result

    async def _run_speaker_diarization(
        self,
        media_path: str,
        aligned_result: TranscriptionResult,
        config: TranscriptionConfig
    ) -> TranscriptionResult:
        """Run speaker diarization using Pyannote."""
        try:
            if not self.diarization_pipeline:
                logger.warning("Diarization pipeline not available")
                return aligned_result

            # Run diarization
            with ProgressHook() as hook:
                diarization = self.diarization_pipeline(
                    media_path,
                    hook=hook
                )

            # Extract speaker turns
            speaker_turns = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_turns.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })

            # Assign speakers to segments
            updated_segments = []
            for segment in aligned_result.segments:
                # Find which speaker turn this segment belongs to
                segment_start = segment.start_ms / 1000.0
                segment_end = segment.end_ms / 1000.0

                assigned_speaker = "Unknown"
                max_overlap = 0

                for turn in speaker_turns:
                    # Calculate overlap
                    overlap_start = max(segment_start, turn["start"])
                    overlap_end = min(segment_end, turn["end"])
                    overlap = max(0, overlap_end - overlap_start)

                    if overlap > max_overlap:
                        max_overlap = overlap
                        assigned_speaker = turn["speaker"]

                # Update segment with speaker
                updated_segment = TranscriptSegment(
                    id=segment.id,
                    transcript_id=segment.transcript_id,
                    speaker=assigned_speaker,
                    start_ms=segment.start_ms,
                    end_ms=segment.end_ms,
                    text=segment.text,
                    confidence=segment.confidence,
                    words=segment.words,
                    created_at=segment.created_at
                )
                updated_segments.append(updated_segment)

            return TranscriptionResult(
                segments=updated_segments,
                language=aligned_result.language,
                duration_seconds=aligned_result.duration_seconds,
                word_timings=aligned_result.word_timings,
                speaker_labels=list(set(seg.speaker for seg in updated_segments))
            )

        except Exception as e:
            logger.error(f"Speaker diarization failed: {e}")
            # Return aligned result if diarization fails
            return aligned_result

    async def _apply_custom_dictionary(
        self,
        result: TranscriptionResult,
        dictionary: Dict[str, str]
    ) -> TranscriptionResult:
        """Apply custom dictionary corrections to transcript."""
        try:
            updated_segments = []

            for segment in result.segments:
                corrected_text = segment.text

                # Apply corrections in order (longest first for phrases)
                sorted_corrections = sorted(
                    dictionary.items(),
                    key=lambda x: len(x[0]),
                    reverse=True
                )

                for pattern, replacement in sorted_corrections:
                    corrected_text = corrected_text.replace(pattern, replacement)

                # Update segment if text changed
                if corrected_text != segment.text:
                    updated_segment = TranscriptSegment(
                        id=segment.id,
                        transcript_id=segment.transcript_id,
                        speaker=segment.speaker,
                        start_ms=segment.start_ms,
                        end_ms=segment.end_ms,
                        text=corrected_text,
                        confidence=segment.confidence,
                        words=segment.words,
                        created_at=segment.created_at
                    )
                    updated_segments.append(updated_segment)
                else:
                    updated_segments.append(segment)

            return TranscriptionResult(
                segments=updated_segments,
                language=result.language,
                duration_seconds=result.duration_seconds,
                word_timings=result.word_timings,
                speaker_labels=result.speaker_labels
            )

        except Exception as e:
            logger.error(f"Custom dictionary application failed: {e}")
            return result

    async def create_clip(
        self,
        transcript: Transcript,
        start_ms: int,
        end_ms: int,
        include_video: bool = True,
        include_audio: bool = True
    ) -> str:
        """
        Create a clip from the transcript with specified time range.

        Args:
            transcript: The transcript to clip from
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds
            include_video: Whether to include video in clip
            include_audio: Whether to include audio in clip

        Returns:
            Path to the generated clip file
        """
        try:
            # This would use FFmpeg to create the actual clip
            # For now, return a placeholder
            logger.info(f"Creating clip from {start_ms}ms to {end_ms}ms")

            # In production, this would:
            # 1. Use FFmpeg to extract the time range
            # 2. Apply any necessary codec conversions
            # 3. Return the path to the generated clip

            return f"/tmp/clip_{transcript.id}_{start_ms}_{end_ms}.mp4"

        except Exception as e:
            logger.error(f"Clip creation failed: {e}")
            raise

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available transcription models."""
        return {
            "whisper": ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
            "diarization": ["pyannote-2.1", "pyannote-3.1"],
            "languages": ["en", "es", "fr", "de", "it", "pt", "auto"]
        }

    def get_model_info(self) -> Dict[str, any]:
        """Get information about the current models."""
        return {
            "whisper_model": settings.WHISPER_MODEL_SIZE,
            "whisper_device": settings.WHISPER_DEVICE,
            "whisper_compute_type": settings.WHISPER_COMPUTE_TYPE,
            "diarization_enabled": self.diarization_pipeline is not None,
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
        }
