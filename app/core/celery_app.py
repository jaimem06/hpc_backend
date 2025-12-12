from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "hpc_cluster",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_send_task_events=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    broker_heartbeat=0,
    worker_concurrency=1, # Asegura un solo hilo
    task_acks_late=True, # Si falla, no pierde la tarea
)