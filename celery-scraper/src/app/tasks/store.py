"""
Store Task
==========

CELERY CONCEPT DEMONSTRATED:
- Final step in a chain
- Return value becomes the result of the entire chain
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from app.celery_app import celery
from app.config import settings


@celery.task(name="app.tasks.store.store_results")
def store_results(stories: list[dict]) -> dict:
    """
    Persist processed stories to a JSON file.

    CELERY CONCEPT: This is the final link in our chain. Its return value
    becomes the result of the entire chain, which callers can retrieve
    via AsyncResult.

    Returns:
        Summary dict with file path and story count.
    """
    storage_dir = Path(settings.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"hn_top_stories_{timestamp}.json"
    filepath = storage_dir / filename

    payload = {
        "fetched_at": timestamp,
        "count": len(stories),
        "stories": stories,
    }

    filepath.write_text(json.dumps(payload, indent=2))

    return {
        "file": str(filepath),
        "count": len(stories),
        "fetched_at": timestamp,
    }
