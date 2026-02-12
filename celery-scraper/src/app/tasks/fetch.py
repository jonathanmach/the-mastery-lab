"""
Fetch Tasks
===========

CELERY CONCEPTS DEMONSTRATED:
- Simple async task execution (fetch_top_stories)
- Retry with exponential backoff (fetch_story_details)
- bind=True to access self (the task instance) for retries
"""

import httpx

from app.celery_app import celery
from app.config import settings


@celery.task(name="app.tasks.fetch.fetch_top_stories")
def fetch_top_stories(limit: int = 30) -> list[int]:
    """
    Fetch the current top story IDs from Hacker News.

    CELERY CONCEPT: This is the simplest form of a Celery task.
    Decorate a regular function with @celery.task and it becomes
    a task that can be called asynchronously with .delay() or .apply_async().

    Returns:
        List of top story IDs (truncated to `limit`).
    """
    url = f"{settings.hn_api_base_url}/topstories.json"
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()
    story_ids: list[int] = response.json()
    return story_ids[:limit]


@celery.task(
    bind=True,
    name="app.tasks.fetch.fetch_story_details",
    # CELERY CONCEPT: Automatic retries with exponential backoff.
    # max_retries: give up after 3 attempts
    # autoretry_for: which exceptions trigger a retry
    # retry_backoff: first retry after 2s, then 4s, then 8s (exponential)
    # retry_backoff_max: cap the delay at 60 seconds
    # retry_jitter: add randomness so retried tasks don't thundering-herd
    autoretry_for=(httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException),
    max_retries=3,
    retry_backoff=2,
    retry_backoff_max=60,
    retry_jitter=True,
)
def fetch_story_details(self, story_id: int) -> dict:
    """
    Fetch full details for a single HN story.

    CELERY CONCEPT: bind=True makes `self` available -- this is the Task
    instance, giving you access to self.request (metadata), self.retry(),
    and self.update_state(). The autoretry_for / retry_backoff parameters
    handle retries declaratively, but you could also call self.retry()
    manually for more control.

    Returns:
        Dict with story fields: id, title, url, score, by, time, type.
    """
    url = f"{settings.hn_api_base_url}/item/{story_id}.json"
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()
    data: dict = response.json()

    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "url": data.get("url"),
        "score": data.get("score", 0),
        "by": data.get("by"),
        "time": data.get("time"),
        "type": data.get("type"),
        "descendants": data.get("descendants", 0),
    }
