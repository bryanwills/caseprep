"""
Media asset models for file uploads and storage.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseTenantAuditModel


class MediaStatus(enum.Enum):
    """Media processing status options."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    TRANSCRIBED = "transcribed"
    FAILED = "failed"
    DELETED = "deleted"


class MediaType(enum.Enum):
    """Media file type categories."""
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    IMAGE = "image"


class MediaAsset(BaseTenantAuditModel):
    """
    Media asset model for storing uploaded files (audio, video, documents).
    """

    __tablename__ = "media_assets"

    # File information
    original_filename = Column(String(500), nullable=False)
    file_type = Column(SQLEnum(MediaType), nullable=False, index=True)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    duration_ms = Column(Integer, nullable=True)  # For audio/video files

    # Storage information
    storage_path = Column(String(1000), nullable=False)
    storage_provider = Column(String(50), default="local", nullable=False)  # local, s3, etc.
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256

    # Processing status
    status = Column(SQLEnum(MediaStatus), default=MediaStatus.UPLOADED, nullable=False, index=True)
    processing_started_at = Column(String, nullable=True)  # ISO datetime
    processing_completed_at = Column(String, nullable=True)  # ISO datetime
    processing_error = Column(Text, nullable=True)

    # Associated matter
    matter_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Media metadata
    media_metadata = Column(JSONB, default=dict, nullable=False)  # Audio codec, bitrate, etc.

    # Audio/video specific fields
    sample_rate = Column(Integer, nullable=True)  # Hz
    bit_rate = Column(Integer, nullable=True)  # bps
    channels = Column(Integer, nullable=True)  # 1=mono, 2=stereo

    # Video specific fields
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    frame_rate = Column(Numeric(5, 2), nullable=True)

    # Transcription settings
    language = Column(String(10), default="en", nullable=False)
    auto_detect_language = Column(Boolean, default=True, nullable=False)
    speaker_diarization = Column(Boolean, default=True, nullable=False)

    # Privacy and retention
    is_confidential = Column(Boolean, default=False, nullable=False)
    delete_after_transcription = Column(Boolean, default=False, nullable=False)

    # Custom fields and tags
    tags = Column(JSONB, default=list, nullable=False)
    custom_fields = Column(JSONB, default=dict, nullable=False)

    # Relationships
    matter = relationship("Matter", back_populates="media_assets")
    transcripts = relationship("Transcript", back_populates="media_asset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MediaAsset(id={self.id}, filename='{self.original_filename}', status='{self.status.value}')>"

    @property
    def file_extension(self) -> str:
        """Get file extension from filename."""
        return self.original_filename.split('.')[-1].lower() if '.' in self.original_filename else ''

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000 if self.duration_ms else 0

    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes."""
        return self.duration_seconds / 60 if self.duration_ms else 0

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024)

    @property
    def file_size_gb(self) -> float:
        """Get file size in GB."""
        return self.file_size_mb / 1024

    @property
    def is_processed(self) -> bool:
        """Check if media has been processed."""
        return self.status in [MediaStatus.TRANSCRIBED, MediaStatus.FAILED]

    @property
    def is_audio(self) -> bool:
        """Check if media is audio file."""
        return self.file_type == MediaType.AUDIO

    @property
    def is_video(self) -> bool:
        """Check if media is video file."""
        return self.file_type == MediaType.VIDEO

    @property
    def can_transcribe(self) -> bool:
        """Check if media can be transcribed."""
        return self.file_type in [MediaType.AUDIO, MediaType.VIDEO]

    def add_tag(self, tag: str):
        """Add a tag to the media asset."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove a tag from the media asset."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def set_metadata(self, key: str, value):
        """Set a metadata value."""
        if self.media_metadata is None:
            self.media_metadata = {}
        self.media_metadata[key] = value

    def get_metadata(self, key: str, default=None):
        """Get a metadata value."""
        return self.media_metadata.get(key, default) if self.media_metadata else default

    def set_processing_status(self, status: MediaStatus, error: str = None):
        """Update processing status."""
        self.status = status
        if status == MediaStatus.PROCESSING:
            from datetime import datetime
            self.processing_started_at = datetime.utcnow().isoformat()
        elif status in [MediaStatus.TRANSCRIBED, MediaStatus.FAILED]:
            from datetime import datetime
            self.processing_completed_at = datetime.utcnow().isoformat()
            if error:
                self.processing_error = error

    def get_display_name(self) -> str:
        """Get display name for the media asset."""
        name = self.original_filename
        if len(name) > 50:
            name = name[:47] + "..."
        return name

    def get_storage_url(self, signed: bool = True) -> str:
        """Get storage URL (implementation depends on storage provider)."""
        # This would generate signed URLs for private files
        # Implementation depends on storage provider (S3, local, etc.)
        return f"/api/v1/media/{self.id}/download"