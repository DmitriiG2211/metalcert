from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "certificates_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.process_certificate": {"queue": "certificates"},
        "app.workers.tasks.generate_certificate_preview": {"queue": "previews"},
    },
    task_default_queue="default",
    task_queues={
        "default": {},
        "certificates": {},
        "previews": {},
    },
    broker_connection_retry_on_startup=True,
    result_expires=86400,  # 24 hours
)
