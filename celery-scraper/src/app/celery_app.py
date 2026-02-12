"""
Celery Application Factory
===========================

CELERY CONCEPT: The Celery "app" is the entry point for everything.
It holds configuration, knows where to find tasks, and is what workers
and beat schedulers connect to.

Key settings explained:
- broker_url: where messages (task calls) are published (Redis)
- result_backend: where return values are stored (Redis)
- task_serializer / result_serializer: JSON is human-readable for learning
- task_track_started: lets us see STARTED state (off by default)
- task_acks_late: worker acknowledges AFTER execution (safer for retries)
- worker_prefetch_multiplier: 1 means "fetch one task at a time" (fair scheduling)
"""

from celery import Celery

from app.config import settings
from app.beat_schedule import beat_schedule

celery = Celery("celery_scraper")

# -- Broker & Backend --
celery.conf.broker_url = settings.celery_broker_url
celery.conf.result_backend = settings.celery_result_backend

# -- Serialization --
# CELERY CONCEPT: Celery serializes task arguments and return values.
# JSON is the safest default. Pickle is faster but has security risks.
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.accept_content = ["json"]

# -- Task execution settings --
celery.conf.task_track_started = True
celery.conf.task_acks_late = True
celery.conf.worker_prefetch_multiplier = 1

# -- Result expiration --
# CELERY CONCEPT: Results are stored temporarily. After this TTL (seconds),
# Redis will automatically delete them. 1 hour for a learning project.
celery.conf.result_expires = 3600

# -- Beat schedule --
celery.conf.beat_schedule = beat_schedule

# -- Task autodiscovery --
# CELERY CONCEPT: autodiscover_tasks scans the listed packages for any
# module containing @celery.task decorated functions.
celery.autodiscover_tasks(["app.tasks"])
