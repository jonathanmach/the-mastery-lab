"""
Celery Beat Schedule
====================

CELERY CONCEPT: Celery Beat is a scheduler that kicks off tasks at
regular intervals -- like cron, but integrated with Celery.

The schedule is a dict where each key is a human-readable name and
the value describes what task to call and how often.
"""

from app.config import settings

beat_schedule = {
    "scrape-hn-top-stories": {
        "task": "app.tasks.pipelines.periodic_pipeline",
        "schedule": settings.beat_pipeline_interval_seconds,
        "args": (),
    },
}
