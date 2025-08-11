"""
Celery application configuration for background tasks.
"""

from celery import Celery
from app.core.config import settings

# Create Celery application
celery_app = Celery(
    "caseprep",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.transcription_tasks",
        "app.tasks.export_tasks",
        "app.tasks.maintenance_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.transcription_tasks.*": {"queue": "transcription"},
        "app.tasks.export_tasks.*": {"queue": "exports"},
        "app.tasks.maintenance_tasks.*": {"queue": "maintenance"},
    },
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task time limits
    task_soft_time_limit=60 * 30,  # 30 minutes
    task_time_limit=60 * 60,       # 1 hour
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=60 * 60 * 24,  # 24 hours
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-temp-files": {
            "task": "app.tasks.maintenance_tasks.cleanup_temp_files",
            "schedule": 60.0 * 60.0 * 6,  # Every 6 hours
        },
        "cleanup-old-exports": {
            "task": "app.tasks.maintenance_tasks.cleanup_old_exports",
            "schedule": 60.0 * 60.0 * 24,  # Every 24 hours
        },
        "update-usage-stats": {
            "task": "app.tasks.maintenance_tasks.update_usage_statistics",
            "schedule": 60.0 * 60.0,  # Every hour
        },
    },
)