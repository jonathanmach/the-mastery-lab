"""
Simple JSON file storage helpers.

Used by the FastAPI layer to read stored results.
"""

import json
from pathlib import Path

from app.config import settings


def list_result_files() -> list[dict]:
    """List all stored result files with metadata."""
    storage_dir = Path(settings.storage_dir)
    if not storage_dir.exists():
        return []

    files = sorted(storage_dir.glob("hn_top_stories_*.json"), reverse=True)
    return [
        {
            "filename": f.name,
            "size_bytes": f.stat().st_size,
            "modified": f.stat().st_mtime,
        }
        for f in files
    ]


def read_result_file(filename: str) -> dict | None:
    """Read a specific result file by name."""
    filepath = Path(settings.storage_dir) / filename
    if not filepath.exists() or not filepath.is_file():
        return None
    return json.loads(filepath.read_text())


def get_latest_results() -> dict | None:
    """Read the most recent result file."""
    storage_dir = Path(settings.storage_dir)
    if not storage_dir.exists():
        return None

    files = sorted(storage_dir.glob("hn_top_stories_*.json"), reverse=True)
    if not files:
        return None
    return json.loads(files[0].read_text())
