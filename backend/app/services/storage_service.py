"""
File storage service for handling media uploads and file management.
"""

import os
import shutil
import hashlib
from typing import BinaryIO, Optional, List
from pathlib import Path
from datetime import datetime

from app.core.config import settings


class StorageService:
    """Service for handling file storage operations."""
    
    def __init__(self):
        self.storage_root = Path(settings.STORAGE_ROOT)
        self.storage_root.mkdir(exist_ok=True, parents=True)
        
        # Create subdirectories
        (self.storage_root / "uploads").mkdir(exist_ok=True)
        (self.storage_root / "temp").mkdir(exist_ok=True)
        (self.storage_root / "exports").mkdir(exist_ok=True)
    
    def generate_file_hash(self, file_content: bytes) -> str:
        """Generate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    def get_file_path(self, tenant_id: str, matter_id: str, filename: str) -> Path:
        """Generate storage path for a file."""
        return self.storage_root / "uploads" / tenant_id / matter_id / filename
    
    async def store_file(
        self, 
        file_content: bytes, 
        tenant_id: str, 
        matter_id: str, 
        original_filename: str
    ) -> tuple[str, str]:
        """
        Store file and return storage path and content hash.
        
        Returns:
            tuple: (storage_path, content_hash)
        """
        content_hash = self.generate_file_hash(file_content)
        
        # Create directory structure
        file_path = self.get_file_path(tenant_id, matter_id, original_filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file with same hash already exists
        existing_file = await self.find_file_by_hash(tenant_id, content_hash)
        if existing_file:
            # Create a symlink to avoid duplication
            if not file_path.exists():
                os.link(existing_file, file_path)
            return str(file_path.relative_to(self.storage_root)), content_hash
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(file_path.relative_to(self.storage_root)), content_hash
    
    async def find_file_by_hash(self, tenant_id: str, content_hash: str) -> Optional[Path]:
        """Find existing file with the same content hash."""
        tenant_path = self.storage_root / "uploads" / tenant_id
        if not tenant_path.exists():
            return None
        
        # Search for files with matching hash
        for file_path in tenant_path.rglob("*"):
            if file_path.is_file():
                with open(file_path, "rb") as f:
                    file_hash = self.generate_file_hash(f.read())
                    if file_hash == content_hash:
                        return file_path
        
        return None
    
    async def get_file_content(self, storage_path: str) -> Optional[bytes]:
        """Get file content by storage path."""
        full_path = self.storage_root / storage_path
        
        if not full_path.exists() or not full_path.is_file():
            return None
        
        with open(full_path, "rb") as f:
            return f.read()
    
    async def delete_file(self, storage_path: str) -> bool:
        """Delete a file by storage path."""
        full_path = self.storage_root / storage_path
        
        if not full_path.exists():
            return False
        
        try:
            full_path.unlink()
            
            # Try to remove empty parent directories
            parent = full_path.parent
            while parent != self.storage_root and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
            
            return True
        except OSError:
            return False
    
    async def get_file_info(self, storage_path: str) -> Optional[dict]:
        """Get file information."""
        full_path = self.storage_root / storage_path
        
        if not full_path.exists() or not full_path.is_file():
            return None
        
        stat = full_path.stat()
        
        return {
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "path": str(full_path),
            "relative_path": storage_path
        }
    
    def get_storage_usage(self, tenant_id: str) -> dict:
        """Get storage usage statistics for a tenant."""
        tenant_path = self.storage_root / "uploads" / tenant_id
        
        if not tenant_path.exists():
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "total_size_gb": 0
            }
        
        total_files = 0
        total_size = 0
        
        for file_path in tenant_path.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_size_gb": total_size / (1024 * 1024 * 1024)
        }
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than max_age_hours."""
        temp_path = self.storage_root / "temp"
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        deleted_count = 0
        
        for file_path in temp_path.rglob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except OSError:
                    pass
        
        return deleted_count


class S3StorageService(StorageService):
    """S3-compatible storage service (for production)."""
    
    def __init__(self):
        # This would use boto3 for S3 operations
        # For now, fall back to local storage
        super().__init__()
        
        # In production, initialize S3 client:
        # import boto3
        # self.s3_client = boto3.client(
        #     's3',
        #     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        #     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        #     region_name=settings.AWS_REGION
        # )
        # self.bucket_name = settings.S3_BUCKET_NAME
    
    async def store_file(self, file_content: bytes, tenant_id: str, matter_id: str, original_filename: str) -> tuple[str, str]:
        """Store file in S3."""
        # For now, use local storage
        # In production, this would upload to S3:
        
        # content_hash = self.generate_file_hash(file_content)
        # s3_key = f"uploads/{tenant_id}/{matter_id}/{original_filename}"
        # 
        # self.s3_client.put_object(
        #     Bucket=self.bucket_name,
        #     Key=s3_key,
        #     Body=file_content,
        #     ContentType=content_type
        # )
        # 
        # return s3_key, content_hash
        
        return await super().store_file(file_content, tenant_id, matter_id, original_filename)


def get_storage_service() -> StorageService:
    """Get the appropriate storage service based on configuration."""
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageService()
    else:
        return StorageService()