"""
Matter (case) models for legal case management.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseTenantAuditModel


class MatterStatus(enum.Enum):
    """Matter status options."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    CLOSED = "closed"
    ON_HOLD = "on_hold"


class MatterPriority(enum.Enum):
    """Matter priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Matter(BaseTenantAuditModel):
    """
    Matter (legal case) model for organizing transcripts and evidence.
    """
    
    __tablename__ = "matters"
    
    # Basic information
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    case_number = Column(String(100), nullable=True, index=True)
    
    # Client information
    client_name = Column(String(255), nullable=True)
    client_contact = Column(String(500), nullable=True)  # JSON string with contact info
    opposing_party = Column(String(255), nullable=True)
    opposing_counsel = Column(String(255), nullable=True)
    
    # Case details
    status = Column(SQLEnum(MatterStatus), default=MatterStatus.ACTIVE, nullable=False, index=True)
    priority = Column(SQLEnum(MatterPriority), default=MatterPriority.MEDIUM, nullable=False)
    practice_area = Column(String(100), nullable=True)  # e.g., "Personal Injury", "Corporate"
    court_name = Column(String(255), nullable=True)
    judge_name = Column(String(255), nullable=True)
    
    # Important dates
    statute_of_limitations = Column(String, nullable=True)  # ISO date string
    trial_date = Column(String, nullable=True)  # ISO date string
    discovery_deadline = Column(String, nullable=True)  # ISO date string
    
    # Data retention and privacy settings
    retention_days = Column(Integer, default=0, nullable=False)  # 0 = use tenant default
    store_media = Column(Boolean, default=False, nullable=False)
    store_transcripts = Column(Boolean, default=False, nullable=False)
    allow_anon_learning = Column(Boolean, default=False, nullable=False)
    
    # Financial information
    billing_rate = Column(Numeric(10, 2), nullable=True)
    estimated_value = Column(Numeric(15, 2), nullable=True)
    budget_limit = Column(Numeric(15, 2), nullable=True)
    
    # Custom fields and metadata
    custom_fields = Column(JSONB, default=dict, nullable=False)
    tags = Column(JSONB, default=list, nullable=False)  # List of strings
    
    # Analytics and statistics
    total_transcripts = Column(Integer, default=0, nullable=False)
    total_duration_ms = Column(Integer, default=0, nullable=False)
    total_storage_bytes = Column(Integer, default=0, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="matters")
    media_assets = relationship("MediaAsset", back_populates="matter", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="matter", cascade="all, delete-orphan")
    matter_participants = relationship("MatterParticipant", back_populates="matter", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Matter(id={self.id}, title='{self.title}', status='{self.status.value}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if matter is in active status."""
        return self.status == MatterStatus.ACTIVE
    
    @property
    def effective_retention_days(self) -> int:
        """Get effective retention days (matter setting or tenant default)."""
        if self.retention_days > 0:
            return self.retention_days
        # Would need to access tenant.data_retention_days
        return 0
    
    @property
    def total_duration_hours(self) -> float:
        """Get total duration in hours."""
        return self.total_duration_ms / (1000 * 60 * 60) if self.total_duration_ms else 0
    
    @property
    def total_storage_mb(self) -> float:
        """Get total storage in MB."""
        return self.total_storage_bytes / (1024 * 1024) if self.total_storage_bytes else 0
    
    def add_tag(self, tag: str):
        """Add a tag to the matter."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the matter."""
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
    
    def update_statistics(self, transcript_count_delta: int = 0, duration_delta: int = 0, storage_delta: int = 0):
        """Update matter statistics."""
        self.total_transcripts += transcript_count_delta
        self.total_duration_ms += duration_delta
        self.total_storage_bytes += storage_delta
        
        # Ensure values don't go negative
        self.total_transcripts = max(0, self.total_transcripts)
        self.total_duration_ms = max(0, self.total_duration_ms)
        self.total_storage_bytes = max(0, self.total_storage_bytes)


class MatterParticipant(BaseTenantAuditModel):
    """
    Participants in a legal matter (attorneys, clients, witnesses, etc.).
    """
    
    __tablename__ = "matter_participants"
    
    matter_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Participant information
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)  # e.g., "Attorney", "Client", "Witness", "Expert"
    title = Column(String(100), nullable=True)
    organization = Column(String(255), nullable=True)
    
    # Contact information
    email = Column(String(320), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    
    # Participant details
    is_primary = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Custom fields
    custom_fields = Column(JSONB, default=dict, nullable=False)
    
    # Relationships
    matter = relationship("Matter", back_populates="matter_participants")
    
    def __repr__(self):
        return f"<MatterParticipant(id={self.id}, name='{self.name}', role='{self.role}')>"


class MatterNote(BaseTenantAuditModel):
    """
    Notes and updates related to a matter.
    """
    
    __tablename__ = "matter_notes"
    
    matter_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Note content
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general", nullable=False)  # e.g., "general", "court", "client"
    
    # Note metadata
    is_confidential = Column(Boolean, default=False, nullable=False)
    is_privileged = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    matter = relationship("Matter")
    
    def __repr__(self):
        return f"<MatterNote(id={self.id}, matter_id={self.matter_id}, type='{self.note_type}')>"


class MatterDocument(BaseTenantAuditModel):
    """
    Documents and files associated with a matter (non-transcription files).
    """
    
    __tablename__ = "matter_documents"
    
    matter_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Document information
    title = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # e.g., "pdf", "docx", "image"
    file_size = Column(Integer, nullable=False)
    
    # Document classification
    document_type = Column(String(100), nullable=False)  # e.g., "pleading", "discovery", "contract"
    is_confidential = Column(Boolean, default=False, nullable=False)
    is_privileged = Column(Boolean, default=False, nullable=False)
    
    # Storage information
    storage_path = Column(String(1000), nullable=False)
    content_hash = Column(String(64), nullable=False)  # SHA-256
    
    # Document metadata
    description = Column(Text, nullable=True)
    tags = Column(JSONB, default=list, nullable=False)
    custom_fields = Column(JSONB, default=dict, nullable=False)
    
    # Version control
    version = Column(Integer, default=1, nullable=False)
    parent_document_id = Column(UUID(as_uuid=True), nullable=True)  # For versioning
    
    # Relationships
    matter = relationship("Matter")
    
    def __repr__(self):
        return f"<MatterDocument(id={self.id}, filename='{self.filename}', type='{self.document_type}')>"