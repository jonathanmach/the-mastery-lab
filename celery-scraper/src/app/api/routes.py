"""
FastAPI Routes
==============

Thin HTTP layer that bridges the user to Celery tasks.
No business logic lives here -- all work is delegated to tasks.
"""

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from app.celery_app import celery
from app.api.schemas import (
    TaskStatusResponse,
    TriggerScrapeRequest,
    TriggerScrapeResponse,
    StoredResultSummary,
)
from app.storage.json_store import get_latest_results, list_result_files, read_result_file
from app.tasks.pipelines import run_scrape_pipeline

router = APIRouter()


@router.post("/scrape", response_model=TriggerScrapeResponse)
def trigger_scrape(body: TriggerScrapeRequest):
    """
    Trigger a full HN scrape pipeline.

    CELERY CONCEPT: .delay() is shorthand for .apply_async().
    It sends the task message to the broker and returns immediately
    with an AsyncResult containing the task ID.
    """
    result = run_scrape_pipeline.delay(limit=body.limit, min_score=body.min_score)
    return TriggerScrapeResponse(
        task_id=result.id,
        status="ACCEPTED",
        message="Scrape pipeline has been queued. Use /tasks/{task_id} to check status.",
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    """
    Check the status of any Celery task by ID.

    CELERY CONCEPT: AsyncResult lets you inspect a task's state.
    Possible states: PENDING -> STARTED -> SUCCESS / FAILURE / RETRY.
    Note: PENDING can mean "not yet started" OR "unknown task ID" --
    Celery cannot distinguish between the two.
    """
    result = AsyncResult(task_id, app=celery)
    response = TaskStatusResponse(
        task_id=task_id,
        status=result.status,
    )
    if result.ready():
        if result.successful():
            response.result = result.result
        else:
            response.error = str(result.result)
    return response


@router.get("/results", response_model=list[StoredResultSummary])
def list_results():
    """List all stored scrape result files."""
    return list_result_files()


@router.get("/results/latest")
def get_latest():
    """Get the most recent scrape results."""
    data = get_latest_results()
    if data is None:
        raise HTTPException(status_code=404, detail="No results found. Trigger a scrape first.")
    return data


@router.get("/results/{filename}")
def get_result_by_file(filename: str):
    """Get a specific result file by name."""
    data = read_result_file(filename)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Result file '{filename}' not found.")
    return data
