"""
Authentication endpoints for login, registration, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ValidationError
from app.schemas.auth import (
    Token, 
    UserCreate, 
    UserLogin, 
    UserResponse,
    PasswordReset,
    PasswordResetConfirm
)
from app.services.auth_service import AuthService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# Initialize auth service
auth_service = AuthService()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    
    Creates a new tenant and user account. The first user becomes the tenant owner.
    """
    try:
        user = await auth_service.register_user(db, user_data)
        return UserResponse.from_orm(user)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.details
        )


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password to get access token.
    """
    try:
        user_login = UserLogin(email=form_data.username, password=form_data.password)
        tokens = await auth_service.authenticate_user(db, user_login)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    try:
        tokens = await auth_service.refresh_access_token(db, refresh_token)
        return tokens
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user = Depends(auth_service.get_current_user)
):
    """
    Get current user information.
    """
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout_user(
    current_user = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user and invalidate tokens.
    """
    await auth_service.logout_user(db, current_user.id)
    return {"message": "Successfully logged out"}


@router.post("/password-reset")
async def request_password_reset(
    password_reset: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email.
    """
    await auth_service.request_password_reset(db, password_reset.email)
    return {"message": "If an account with that email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset with token.
    """
    try:
        await auth_service.reset_password(
            db, 
            password_reset_confirm.token, 
            password_reset_confirm.new_password
        )
        return {"message": "Password has been reset successfully"}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )


@router.post("/verify-email/{token}")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email address with verification token.
    """
    try:
        await auth_service.verify_email(db, token)
        return {"message": "Email verified successfully"}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )


@router.post("/resend-verification")
async def resend_verification_email(
    current_user = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Resend email verification.
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    await auth_service.send_verification_email(db, current_user)
    return {"message": "Verification email sent"}


# OAuth endpoints would be implemented here
@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    """
    Initiate OAuth login with provider (Google, GitHub, Facebook).
    """
    # This would redirect to OAuth provider
    # Implementation depends on chosen OAuth library
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"OAuth with {provider} not yet implemented"
    )


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback from provider.
    """
    # This would handle the OAuth callback and create/login user
    # Implementation depends on chosen OAuth library
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"OAuth callback for {provider} not yet implemented"
    )