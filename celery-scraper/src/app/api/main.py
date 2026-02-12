"""
FastAPI Application
===================

This is the HTTP entry point. It is entirely separate from the Celery
worker process -- they share config and task definitions, but run as
independent processes communicating through Redis.
"""

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Celery Scraper -- HN Top Stories",
    description="Learning project: Celery task queue with FastAPI and Hacker News API",
    version="0.1.0",
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
