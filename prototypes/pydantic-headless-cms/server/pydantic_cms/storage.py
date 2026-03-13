from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ObjectStorage(ABC):
    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str) -> str:
        """Store bytes under key. Returns the public URL."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the object at key. No-op if it doesn't exist."""

    @abstractmethod
    def url_for(self, key: str) -> str:
        """Return the public URL for an existing key."""


class LocalObjectStorage(ObjectStorage):
    """Stores files in a local directory. Pair with FastAPI StaticFiles to serve them."""

    def __init__(
        self,
        upload_dir: str = ".storage/uploads",
        base_url: str = "http://localhost:8004/media",
    ) -> None:
        self._dir = Path(upload_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._base_url = base_url.rstrip("/")

    def upload(self, key: str, data: bytes, content_type: str) -> str:
        (self._dir / key).write_bytes(data)
        return self.url_for(key)

    def delete(self, key: str) -> None:
        p = self._dir / key
        if p.exists():
            p.unlink()

    def url_for(self, key: str) -> str:
        return f"{self._base_url}/{key}"
