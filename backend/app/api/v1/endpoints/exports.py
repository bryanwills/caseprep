"""
Export management endpoints for generating various output formats.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


class ExportFormat(str, Enum):
    """Export format options."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


class ExportStatus(str, Enum):
    """Export processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportType(str, Enum):
    """Type of export."""
    TRANSCRIPT = "transcript"
    MATTER_SUMMARY = "matter_summary"
    USER_REPORT = "user_report"
    USAGE_REPORT = "usage_report"


class ExportRequest(BaseModel):
    export_type: ExportType
    format: ExportFormat
    resource_id: str = Field(..., description="ID of the resource to export (transcript_id, matter_id, etc.)")
    include_segments: bool = True
    include_speakers: bool = True
    include_timestamps: bool = True
    include_metadata: bool = False
    date_format: str = Field("YYYY-MM-DD HH:mm:ss", description="Date format for timestamps")
    custom_template: Optional[str] = Field(None, description="Custom template ID for formatting")


class ExportResponse(BaseModel):
    id: str
    export_type: ExportType
    format: ExportFormat
    status: ExportStatus
    resource_id: str
    filename: str
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


# Mock export tracking (in production, this would be a database table)
exports_db = {}


@router.post("/", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
async def create_export(
    export_request: ExportRequest,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new export job."""
    if not current_user.has_permission("export:create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create exports"
        )
    
    # Validate resource exists based on export type
    if export_request.export_type == ExportType.TRANSCRIPT:
        from app.models.transcript import Transcript
        resource_query = select(Transcript).where(
            and_(
                Transcript.id == export_request.resource_id,
                Transcript.tenant_id == current_user.tenant_id
            )
        )
        resource_result = await db.execute(resource_query)
        resource = resource_result.scalar_one_or_none()
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )
        
        filename = f"{resource.title}_{export_request.format.value}"
        
    elif export_request.export_type == ExportType.MATTER_SUMMARY:
        from app.models.matter import Matter
        resource_query = select(Matter).where(
            and_(
                Matter.id == export_request.resource_id,
                Matter.tenant_id == current_user.tenant_id
            )
        )
        resource_result = await db.execute(resource_query)
        resource = resource_result.scalar_one_or_none()
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matter not found"
            )
        
        filename = f"matter_summary_{resource.title}_{export_request.format.value}"
        
    else:
        # For user and usage reports, use tenant-level validation
        filename = f"{export_request.export_type.value}_{export_request.format.value}"
    
    # Generate export ID
    import uuid
    export_id = str(uuid.uuid4())
    
    # Create export record
    export_record = {
        "id": export_id,
        "export_type": export_request.export_type,
        "format": export_request.format,
        "status": ExportStatus.PENDING,
        "resource_id": export_request.resource_id,
        "filename": filename,
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        "created_at": datetime.utcnow(),
        "options": export_request.dict(exclude={"export_type", "format", "resource_id"})
    }
    
    exports_db[export_id] = export_record
    
    # TODO: Trigger background export task
    # This would typically trigger a Celery task
    
    return ExportResponse(**export_record)


@router.get("/", response_model=List[ExportResponse])
async def list_exports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    export_type: Optional[ExportType] = None,
    status: Optional[ExportStatus] = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List export jobs for the current user's tenant."""
    if not current_user.has_permission("export:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read exports"
        )
    
    # Filter exports by tenant
    tenant_exports = [
        export for export in exports_db.values()
        if export["tenant_id"] == current_user.tenant_id
    ]
    
    # Apply filters
    if export_type:
        tenant_exports = [e for e in tenant_exports if e["export_type"] == export_type]
    if status:
        tenant_exports = [e for e in tenant_exports if e["status"] == status]
    
    # Apply pagination
    paginated_exports = tenant_exports[skip:skip + limit]
    
    return [ExportResponse(**export) for export in paginated_exports]


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific export job by ID."""
    if not current_user.has_permission("export:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read exports"
        )
    
    export_record = exports_db.get(export_id)
    
    if not export_record or export_record["tenant_id"] != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    return ExportResponse(**export_record)


@router.delete("/{export_id}")
async def delete_export(
    export_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an export job."""
    if not current_user.has_permission("export:create"):  # Same permission as create
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete exports"
        )
    
    export_record = exports_db.get(export_id)
    
    if not export_record or export_record["tenant_id"] != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    # Don't allow deletion of processing exports
    if export_record["status"] == ExportStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete export that is currently processing"
        )
    
    # TODO: Delete actual export file if it exists
    
    del exports_db[export_id]
    
    return {"message": "Export deleted successfully"}


@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download an export file."""
    if not current_user.has_permission("export:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to download exports"
        )
    
    export_record = exports_db.get(export_id)
    
    if not export_record or export_record["tenant_id"] != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    if export_record["status"] != ExportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Export is not ready for download"
        )
    
    # TODO: Implement actual file streaming/download
    # This would typically return a FileResponse or generate a signed URL
    
    return {
        "download_url": f"/files/exports/{export_id}/{export_record['filename']}",
        "filename": export_record["filename"],
        "expires_at": export_record.get("expires_at")
    }


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_export_template(
    name: str,
    template_content: str,
    description: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a custom export template."""
    if not current_user.has_permission("export:create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create export templates"
        )
    
    # TODO: Implement template storage and validation
    # This would typically validate the template syntax and store it
    
    template_id = str(uuid.uuid4())
    
    return {
        "id": template_id,
        "name": name,
        "description": description,
        "created_at": datetime.utcnow().isoformat(),
        "message": "Export template created successfully"
    }


@router.get("/formats/supported")
async def get_supported_formats(
    export_type: Optional[ExportType] = None
):
    """Get supported export formats, optionally filtered by export type."""
    
    format_support = {
        ExportType.TRANSCRIPT: [ExportFormat.PDF, ExportFormat.DOCX, ExportFormat.TXT, ExportFormat.JSON],
        ExportType.MATTER_SUMMARY: [ExportFormat.PDF, ExportFormat.DOCX, ExportFormat.JSON],
        ExportType.USER_REPORT: [ExportFormat.PDF, ExportFormat.CSV, ExportFormat.XLSX],
        ExportType.USAGE_REPORT: [ExportFormat.PDF, ExportFormat.CSV, ExportFormat.XLSX, ExportFormat.JSON]
    }
    
    if export_type:
        return {
            "export_type": export_type,
            "supported_formats": [fmt.value for fmt in format_support.get(export_type, [])]
        }
    
    return {
        "all_formats": [fmt.value for fmt in ExportFormat],
        "format_support": {
            export_type.value: [fmt.value for fmt in formats]
            for export_type, formats in format_support.items()
        }
    }