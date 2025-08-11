"""
Base model classes with common functionality.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

from app.core.database import Base


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin to add UUID primary key."""
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality."""
    
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def soft_delete(self):
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Mixin to add audit trail fields."""
    
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    # JSON field for additional audit metadata
    audit_metadata = Column(Text, nullable=True)


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Base model class with UUID primary key and timestamps.
    """
    
    __abstract__ = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def __repr__(self) -> str:
        """String representation of model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class TenantMixin:
    """Mixin to add tenant isolation."""
    
    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )


class BaseAuditModel(BaseModel, AuditMixin, SoftDeleteMixin):
    """
    Base model with full audit trail and soft delete functionality.
    """
    
    __abstract__ = True


class BaseTenantModel(BaseModel, TenantMixin):
    """
    Base model with tenant isolation.
    """
    
    __abstract__ = True


class BaseTenantAuditModel(BaseModel, TenantMixin, AuditMixin, SoftDeleteMixin):
    """
    Base model with tenant isolation, audit trail, and soft delete.
    """
    
    __abstract__ = True


class HashMixin:
    """Mixin for models that need hash verification."""
    
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256
    hash_algorithm = Column(String(20), default="sha256", nullable=False)
    
    def verify_hash(self, content: bytes) -> bool:
        """Verify content against stored hash."""
        import hashlib
        
        if self.hash_algorithm == "sha256":
            computed_hash = hashlib.sha256(content).hexdigest()
            return computed_hash == self.content_hash
        
        return False
    
    def compute_and_set_hash(self, content: bytes) -> str:
        """Compute and set hash for content."""
        import hashlib
        
        if self.hash_algorithm == "sha256":
            self.content_hash = hashlib.sha256(content).hexdigest()
            return self.content_hash
        
        raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}")