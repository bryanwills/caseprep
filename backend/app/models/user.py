"""
User and tenant models for authentication and authorization.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, BaseTenantModel


class UserRole(enum.Enum):
    """User roles within a tenant."""
    OWNER = "owner"
    ADMIN = "admin" 
    EDITOR = "editor"
    VIEWER = "viewer"


class SubscriptionPlan(enum.Enum):
    """Subscription plan types."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Tenant(BaseModel):
    """
    Tenant model for multi-tenancy support.
    """
    
    __tablename__ = "tenants"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Subscription information
    plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.STARTER, nullable=False)
    subscription_status = Column(String(50), default="active", nullable=False)
    trial_ends_at = Column(String, nullable=True)  # ISO datetime string
    
    # Settings stored as JSON
    settings = Column(JSONB, default=dict, nullable=False)
    
    # Resource limits
    max_users = Column(Integer, default=5, nullable=False)
    max_storage_gb = Column(Integer, default=10, nullable=False)
    max_transcription_hours = Column(Integer, default=10, nullable=False)
    
    # Feature flags
    features = Column(JSONB, default=dict, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    matters = relationship("Matter", back_populates="tenant", cascade="all, delete-orphan")
    
    # Branding and customization
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color
    secondary_color = Column(String(7), nullable=True)  # Hex color
    custom_domain = Column(String(255), nullable=True, unique=True)
    
    # Compliance settings
    data_retention_days = Column(Integer, default=0, nullable=False)  # 0 = no retention
    require_mfa = Column(Boolean, default=False, nullable=False)
    allowed_ip_ranges = Column(JSONB, default=list, nullable=False)
    sso_enabled = Column(Boolean, default=False, nullable=False)
    sso_config = Column(JSONB, default=dict, nullable=False)
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', plan='{self.plan.value}')>"
    
    @property
    def is_trial(self) -> bool:
        """Check if tenant is on trial."""
        return self.subscription_status == "trial"
    
    @property
    def is_active(self) -> bool:
        """Check if tenant subscription is active."""
        return self.subscription_status in ["active", "trial"]
    
    def get_setting(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Set a setting value."""
        if self.settings is None:
            self.settings = {}
        self.settings[key] = value
    
    def get_feature(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return self.features.get(feature, False)
    
    def enable_feature(self, feature: str):
        """Enable a feature."""
        if self.features is None:
            self.features = {}
        self.features[feature] = True
    
    def disable_feature(self, feature: str):
        """Disable a feature."""
        if self.features is None:
            self.features = {}
        self.features[feature] = False


class User(BaseTenantModel):
    """
    User model with tenant association.
    """
    
    __tablename__ = "users"
    
    email = Column(String(320), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Role within tenant
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    
    # Authentication
    verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(String, nullable=True)  # ISO datetime string
    
    # MFA settings
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(100), nullable=True)
    backup_codes = Column(JSONB, default=list, nullable=False)
    
    # OAuth information
    oauth_providers = Column(JSONB, default=dict, nullable=False)  # Store OAuth provider data
    
    # User preferences
    preferences = Column(JSONB, default=dict, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    
    # Login tracking
    last_login_at = Column(String, nullable=True)  # ISO datetime string
    last_login_ip = Column(String(45), nullable=True)  # IPv6 compatible
    login_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.email.split("@")[0]
    
    @property
    def initials(self) -> str:
        """Get user initials."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.display_name:
            parts = self.display_name.split()
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[1][0]}".upper()
            return self.display_name[0].upper()
        return self.email[0].upper()
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        role_permissions = {
            UserRole.OWNER: ["*"],  # All permissions
            UserRole.ADMIN: [
                "matter:create", "matter:read", "matter:update", "matter:delete",
                "transcript:create", "transcript:read", "transcript:update", "transcript:delete",
                "user:invite", "user:read", "user:update",
                "export:create", "export:read"
            ],
            UserRole.EDITOR: [
                "matter:read", "matter:update",
                "transcript:create", "transcript:read", "transcript:update",
                "export:create", "export:read"
            ],
            UserRole.VIEWER: [
                "matter:read", "transcript:read", "export:read"
            ]
        }
        
        permissions = role_permissions.get(self.role, [])
        return "*" in permissions or permission in permissions
    
    def get_preference(self, key: str, default=None):
        """Get a user preference."""
        return self.preferences.get(key, default)
    
    def set_preference(self, key: str, value):
        """Set a user preference."""
        if self.preferences is None:
            self.preferences = {}
        self.preferences[key] = value
    
    def add_oauth_provider(self, provider: str, provider_data: dict):
        """Add OAuth provider data."""
        if self.oauth_providers is None:
            self.oauth_providers = {}
        self.oauth_providers[provider] = provider_data
    
    def remove_oauth_provider(self, provider: str):
        """Remove OAuth provider data."""
        if self.oauth_providers and provider in self.oauth_providers:
            del self.oauth_providers[provider]