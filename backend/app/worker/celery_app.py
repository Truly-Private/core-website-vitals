"""
Celery application configuration for Core Website Vitals.
Handles background task processing for SEO analysis.
"""

import os
from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings
import structlog

logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Create Celery app instance
celery_app = Celery(
    "core-website-vitals",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.worker.tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Task execution
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
    
    # Task routing
    task_routes={
        "app.worker.tasks.perform_seo_analysis": {"queue": "seo_analysis"},
        "app.worker.tasks.batch_seo_analysis": {"queue": "batch_analysis"},
        "app.worker.tasks.cleanup_expired_tasks": {"queue": "maintenance"},
        "app.worker.tasks.generate_weekly_report": {"queue": "reports"},
    },
    
    # Task time limits
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    
    # Task retries
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Results
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Timezone
    timezone=settings.TIMEZONE,
    enable_utc=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    
    # Performance
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
    
    # Beat scheduler for periodic tasks
    beat_schedule={
        "cleanup-expired-tasks": {
            "task": "app.worker.tasks.cleanup_expired_tasks",
            "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        },
        "generate-weekly-reports": {
            "task": "app.worker.tasks.generate_weekly_report",
            "schedule": crontab(minute=0, hour=9, day_of_week=1),  # Monday at 9 AM
        },
        "cleanup-analysis-cache": {
            "task": "app.worker.tasks.cleanup_analysis_cache",
            "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
        },
    },
)

# Task annotations for monitoring
celery_app.conf.task_annotations = {
    "app.worker.tasks.perform_seo_analysis": {
        "rate_limit": "10/s",
        "time_limit": 300,  # 5 minutes
        "soft_time_limit": 240,  # 4 minutes
        "max_retries": 3,
        "default_retry_delay": 60,
    },
    "app.worker.tasks.batch_seo_analysis": {
        "rate_limit": "5/s",
        "time_limit": 600,  # 10 minutes
        "soft_time_limit": 540,  # 9 minutes
        "max_retries": 2,
        "default_retry_delay": 120,
    },
    "app.worker.tasks.cleanup_expired_tasks": {
        "rate_limit": "1/m",
        "time_limit": 180,  # 3 minutes
        "max_retries": 1,
    },
    "app.worker.tasks.generate_weekly_report": {
        "rate_limit": "1/h",
        "time_limit": 900,  # 15 minutes
        "max_retries": 2,
        "default_retry_delay": 300,
    },
}

# Queue configuration
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_queues = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
    "seo_analysis": {
        "exchange": "seo_analysis",
        "routing_key": "seo_analysis",
    },
    "batch_analysis": {
        "exchange": "batch_analysis",
        "routing_key": "batch_analysis",
    },
    "maintenance": {
        "exchange": "maintenance",
        "routing_key": "maintenance",
    },
    "reports": {
        "exchange": "reports",
        "routing_key": "reports",
    },
}

# Error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    logger.info("Debug task executed", task_id=self.request.id)
    return f"Request: {self.request!r}"

# Task failure handler
@celery_app.task(bind=True, name="handle_task_failure")
def handle_task_failure(self, task_id, error, traceback):
    """Handle task failures and log errors."""
    logger.error("Task failed", 
                task_id=task_id, 
                error=str(error), 
                traceback=traceback)
    
    # Could send notifications or update database here
    return f"Task {task_id} failed: {error}"

# Task success handler
@celery_app.task(bind=True, name="handle_task_success")
def handle_task_success(self, task_id, result):
    """Handle task success."""
    logger.info("Task completed successfully", 
                task_id=task_id, 
                result_type=type(result).__name__)
    
    return f"Task {task_id} completed successfully"

# Worker event handlers
from celery.signals import worker_ready, worker_shutdown, task_prerun, task_postrun, task_failure, task_retry

@worker_ready.connect
def worker_ready_handler(sender, **kwargs):
    """Called when worker is ready."""
    logger.info("Celery worker is ready", worker=sender)

@worker_shutdown.connect
def worker_shutdown_handler(sender, **kwargs):
    """Called when worker is shutting down."""
    logger.info("Celery worker is shutting down", worker=sender)

@task_prerun.connect
def task_prerun_handler(sender, task_id, task, args, kwargs, **kwds):
    """Called before task execution."""
    logger.info("Task starting", 
                task_name=task.name, 
                task_id=task_id)

@task_postrun.connect
def task_postrun_handler(sender, task_id, task, args, kwargs, retval, state, **kwds):
    """Called after task execution."""
    logger.info("Task finished", 
                task_name=task.name, 
                task_id=task_id, 
                state=state)

@task_failure.connect
def task_failure_handler(sender, task_id, exception, args, kwargs, einfo, **kwds):
    """Called when task fails."""
    logger.error("Task failed", 
                task_name=sender.name, 
                task_id=task_id, 
                exception=str(exception),
                einfo=str(einfo))

@task_retry.connect
def task_retry_handler(sender, task_id, reason, args, kwargs, einfo, **kwds):
    """Called when task is retried."""
    logger.warning("Task retrying", 
                   task_name=sender.name, 
                   task_id=task_id, 
                   reason=str(reason))

# Custom task base class
class CustomTask(celery_app.Task):
    """Custom task base class with additional functionality."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error("Custom task failure handler", 
                    task_name=self.name, 
                    task_id=task_id, 
                    exception=str(exc))
        
        # Could implement custom failure handling here
        # like sending notifications or updating database
        
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning("Custom task retry handler", 
                      task_name=self.name, 
                      task_id=task_id, 
                      exception=str(exc))
        
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info("Custom task success handler", 
                   task_name=self.name, 
                   task_id=task_id)

# Set the custom task class
celery_app.Task = CustomTask

# Health check task
@celery_app.task(bind=True, name="health_check")
def health_check(self):
    """Health check task to verify worker is functioning."""
    try:
        import time
        start_time = time.time()
        
        # Simulate some work
        time.sleep(0.1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            "status": "healthy",
            "worker_id": self.request.id,
            "duration": duration,
            "timestamp": start_time
        }
        
        logger.info("Health check passed", **result)
        return result
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise

# Configuration validation
def validate_celery_config():
    """Validate Celery configuration."""
    try:
        # Check broker connection
        inspect = celery_app.control.inspect()
        if not inspect:
            raise Exception("Cannot connect to Celery broker")
        
        # Check if workers are active
        active_workers = inspect.active()
        if not active_workers:
            logger.warning("No active Celery workers found")
        
        logger.info("Celery configuration is valid")
        return True
        
    except Exception as e:
        logger.error("Celery configuration validation failed", error=str(e))
        return False

# Export the app
__all__ = ["celery_app", "validate_celery_config"]