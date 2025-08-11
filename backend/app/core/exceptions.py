"""
Custom exception classes for the CasePrep application.
"""

from typing import Any, Dict, Optional


class CasePrepException(Exception):
    """
    Base exception class for CasePrep-specific errors.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# Authentication & Authorization Exceptions
class AuthenticationError(CasePrepException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details,
        )


class AuthorizationError(CasePrepException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details,
        )


class InvalidTokenError(CasePrepException):
    """Raised when a token is invalid or expired."""
    
    def __init__(self, message: str = "Invalid or expired token", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_TOKEN",
            status_code=401,
            details=details,
        )


# Resource Exceptions
class ResourceNotFoundError(CasePrepException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} with ID '{resource_id}' not found"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class ResourceAlreadyExistsError(CasePrepException):
    """Raised when trying to create a resource that already exists."""
    
    def __init__(self, resource: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} already exists"
        super().__init__(
            message=message,
            error_code="RESOURCE_ALREADY_EXISTS",
            status_code=409,
            details=details,
        )


class ResourceLimitExceededError(CasePrepException):
    """Raised when a resource limit is exceeded."""
    
    def __init__(self, message: str, limit: int, current: int, details: Optional[Dict[str, Any]] = None):
        full_details = {"limit": limit, "current": current}
        if details:
            full_details.update(details)
            
        super().__init__(
            message=message,
            error_code="RESOURCE_LIMIT_EXCEEDED",
            status_code=429,
            details=full_details,
        )


# Validation Exceptions
class ValidationError(CasePrepException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        full_details = details or {}
        if field:
            full_details["field"] = field
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=full_details,
        )


class InvalidFileFormatError(CasePrepException):
    """Raised when an uploaded file has an invalid format."""
    
    def __init__(self, filename: str, allowed_formats: list, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid file format for '{filename}'. Allowed formats: {', '.join(allowed_formats)}"
        full_details = {
            "filename": filename,
            "allowed_formats": allowed_formats,
        }
        if details:
            full_details.update(details)
            
        super().__init__(
            message=message,
            error_code="INVALID_FILE_FORMAT",
            status_code=400,
            details=full_details,
        )


class FileSizeExceededError(CasePrepException):
    """Raised when an uploaded file exceeds size limits."""
    
    def __init__(self, filename: str, size: int, max_size: int, details: Optional[Dict[str, Any]] = None):
        message = f"File '{filename}' size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
        full_details = {
            "filename": filename,
            "size": size,
            "max_size": max_size,
        }
        if details:
            full_details.update(details)
            
        super().__init__(
            message=message,
            error_code="FILE_SIZE_EXCEEDED",
            status_code=413,
            details=full_details,
        )


# Processing Exceptions
class TranscriptionError(CasePrepException):
    """Raised when transcription processing fails."""
    
    def __init__(self, message: str, transcript_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        full_details = details or {}
        if transcript_id:
            full_details["transcript_id"] = transcript_id
            
        super().__init__(
            message=message,
            error_code="TRANSCRIPTION_ERROR",
            status_code=500,
            details=full_details,
        )


class MediaProcessingError(CasePrepException):
    """Raised when media file processing fails."""
    
    def __init__(self, message: str, media_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        full_details = details or {}
        if media_id:
            full_details["media_id"] = media_id
            
        super().__init__(
            message=message,
            error_code="MEDIA_PROCESSING_ERROR",
            status_code=500,
            details=full_details,
        )


class ExportError(CasePrepException):
    """Raised when export generation fails."""
    
    def __init__(
        self, 
        message: str, 
        format_type: Optional[str] = None, 
        transcript_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        full_details = details or {}
        if format_type:
            full_details["format"] = format_type
        if transcript_id:
            full_details["transcript_id"] = transcript_id
            
        super().__init__(
            message=message,
            error_code="EXPORT_ERROR",
            status_code=500,
            details=full_details,
        )


# Storage Exceptions
class StorageError(CasePrepException):
    """Raised when storage operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        full_details = details or {}
        if operation:
            full_details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            status_code=500,
            details=full_details,
        )


class StorageQuotaExceededError(CasePrepException):
    """Raised when storage quota is exceeded."""
    
    def __init__(self, tenant_id: str, quota: int, current_usage: int, details: Optional[Dict[str, Any]] = None):
        message = f"Storage quota exceeded for tenant {tenant_id}. Used: {current_usage}, Quota: {quota}"
        full_details = {
            "tenant_id": tenant_id,
            "quota": quota,
            "current_usage": current_usage,
        }
        if details:
            full_details.update(details)
            
        super().__init__(
            message=message,
            error_code="STORAGE_QUOTA_EXCEEDED",
            status_code=429,
            details=full_details,
        )


# Business Logic Exceptions
class MatterNotActiveError(CasePrepException):
    """Raised when trying to operate on an inactive matter."""
    
    def __init__(self, matter_id: str, status: str, details: Optional[Dict[str, Any]] = None):
        message = f"Matter {matter_id} is not active (current status: {status})"
        full_details = {
            "matter_id": matter_id,
            "status": status,
        }
        if details:
            full_details.update(details)
            
        super().__init__(
            message=message,
            error_code="MATTER_NOT_ACTIVE",
            status_code=409,
            details=full_details,
        )


class TranscriptInProgressError(CasePrepException):
    """Raised when trying to modify a transcript that is being processed."""
    
    def __init__(self, transcript_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Transcript {transcript_id} is currently being processed and cannot be modified"
        full_details = {"transcript_id": transcript_id}
        if details:
            full_details.update(details)
            
        super().__init__(
            message=message,
            error_code="TRANSCRIPT_IN_PROGRESS",
            status_code=409,
            details=full_details,
        )


class RetentionPolicyViolationError(CasePrepException):
    """Raised when an operation violates data retention policies."""
    
    def __init__(self, message: str, policy_details: Dict[str, Any], details: Optional[Dict[str, Any]] = None):
        full_details = {"policy": policy_details}
        if details:
            full_details.update(details)
            
        super().__init__(
            message=message,
            error_code="RETENTION_POLICY_VIOLATION",
            status_code=403,
            details=full_details,
        )


# External Service Exceptions
class ExternalServiceError(CasePrepException):
    """Raised when external service calls fail."""
    
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        full_message = f"External service '{service}' error: {message}"
        full_details = {"service": service}
        if details:
            full_details.update(details)
            
        super().__init__(
            message=full_message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=full_details,
        )


class RateLimitExceededError(CasePrepException):
    """Raised when API rate limits are exceeded."""
    
    def __init__(
        self, 
        limit: int, 
        window: int, 
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Rate limit exceeded: {limit} requests per {window} seconds"
        full_details = {
            "limit": limit,
            "window": window,
        }
        if retry_after:
            full_details["retry_after"] = retry_after
        if details:
            full_details.update(details)
            
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=full_details,
        )


# Configuration/Setup Exceptions
class ConfigurationError(CasePrepException):
    """Raised when there are configuration issues."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        full_details = details or {}
        if config_key:
            full_details["config_key"] = config_key
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=full_details,
        )


class DatabaseError(CasePrepException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        full_details = details or {}
        if operation:
            full_details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=full_details,
        )