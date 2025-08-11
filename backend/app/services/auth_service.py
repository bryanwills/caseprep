"""
Authentication service for user management and JWT token handling.
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ValidationError
from app.models.user import User, Tenant, UserRole, SubscriptionPlan
from app.schemas.auth import UserCreate, UserLogin, Token, TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management."""

    def __init__(self):
        settings = get_settings()
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.refresh_token_expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return encoded_jwt

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            tenant_id: str = payload.get("tenant_id")
            email: str = payload.get("email")
            role: str = payload.get("role")

            if user_id is None or tenant_id is None:
                raise AuthenticationError("Invalid token")

            token_data = TokenData(
                sub=user_id,
                tenant_id=tenant_id,
                email=email,
                role=role,
                exp=payload.get("exp"),
                iat=payload.get("iat")
            )
            return token_data
        except JWTError:
            raise AuthenticationError("Could not validate credentials")

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email address."""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def authenticate_user(self, db: AsyncSession, user_login: UserLogin) -> Token:
        """Authenticate user and return tokens."""
        user = await self.get_user_by_email(db, user_login.email)

        if not user:
            raise AuthenticationError("Incorrect email or password")

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        if not self.verify_password(user_login.password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")

        # Create token data
        token_data = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email,
            "role": user.role.value
        }

        # Create tokens
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)

        # Update last login
        user.last_login_at = datetime.utcnow().isoformat()
        user.login_count += 1
        await db.commit()

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )

    async def refresh_access_token(self, db: AsyncSession, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            token_type = payload.get("type")

            if token_type != "refresh":
                raise AuthenticationError("Invalid token type")

            user_id = payload.get("sub")
            user = await self.get_user_by_id(db, user_id)

            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            # Create new token data
            token_data = {
                "sub": str(user.id),
                "tenant_id": str(user.tenant_id),
                "email": user.email,
                "role": user.role.value
            }

            # Create new tokens
            access_token = self.create_access_token(token_data)
            new_refresh_token = self.create_refresh_token(token_data)

            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60
            )

        except JWTError:
            raise AuthenticationError("Could not validate refresh token")

    async def register_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        """Register a new user and tenant."""
        # Check if user already exists
        existing_user = await self.get_user_by_email(db, user_data.email)
        if existing_user:
            raise ValidationError("Email already registered")

        # Create tenant first
        tenant_slug = user_data.firm_name.lower().replace(" ", "-").replace("_", "-")

        # Ensure unique slug
        slug_query = select(Tenant).where(Tenant.slug == tenant_slug)
        existing_tenant = await db.execute(slug_query)
        if existing_tenant.scalar_one_or_none():
            import uuid
            tenant_slug = f"{tenant_slug}-{str(uuid.uuid4())[:8]}"

        tenant = Tenant(
            name=user_data.firm_name,
            slug=tenant_slug,
            plan=SubscriptionPlan.STARTER,
            subscription_status="trial"
        )
        db.add(tenant)
        await db.flush()  # Get tenant ID

        # Create user
        hashed_password = self.get_password_hash(user_data.password)

        user = User(
            tenant_id=tenant.id,
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=UserRole.OWNER,  # First user is always owner
            is_active=True,
            is_verified=False  # Require email verification
        )
        db.add(user)

        await db.commit()
        await db.refresh(user)

        # TODO: Send verification email

        return user

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Get current authenticated user."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            token_data = self.verify_token(token)
            user = await self.get_user_by_id(db, token_data.sub)

            if user is None:
                raise credentials_exception

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Inactive user"
                )

            return user

        except AuthenticationError:
            raise credentials_exception

    async def logout_user(self, db: AsyncSession, user_id: str):
        """Logout user (in production, this would invalidate tokens)."""
        # In a production system, you might want to:
        # 1. Add tokens to a blacklist
        # 2. Store active sessions in Redis
        # 3. Implement token revocation

        # For now, just update last seen time
        user = await self.get_user_by_id(db, user_id)
        if user:
            # Could track last logout time if needed
            await db.commit()

    async def request_password_reset(self, db: AsyncSession, email: str):
        """Request password reset token."""
        user = await self.get_user_by_email(db, email)

        if user:
            # Generate reset token
            import secrets
            reset_token = secrets.token_urlsafe(32)
            reset_expires = datetime.utcnow() + timedelta(hours=1)

            user.password_reset_token = reset_token
            user.password_reset_expires = reset_expires.isoformat()

            await db.commit()

            # TODO: Send password reset email

    async def reset_password(self, db: AsyncSession, token: str, new_password: str):
        """Reset password using reset token."""
        query = select(User).where(User.password_reset_token == token)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValidationError("Invalid or expired reset token")

        # Check token expiration
        if user.password_reset_expires:
            expires = datetime.fromisoformat(user.password_reset_expires)
            if datetime.utcnow() > expires:
                raise ValidationError("Reset token has expired")

        # Update password
        user.hashed_password = self.get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None

        await db.commit()

    async def verify_email(self, db: AsyncSession, token: str):
        """Verify email address using verification token."""
        query = select(User).where(User.verification_token == token)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValidationError("Invalid verification token")

        user.is_verified = True
        user.verification_token = None

        await db.commit()

    async def send_verification_email(self, db: AsyncSession, user: User):
        """Send verification email to user."""
        if user.is_verified:
            return

        # Generate verification token if not exists
        if not user.verification_token:
            import secrets
            user.verification_token = secrets.token_urlsafe(32)
            await db.commit()

        # TODO: Send verification email with token