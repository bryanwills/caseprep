"""
Pydantic schemas for authentication endpoints.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime

from app.models.user import UserRole, SubscriptionPlan


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Token payload data."""
    sub: str  # user_id
    tenant_id: str
    email: str
    role: str
    exp: int
    iat: int


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    firm_name: str = Field(..., min_length=1, max_length=255)

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        # Check for at least one digit
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')

        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_chars for char in v):
            raise ValueError('Password must contain at least one special character')

        return v

    @validator('firm_name')
    def validate_firm_name(cls, v):
        """Validate firm name."""
        if not v.strip():
            raise ValueError('Firm name cannot be empty')
        return v.strip()


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    tenant_id: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    preferences: dict = {}
    timezone: str = "UTC"
    language: str = "en"

    class Config:
        from_attributes = True
        use_enum_values = True


class UserUpdate(BaseModel):
    """User update request schema."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    preferences: Optional[dict] = None


class PasswordReset(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_chars for char in v):
            raise ValueError('Password must contain at least one special character')

        return v


class PasswordChange(BaseModel):
    """Password change request schema."""
    current_password: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_chars for char in v):
            raise ValueError('Password must contain at least one special character')

        return v


class EmailVerification(BaseModel):
    """Email verification schema."""
    token: str


class TenantResponse(BaseModel):
    """Tenant response schema."""
    id: str
    name: str
    slug: str
    plan: SubscriptionPlan
    subscription_status: str
    trial_ends_at: Optional[datetime] = None
    max_users: int
    max_storage_gb: int
    max_transcription_hours: int
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    custom_domain: Optional[str] = None
    created_at: datetime
    features: dict = {}
    settings: dict = {}

    class Config:
        from_attributes = True
        use_enum_values = True


class OAuthProvider(BaseModel):
    """OAuth provider configuration."""
    provider: str = Field(..., pattern="^(google|github|facebook)$")
    client_id: str
    redirect_uri: str
    state: Optional[str] = None


class OAuthCallback(BaseModel):
    """OAuth callback data."""
    provider: str
    code: str
    state: Optional[str] = None


class MFASetup(BaseModel):
    """MFA setup response."""
    secret: str
    qr_code_url: str
    backup_codes: list[str]


class MFAVerify(BaseModel):
    """MFA verification request."""
    token: str = Field(..., pattern="^[0-9]{6}$")


class MFABackupCode(BaseModel):
    """MFA backup code usage."""
    backup_code: str = Field(..., min_length=8, max_length=8)


class SessionResponse(BaseModel):
    """Active session information."""
    id: str
    device_info: str
    ip_address: str
    location: Optional[str] = None
    created_at: datetime
    last_seen: datetime
    is_current: bool = False