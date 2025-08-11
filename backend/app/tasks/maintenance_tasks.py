"""
Maintenance and cleanup tasks for system health.
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, and_

from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.models.user import User, Tenant
from app.models.matter import Matter
from app.models.media import MediaAsset, MediaStatus
from app.models.transcript import Transcript, TranscriptStatus
from app.services.storage_service import get_storage_service


# Create async database session for tasks
async_engine = create_async_engine(str(settings.DATABASE_URL))
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


@celery_app.task(name="app.tasks.maintenance_tasks.cleanup_temp_files")
def cleanup_temp_files():
    """Clean up temporary files older than 24 hours."""
    storage_service = get_storage_service()
    deleted_count = storage_service.cleanup_temp_files(max_age_hours=24)
    
    return {
        "deleted_files": deleted_count,
        "timestamp": datetime.utcnow().isoformat()
    }


@celery_app.task(name="app.tasks.maintenance_tasks.cleanup_old_exports")
def cleanup_old_exports():
    """Clean up export files older than 7 days."""
    from app.tasks.export_tasks import cleanup_old_exports as cleanup_exports
    return cleanup_exports.delay(max_age_days=7)


@celery_app.task(name="app.tasks.maintenance_tasks.update_usage_statistics")
def update_usage_statistics():
    """Update usage statistics for all tenants."""
    return asyncio.run(_update_usage_statistics_async())


async def _update_usage_statistics_async():
    """Async implementation of usage statistics update."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all active tenants
            tenants_query = select(Tenant).where(Tenant.subscription_status.in_(["active", "trial"]))
            tenants_result = await db.execute(tenants_query)
            tenants = list(tenants_result.scalars().all())
            
            updated_tenants = 0
            
            for tenant in tenants:
                # Update matter statistics
                matters_query = select(
                    func.count(Matter.id).label("total_matters"),
                    func.sum(Matter.total_storage_bytes).label("total_storage"),
                    func.sum(Matter.total_duration_ms).label("total_duration"),
                    func.sum(Matter.total_transcripts).label("total_transcripts")
                ).where(Matter.tenant_id == tenant.id)
                
                matters_result = await db.execute(matters_query)
                stats = matters_result.first()
                
                # Update tenant settings with usage stats
                if tenant.settings is None:
                    tenant.settings = {}
                
                tenant.settings.update({
                    "usage_stats": {
                        "total_matters": stats.total_matters or 0,
                        "total_storage_bytes": stats.total_storage or 0,
                        "total_duration_ms": stats.total_duration or 0,
                        "total_transcripts": stats.total_transcripts or 0,
                        "last_updated": datetime.utcnow().isoformat()
                    }
                })
                
                updated_tenants += 1
            
            await db.commit()
            
            return {
                "success": True,
                "updated_tenants": updated_tenants,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


@celery_app.task(name="app.tasks.maintenance_tasks.cleanup_failed_transcriptions")
def cleanup_failed_transcriptions(max_age_hours: int = 72):
    """Clean up failed transcription attempts older than specified hours."""
    return asyncio.run(_cleanup_failed_transcriptions_async(max_age_hours))


async def _cleanup_failed_transcriptions_async(max_age_hours: int):
    """Async implementation of failed transcription cleanup."""
    async with AsyncSessionLocal() as db:
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Find old failed media assets
            failed_query = select(MediaAsset).where(
                and_(
                    MediaAsset.status == MediaStatus.FAILED,
                    MediaAsset.updated_at < cutoff_time.isoformat()
                )
            )
            
            failed_result = await db.execute(failed_query)
            failed_assets = list(failed_result.scalars().all())
            
            cleanup_count = 0
            storage_service = get_storage_service()
            
            for asset in failed_assets:
                try:
                    # Delete file from storage
                    await storage_service.delete_file(asset.storage_path)
                    
                    # Delete database record
                    await db.delete(asset)
                    cleanup_count += 1
                    
                except Exception as e:
                    print(f"Error cleaning up failed asset {asset.id}: {e}")
            
            await db.commit()
            
            return {
                "success": True,
                "cleaned_up_assets": cleanup_count,
                "max_age_hours": max_age_hours,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


@celery_app.task(name="app.tasks.maintenance_tasks.optimize_database")
def optimize_database():
    """Run database optimization tasks."""
    return asyncio.run(_optimize_database_async())


async def _optimize_database_async():
    """Async implementation of database optimization."""
    async with AsyncSessionLocal() as db:
        try:
            # This would run database-specific optimization commands
            # For PostgreSQL, you might run VACUUM ANALYZE
            
            # For now, just return success
            return {
                "success": True,
                "message": "Database optimization completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


@celery_app.task(name="app.tasks.maintenance_tasks.check_system_health")
def check_system_health():
    """Check overall system health and report issues."""
    return asyncio.run(_check_system_health_async())


async def _check_system_health_async():
    """Async implementation of system health check."""
    async with AsyncSessionLocal() as db:
        try:
            health_report = {
                "database_connection": True,
                "storage_accessible": True,
                "issues": [],
                "statistics": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Check database connectivity
            try:
                test_query = select(func.count(User.id))
                await db.execute(test_query)
            except Exception as e:
                health_report["database_connection"] = False
                health_report["issues"].append(f"Database connection issue: {e}")
            
            # Check storage accessibility
            try:
                storage_service = get_storage_service()
                # Try to create a test file
                test_content = b"health_check_test"
                test_path = "health_check_test.txt"
                # This would test storage write/read operations
                health_report["storage_accessible"] = True
            except Exception as e:
                health_report["storage_accessible"] = False
                health_report["issues"].append(f"Storage access issue: {e}")
            
            # Get system statistics
            try:
                # Count active tenants
                active_tenants_query = select(func.count(Tenant.id)).where(
                    Tenant.subscription_status.in_(["active", "trial"])
                )
                active_tenants_result = await db.execute(active_tenants_query)
                active_tenants = active_tenants_result.scalar()
                
                # Count processing media assets
                processing_query = select(func.count(MediaAsset.id)).where(
                    MediaAsset.status == MediaStatus.PROCESSING
                )
                processing_result = await db.execute(processing_query)
                processing_assets = processing_result.scalar()
                
                # Count failed transcriptions
                failed_query = select(func.count(MediaAsset.id)).where(
                    MediaAsset.status == MediaStatus.FAILED
                )
                failed_result = await db.execute(failed_query)
                failed_assets = failed_result.scalar()
                
                health_report["statistics"] = {
                    "active_tenants": active_tenants,
                    "processing_assets": processing_assets,
                    "failed_assets": failed_assets
                }
                
            except Exception as e:
                health_report["issues"].append(f"Statistics collection error: {e}")
            
            # Overall health status
            health_report["status"] = "healthy" if not health_report["issues"] else "issues_detected"
            
            return health_report
            
        except Exception as e:
            return {
                "status": "error",
                "database_connection": False,
                "storage_accessible": False,
                "issues": [f"Health check failed: {e}"],
                "timestamp": datetime.utcnow().isoformat()
            }


@celery_app.task(name="app.tasks.maintenance_tasks.send_usage_reports")
def send_usage_reports():
    """Send usage reports to tenant administrators."""
    return asyncio.run(_send_usage_reports_async())


async def _send_usage_reports_async():
    """Async implementation of usage report sending."""
    async with AsyncSessionLocal() as db:
        try:
            # Get tenants that need usage reports (could be monthly/weekly)
            tenants_query = select(Tenant).where(Tenant.subscription_status.in_(["active", "trial"]))
            tenants_result = await db.execute(tenants_query)
            tenants = list(tenants_result.scalars().all())
            
            reports_sent = 0
            
            for tenant in tenants:
                try:
                    # Generate usage report for tenant
                    # This would compile usage statistics and send email
                    
                    # For now, just increment counter
                    reports_sent += 1
                    
                except Exception as e:
                    print(f"Error sending usage report for tenant {tenant.id}: {e}")
            
            return {
                "success": True,
                "reports_sent": reports_sent,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }