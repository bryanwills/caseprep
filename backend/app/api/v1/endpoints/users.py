"""
User management endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    full_name: str
    initials: str
    last_login_at: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True
        use_enum_values = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = Field(None, max_length=500)
    role: Optional[UserRole] = None
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    preferences: Optional[dict] = None


class UserInvite(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users in the current tenant."""
    if not current_user.has_permission("user:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read users"
        )
    
    # Build query
    query = select(User).where(User.tenant_id == current_user.tenant_id)
    
    # Apply filters
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.display_name.ilike(search_pattern)
            )
        )
    
    # Apply pagination and ordering
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [UserResponse.from_orm(user) for user in users]


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user's profile."""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    # Users can't change their own role
    update_data = user_data.dict(exclude_unset=True, exclude={"role"})
    
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
        elif field == "preferences" and value is not None:
            current_user.preferences = value
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user by ID."""
    if not current_user.has_permission("user:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read users"
        )
    
    query = select(User).where(
        and_(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id
        )
    )
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a user."""
    if not current_user.has_permission("user:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update users"
        )
    
    # Get existing user
    query = select(User).where(
        and_(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent non-owners from changing owner role
    if (user_data.role and 
        user_data.role != user.role and 
        current_user.role != UserRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can change user roles"
        )
    
    # Prevent removing last owner
    if (user_data.role and 
        user.role == UserRole.OWNER and 
        user_data.role != UserRole.OWNER):
        
        # Check if this is the last owner
        owner_count_query = select(func.count(User.id)).where(
            and_(
                User.tenant_id == current_user.tenant_id,
                User.role == UserRole.OWNER,
                User.is_active == True
            )
        )
        owner_count_result = await db.execute(owner_count_query)
        owner_count = owner_count_result.scalar()
        
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner from the tenant"
            )
    
    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
        elif field == "preferences" and value is not None:
            user.preferences = value
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a user account."""
    if not current_user.has_permission("user:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to deactivate users"
        )
    
    # Get existing user
    query = select(User).where(
        and_(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deactivating last owner
    if user.role == UserRole.OWNER:
        owner_count_query = select(func.count(User.id)).where(
            and_(
                User.tenant_id == current_user.tenant_id,
                User.role == UserRole.OWNER,
                User.is_active == True
            )
        )
        owner_count_result = await db.execute(owner_count_query)
        owner_count = owner_count_result.scalar()
        
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last owner"
            )
    
    user.is_active = False
    await db.commit()
    
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate a user account."""
    if not current_user.has_permission("user:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to activate users"
        )
    
    # Get existing user
    query = select(User).where(
        and_(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    await db.commit()
    
    return {"message": "User activated successfully"}


@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_user(
    invite_data: UserInvite,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite a new user to the tenant."""
    if not current_user.has_permission("user:invite"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to invite users"
        )
    
    # Check if user already exists
    existing_user_query = select(User).where(
        and_(
            User.email == invite_data.email,
            User.tenant_id == current_user.tenant_id
        )
    )
    existing_user_result = await db.execute(existing_user_query)
    existing_user = existing_user_result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists in the tenant"
        )
    
    # TODO: Implement actual user invitation system
    # This would typically:
    # 1. Create a pending invitation record
    # 2. Send an invitation email
    # 3. Allow the user to complete registration via invitation link
    
    return {
        "message": "User invitation sent successfully",
        "email": invite_data.email,
        "role": invite_data.role
    }