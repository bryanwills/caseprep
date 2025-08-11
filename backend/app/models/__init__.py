"""
Models package for CasePrep backend.
"""

from .base import BaseModel, BaseTenantModel, BaseTenantAuditModel
from .user import User, Tenant, UserRole, SubscriptionPlan
from .matter import Matter, MatterParticipant, MatterNote, MatterDocument, MatterStatus, MatterPriority
from .media import MediaAsset, MediaStatus, MediaType
from .transcript import Transcript, TranscriptSegment, TranscriptStatus, TranscriptFormat, SpeakerRole

__all__ = [
    # Base models
    "BaseModel",
    "BaseTenantModel", 
    "BaseTenantAuditModel",
    
    # User and tenant models
    "User",
    "Tenant",
    "UserRole",
    "SubscriptionPlan",
    
    # Matter models
    "Matter",
    "MatterParticipant",
    "MatterNote",
    "MatterDocument",
    "MatterStatus",
    "MatterPriority",
    
    # Media models
    "MediaAsset",
    "MediaStatus",
    "MediaType",
    
    # Transcript models
    "Transcript",
    "TranscriptSegment",
    "TranscriptStatus",
    "TranscriptFormat",
    "SpeakerRole",
]