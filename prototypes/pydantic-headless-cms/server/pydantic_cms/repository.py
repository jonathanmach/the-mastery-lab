from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ContentEntry, ContentTypeSchema


class ContentTypeRepository(ABC):
    @abstractmethod
    def save(self, schema: ContentTypeSchema) -> None: ...

    @abstractmethod
    def get(self, id: str) -> ContentTypeSchema | None: ...

    @abstractmethod
    def list_all(self) -> list[ContentTypeSchema]: ...

    @abstractmethod
    def delete(self, id: str) -> bool: ...

    @abstractmethod
    def exists(self, id: str) -> bool: ...


class ContentRepository(ABC):
    @abstractmethod
    def save(self, entry: ContentEntry) -> None: ...

    @abstractmethod
    def get(self, id: str) -> ContentEntry | None: ...

    @abstractmethod
    def list_all(self, content_type_id: str) -> list[ContentEntry]: ...

    @abstractmethod
    def delete(self, id: str) -> bool: ...


class InMemoryContentTypeRepository(ContentTypeRepository):
    def __init__(self) -> None:
        self._store: dict[str, ContentTypeSchema] = {}

    def save(self, schema: ContentTypeSchema) -> None:
        self._store[schema.id] = schema

    def get(self, id: str) -> ContentTypeSchema | None:
        return self._store.get(id)

    def list_all(self) -> list[ContentTypeSchema]:
        return list(self._store.values())

    def delete(self, id: str) -> bool:
        if id not in self._store:
            return False
        del self._store[id]
        return True

    def exists(self, id: str) -> bool:
        return id in self._store


class InMemoryContentRepository(ContentRepository):
    def __init__(self) -> None:
        self._store: dict[str, ContentEntry] = {}

    def save(self, entry: ContentEntry) -> None:
        self._store[entry.id] = entry

    def get(self, id: str) -> ContentEntry | None:
        return self._store.get(id)

    def list_all(self, content_type_id: str) -> list[ContentEntry]:
        return [e for e in self._store.values() if e.content_type_id == content_type_id]

    def delete(self, id: str) -> bool:
        if id not in self._store:
            return False
        del self._store[id]
        return True
