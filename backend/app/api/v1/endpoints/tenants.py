"""
Tenant management endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import User, Tenant, SubscriptionPlan
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: SubscriptionPlan
    subscription_status: str
    trial_ends_at: Optional[str] = None
    max_users: int
    max_storage_gb: int
    max_transcription_hours: int
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    custom_domain: Optional[str] = None
    created_at: str
    is_trial: bool
    is_active: bool
    features: dict = {}
    settings: dict = {}

    class Config:
        from_attributes = True
        use_enum_values = True


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    secondary_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    custom_domain: Optional[str] = Field(None, max_length=255)
    settings: Optional[dict] = None


class TenantSettings(BaseModel):
    data_retention_days: Optional[int] = Field(None, ge=0)
    require_mfa: Optional[bool] = None
    allowed_ip_ranges: Optional[list] = None
    auto_transcription: Optional[bool] = None
    default_language: Optional[str] = Field(None, max_length=10)
    transcription_quality: Optional[str] = Field(None, pattern=r"^(standard|high|premium)$")


@router.get("/me", response_model=TenantResponse)
async def get_current_tenant(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's tenant information."""
    query = select(Tenant).where(Tenant.id == current_user.tenant_id)
    result = await db.execute(query)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return TenantResponse.from_orm(tenant)


@router.put("/me", response_model=TenantResponse)
async def update_current_tenant(
    tenant_data: TenantUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current tenant information."""
    # Only owners can update tenant information
    if current_user.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owners can update tenant information"
        )

    # Get tenant
    query = select(Tenant).where(Tenant.id == current_user.tenant_id)
    result = await db.execute(query)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Update fields
    update_data = tenant_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(tenant, field):
            setattr(tenant, field, value)
        elif field == "settings" and value is not None:
            # Merge settings
            if tenant.settings is None:
                tenant.settings = {}
            tenant.settings.update(value)

    await db.commit()
    await db.refresh(tenant)

    return TenantResponse.from_orm(tenant)


@router.put("/me/settings")
async def update_tenant_settings(
    settings_data: TenantSettings,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update tenant settings."""
    # Only owners and admins can update settings
    if current_user.role.value not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update tenant settings"
        )

    # Get tenant
    query = select(Tenant).where(Tenant.id == current_user.tenant_id)
    result = await db.execute(query)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Update settings
    settings_dict = settings_data.dict(exclude_unset=True)

    if tenant.settings is None:
        tenant.settings = {}

    # Update individual settings and apply to tenant fields where applicable
    for key, value in settings_dict.items():
        tenant.settings[key] = value

        # Apply certain settings directly to tenant fields
        if key == "data_retention_days":
            tenant.data_retention_days = value
        elif key == "require_mfa":
            tenant.require_mfa = value
        elif key == "allowed_ip_ranges":
            tenant.allowed_ip_ranges = value

    await db.commit()

    return {"message": "Tenant settings updated successfully", "settings": tenant.settings}


@router.get("/me/usage")
async def get_tenant_usage(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current tenant's resource usage."""
    # Get tenant
    query = select(Tenant).where(Tenant.id == current_user.tenant_id)
    result = await db.execute(query)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Count current users
    from sqlalchemy import func
    user_count_query = select(func.count(User.id)).where(
        User.tenant_id == current_user.tenant_id,
        User.is_active == True
    )
    user_count_result = await db.execute(user_count_query)
    current_users = user_count_result.scalar()

    # Get storage and transcription usage from matters
    from app.models.matter import Matter
    usage_query = select(
        func.sum(Matter.total_storage_bytes).label("total_storage_bytes"),
        func.sum(Matter.total_duration_ms).label("total_duration_ms"),
        func.count(Matter.id).label("total_matters")
    ).where(Matter.tenant_id == current_user.tenant_id)

    usage_result = await db.execute(usage_query)
    usage = usage_result.first()

    total_storage_gb = (usage.total_storage_bytes or 0) / (1024 * 1024 * 1024)
    total_transcription_hours = (usage.total_duration_ms or 0) / (1000 * 60 * 60)

    return {
        "plan": tenant.plan.value,
        "subscription_status": tenant.subscription_status,
        "usage": {
            "users": {
                "current": current_users,
                "limit": tenant.max_users,
                "percentage": (current_users / tenant.max_users * 100) if tenant.max_users > 0 else 0
            },
            "storage": {
                "current_gb": round(total_storage_gb, 2),
                "limit_gb": tenant.max_storage_gb,
                "percentage": (total_storage_gb / tenant.max_storage_gb * 100) if tenant.max_storage_gb > 0 else 0
            },
            "transcription": {
                "current_hours": round(total_transcription_hours, 2),
                "limit_hours": tenant.max_transcription_hours,
                "percentage": (total_transcription_hours / tenant.max_transcription_hours * 100) if tenant.max_transcription_hours > 0 else 0
            }
        },
        "totals": {
            "matters": usage.total_matters or 0,
            "storage_gb": round(total_storage_gb, 2),
            "transcription_hours": round(total_transcription_hours, 2)
        }
    }


@router.post("/me/features/{feature}/enable")
async def enable_feature(
    feature: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enable a feature for the tenant."""
    # Only owners can manage features
    if current_user.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owners can manage features"
        )

    # Get tenant
    query = select(Tenant).where(Tenant.id == current_user.tenant_id)
    result = await db.execute(query)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    tenant.enable_feature(feature)
    await db.commit()

    return {"message": f"Feature '{feature}' enabled successfully"}


@router.post("/me/features/{feature}/disable")
async def disable_feature(
    feature: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable a feature for the tenant."""
    # Only owners can manage features
    if current_user.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owners can manage features"
        )

    # Get tenant
    query = select(Tenant).where(Tenant.id == current_user.tenant_id)
    result = await db.execute(query)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    tenant.disable_feature(feature)
    await db.commit()

    return {"message": f"Feature '{feature}' disabled successfully"}