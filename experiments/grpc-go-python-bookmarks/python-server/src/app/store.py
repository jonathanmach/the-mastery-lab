from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(slots=True)
class BookmarkRecord:
    id: str
    url: str
    title: str
    description: str
    tags: list[str]
    created_at_unix: int


class BookmarkStore:
    def __init__(self) -> None:
        self._bookmarks: dict[str, BookmarkRecord] = {}
        self._order: list[str] = []
        self._counter = 0
        self._lock = Lock()

    def create(
        self,
        *,
        url: str,
        title: str,
        description: str,
        tags: list[str],
        created_at_unix: int,
    ) -> BookmarkRecord:
        with self._lock:
            self._counter += 1
            bookmark_id = f"bkm_{self._counter:04d}"
            record = BookmarkRecord(
                id=bookmark_id,
                url=url,
                title=title,
                description=description,
                tags=list(tags),
                created_at_unix=created_at_unix,
            )
            self._bookmarks[bookmark_id] = record
            self._order.append(bookmark_id)
            return record

    def get(self, bookmark_id: str) -> BookmarkRecord | None:
        with self._lock:
            return self._bookmarks.get(bookmark_id)

    def list(self) -> list[BookmarkRecord]:
        with self._lock:
            return [self._bookmarks[bookmark_id] for bookmark_id in self._order]

    def tag(self, bookmark_id: str, tags: list[str]) -> BookmarkRecord | None:
        with self._lock:
            record = self._bookmarks.get(bookmark_id)
            if record is None:
                return None
            record.tags = list(tags)
            return record

    def delete(self, bookmark_id: str) -> bool:
        with self._lock:
            if bookmark_id not in self._bookmarks:
                return False
            del self._bookmarks[bookmark_id]
            self._order.remove(bookmark_id)
            return True
