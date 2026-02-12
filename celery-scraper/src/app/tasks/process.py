"""
Process Task
============

CELERY CONCEPT DEMONSTRATED:
- Task as a step in a chain -- receives output of previous task as input
- Pure data transformation (no side effects) making it easy to test
"""

from app.celery_app import celery


@celery.task(name="app.tasks.process.process_stories")
def process_stories(stories: list[dict], min_score: int = 10) -> list[dict]:
    """
    Filter and enrich a list of story dicts.

    CELERY CONCEPT: In a chain (task1 | task2 | task3), each task receives
    the return value of the previous task as its first argument. This task
    is designed to sit in the middle of a chain:
        fetch -> [group of fetch_story_details] -> process_stories -> store_results

    Args:
        stories: list of story dicts from fetch_story_details
        min_score: drop stories below this score threshold

    Returns:
        Filtered and sorted list of story dicts.
    """
    filtered = [
        story for story in stories
        if story and story.get("title") and story.get("score", 0) >= min_score
    ]

    filtered.sort(key=lambda s: s.get("score", 0), reverse=True)

    for rank, story in enumerate(filtered, start=1):
        story["rank"] = rank

    return filtered
