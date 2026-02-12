"""
Test Configuration
==================

CELERY CONCEPT: For unit tests, you typically want tasks to execute
synchronously (eagerly) rather than sending them to a real broker.
Setting task_always_eager=True makes .delay() and .apply_async()
run the task inline in the current process.
"""

import pytest

from app.celery_app import celery


@pytest.fixture(autouse=True)
def celery_eager_mode():
    """Run all Celery tasks synchronously during tests."""
    celery.conf.task_always_eager = True
    celery.conf.task_eager_propagates = True
    yield
    celery.conf.task_always_eager = False
    celery.conf.task_eager_propagates = False
