"""Pydantic models for API request/response validation."""

from pydantic import BaseModel


class TriggerScrapeRequest(BaseModel):
    limit: int = 20
    min_score: int = 10


class TriggerScrapeResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
    result: dict | list | str | None = None
    error: str | None = None


class StoredResultSummary(BaseModel):
    filename: str
    size_bytes: int
    modified: float
