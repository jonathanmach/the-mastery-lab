"""
Pipeline Tasks
==============

CELERY CONCEPTS DEMONSTRATED:
- chain(): execute tasks sequentially, passing results forward
- group(): execute tasks in parallel
- chord(): group + callback (parallel fetch, then process results together)
- Orchestrating complex workflows from simple building blocks
"""

from celery import chord

from celery import shared_task
from app.tasks.fetch import fetch_top_stories, fetch_story_details
from app.tasks.process import process_stories
from app.tasks.store import store_results


@shared_task
def run_scrape_pipeline(limit: int = 20, min_score: int = 10) -> str:
    """
    Orchestrate a full scrape pipeline and return the chord's AsyncResult ID.

    CELERY CONCEPT -- THE PIPELINE PATTERN:

    1. fetch_top_stories(limit)          -> returns [id1, id2, ..., idN]
    2. For each ID, fetch_story_details  -> runs N tasks IN PARALLEL (group)
    3. process_stories(all_results)      -> filters/sorts the collected stories
    4. store_results(processed)          -> writes to disk

    Steps 2-4 form a "chord": a group of parallel tasks whose collected
    results are passed to a callback chain.

    We call fetch_top_stories() directly (not via .delay()) because we're
    already inside a worker -- no need to queue it, we just need the IDs.
    """
    # Stage 1: Fetch story IDs (runs inline in this worker)
    story_ids = fetch_top_stories(limit)

    # Stage 2: chord = group(fetch each story in parallel) | process | store
    #
    # CELERY CONCEPT: chord(header, callback)
    #   header = group of tasks that run in parallel
    #   callback = task (or chain) that receives a list of all header results
    #
    # The | operator chains tasks: process_stories | store_results means
    # "pass the output of process_stories into store_results".
    callback = process_stories.s(min_score=min_score) | store_results.s()
    header = [fetch_story_details.s(sid) for sid in story_ids]

    result = chord(header)(callback)

    return result.id


@shared_task
def periodic_pipeline() -> str:
    """
    Entry point for Celery Beat.

    CELERY CONCEPT: Beat tasks should be lightweight launchers.
    This task just kicks off the real pipeline and returns immediately.
    The actual work happens in the chord spawned by run_scrape_pipeline.
    """
    return run_scrape_pipeline(limit=20, min_score=10)
