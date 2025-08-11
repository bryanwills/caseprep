"""
Transcript and transcript segment models for transcription results.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseTenantAuditModel


class TranscriptStatus(enum.Enum):
    """Transcript processing status options."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWING = "reviewing"
    APPROVED = "approved"


class TranscriptFormat(enum.Enum):
    """Transcript output format options."""
    PLAIN_TEXT = "plain_text"
    TIMESTAMPED = "timestamped"
    SPEAKER_SEPARATED = "speaker_separated"
    LEGAL_FORMAT = "legal_format"


class SpeakerRole(enum.Enum):
    """Speaker role classifications."""
    UNKNOWN = "unknown"
    ATTORNEY = "attorney"
    CLIENT = "client"
    WITNESS = "witness"
    JUDGE = "judge"
    COURT_REPORTER = "court_reporter"
    INTERPRETER = "interpreter"
    OTHER = "other"


class Transcript(BaseTenantAuditModel):
    """
    Transcript model for storing transcription results and metadata.
    """
    
    __tablename__ = "transcripts"
    
    # Associated records
    matter_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    media_asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Transcript content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)  # Full transcript text
    
    # Processing information
    status = Column(SQLEnum(TranscriptStatus), default=TranscriptStatus.PENDING, nullable=False, index=True)
    format = Column(SQLEnum(TranscriptFormat), default=TranscriptFormat.TIMESTAMPED, nullable=False)
    language = Column(String(10), nullable=False)
    
    # Transcription settings used
    model_used = Column(String(100), nullable=True)  # e.g., "whisper-large-v3"
    speaker_diarization_enabled = Column(Boolean, default=False, nullable=False)
    auto_punctuation = Column(Boolean, default=True, nullable=False)
    profanity_filter = Column(Boolean, default=False, nullable=False)
    
    # Quality metrics
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    word_count = Column(Integer, default=0, nullable=False)
    segment_count = Column(Integer, default=0, nullable=False)
    speaker_count = Column(Integer, default=0, nullable=False)
    
    # Processing timing
    processing_duration_ms = Column(Integer, nullable=True)
    processing_started_at = Column(String, nullable=True)  # ISO datetime
    processing_completed_at = Column(String, nullable=True)  # ISO datetime
    processing_error = Column(Text, nullable=True)
    
    # Review and approval
    reviewed_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(String, nullable=True)  # ISO datetime
    review_notes = Column(Text, nullable=True)
    
    # Legal compliance
    is_privileged = Column(Boolean, default=False, nullable=False)
    is_confidential = Column(Boolean, default=True, nullable=False)
    retention_override_days = Column(Integer, nullable=True)  # Override matter retention
    
    # Export tracking
    exported_formats = Column(JSONB, default=list, nullable=False)  # ["pdf", "docx", "txt"]
    last_exported_at = Column(String, nullable=True)  # ISO datetime
    
    # Custom fields and metadata
    custom_fields = Column(JSONB, default=dict, nullable=False)
    tags = Column(JSONB, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Analytics
    view_count = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    matter = relationship("Matter", back_populates="transcripts")
    media_asset = relationship("MediaAsset", back_populates="transcripts")
    segments = relationship("TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Transcript(id={self.id}, title='{self.title}', status='{self.status.value}')>"
    
    @property
    def duration_seconds(self) -> float:
        """Get transcript duration from media asset."""
        return self.media_asset.duration_seconds if self.media_asset else 0
    
    @property
    def duration_minutes(self) -> float:
        """Get transcript duration in minutes."""
        return self.duration_seconds / 60
    
    @property
    def processing_duration_seconds(self) -> float:
        """Get processing duration in seconds."""
        return self.processing_duration_ms / 1000 if self.processing_duration_ms else 0
    
    @property
    def is_completed(self) -> bool:
        """Check if transcription is completed."""
        return self.status in [TranscriptStatus.COMPLETED, TranscriptStatus.REVIEWING, TranscriptStatus.APPROVED]
    
    @property
    def is_reviewable(self) -> bool:
        """Check if transcript can be reviewed."""
        return self.status in [TranscriptStatus.COMPLETED, TranscriptStatus.REVIEWING]
    
    @property
    def words_per_minute(self) -> float:
        """Calculate words per minute."""
        if self.word_count > 0 and self.duration_minutes > 0:
            return self.word_count / self.duration_minutes
        return 0
    
    @property
    def has_speakers(self) -> bool:
        """Check if transcript has speaker diarization."""
        return self.speaker_diarization_enabled and self.speaker_count > 0
    
    def add_tag(self, tag: str):
        """Add a tag to the transcript."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the transcript."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def set_custom_field(self, key: str, value):
        """Set a custom field value."""
        if self.custom_fields is None:
            self.custom_fields = {}
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default=None):
        """Get a custom field value."""
        return self.custom_fields.get(key, default) if self.custom_fields else default
    
    def mark_exported(self, format: str):
        """Mark transcript as exported in a specific format."""
        if self.exported_formats is None:
            self.exported_formats = []
        if format not in self.exported_formats:
            self.exported_formats.append(format)
        
        from datetime import datetime
        self.last_exported_at = datetime.utcnow().isoformat()
    
    def increment_view_count(self):
        """Increment view count."""
        self.view_count += 1
    
    def increment_download_count(self):
        """Increment download count."""
        self.download_count += 1
    
    def set_processing_status(self, status: TranscriptStatus, error: str = None):
        """Update processing status."""
        self.status = status
        if status == TranscriptStatus.PROCESSING:
            from datetime import datetime
            self.processing_started_at = datetime.utcnow().isoformat()
        elif status in [TranscriptStatus.COMPLETED, TranscriptStatus.FAILED]:
            from datetime import datetime
            self.processing_completed_at = datetime.utcnow().isoformat()
            if error:
                self.processing_error = error
    
    def approve(self, user_id: str, notes: str = None):
        """Approve the transcript."""
        from datetime import datetime
        self.status = TranscriptStatus.APPROVED
        self.reviewed_by_user_id = user_id
        self.reviewed_at = datetime.utcnow().isoformat()
        if notes:
            self.review_notes = notes


class TranscriptSegment(BaseTenantAuditModel):
    """
    Individual transcript segments with timing and speaker information.
    """
    
    __tablename__ = "transcript_segments"
    
    transcript_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Segment identification
    segment_index = Column(Integer, nullable=False, index=True)  # Order in transcript
    
    # Timing information (milliseconds)
    start_time = Column(Integer, nullable=False)
    end_time = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    
    # Content
    text = Column(Text, nullable=False)
    
    # Speaker information
    speaker_id = Column(String(50), nullable=True)  # e.g., "SPEAKER_00", "SPEAKER_01"
    speaker_name = Column(String(255), nullable=True)  # Assigned speaker name
    speaker_role = Column(SQLEnum(SpeakerRole), default=SpeakerRole.UNKNOWN, nullable=False)
    
    # Quality metrics
    confidence = Column(Numeric(4, 3), nullable=True)  # 0.000 to 1.000
    
    # Segment metadata
    word_count = Column(Integer, default=0, nullable=False)
    is_question = Column(Boolean, default=False, nullable=False)
    is_interruption = Column(Boolean, default=False, nullable=False)
    has_crosstalk = Column(Boolean, default=False, nullable=False)
    
    # Editing and review
    is_edited = Column(Boolean, default=False, nullable=False)
    original_text = Column(Text, nullable=True)  # Original before editing
    edited_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    edited_at = Column(String, nullable=True)  # ISO datetime
    
    # Custom fields
    custom_fields = Column(JSONB, default=dict, nullable=False)
    
    # Relationships
    transcript = relationship("Transcript", back_populates="segments")
    
    def __repr__(self):
        return f"<TranscriptSegment(id={self.id}, transcript_id={self.transcript_id}, speaker='{self.speaker_id}')>"
    
    @property
    def start_time_seconds(self) -> float:
        """Get start time in seconds."""
        return self.start_time / 1000
    
    @property
    def end_time_seconds(self) -> float:
        """Get end time in seconds."""
        return self.end_time / 1000
    
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration / 1000
    
    @property
    def start_time_formatted(self) -> str:
        """Get formatted start time (MM:SS)."""
        total_seconds = self.start_time_seconds
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def end_time_formatted(self) -> str:
        """Get formatted end time (MM:SS)."""
        total_seconds = self.end_time_seconds
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def time_range_formatted(self) -> str:
        """Get formatted time range."""
        return f"{self.start_time_formatted} - {self.end_time_formatted}"
    
    @property
    def has_speaker(self) -> bool:
        """Check if segment has speaker information."""
        return self.speaker_id is not None or self.speaker_name is not None
    
    @property
    def display_speaker(self) -> str:
        """Get display name for speaker."""
        if self.speaker_name:
            return self.speaker_name
        elif self.speaker_id:
            return self.speaker_id.replace("SPEAKER_", "Speaker ")
        else:
            return "Unknown Speaker"
    
    def edit_text(self, new_text: str, user_id: str):
        """Edit the segment text."""
        if not self.is_edited:
            self.original_text = self.text
        
        self.text = new_text
        self.is_edited = True
        self.edited_by_user_id = user_id
        
        from datetime import datetime
        self.edited_at = datetime.utcnow().isoformat()
        
        # Recalculate word count
        self.word_count = len(new_text.split())
    
    def assign_speaker(self, speaker_name: str, speaker_role: SpeakerRole = None):
        """Assign a speaker name to this segment."""
        self.speaker_name = speaker_name
        if speaker_role:
            self.speaker_role = speaker_role
    
    def set_custom_field(self, key: str, value):
        """Set a custom field value."""
        if self.custom_fields is None:
            self.custom_fields = {}
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default=None):
        """Get a custom field value."""
        return self.custom_fields.get(key, default) if self.custom_fields else default