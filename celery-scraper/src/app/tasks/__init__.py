"""
Tasks Package
=============

Importing all task modules here so that Celery's autodiscover_tasks
can find them when it scans "app.tasks".
"""

from app.tasks.fetch import fetch_top_stories, fetch_story_details  # noqa: F401
from app.tasks.process import process_stories  # noqa: F401
from app.tasks.store import store_results  # noqa: F401
from app.tasks.pipelines import periodic_pipeline, run_scrape_pipeline  # noqa: F401
