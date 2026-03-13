from __future__ import annotations

import uuid
from typing import Any

from .builder import build_model
from .models import ContentEntry, ContentTypeSchema
from .repository import ContentRepository, ContentTypeRepository


class CMS:
    def __init__(
        self,
        content_type_repo: ContentTypeRepository,
        content_repo: ContentRepository,
    ) -> None:
        self._ct_repo = content_type_repo
        self._c_repo = content_repo

    # ── Content Types ────────────────────────────────────────────────────

    def define_content_type(self, schema: ContentTypeSchema) -> ContentTypeSchema:
        self._ct_repo.save(schema)
        return schema

    def get_content_type(self, id: str) -> ContentTypeSchema:
        schema = self._ct_repo.get(id)
        if schema is None:
            raise KeyError(f"Content type '{id}' not found")
        return schema

    def list_content_types(self) -> list[ContentTypeSchema]:
        return self._ct_repo.list_all()

    def update_content_type(self, schema: ContentTypeSchema) -> ContentTypeSchema:
        if not self._ct_repo.exists(schema.id):
            raise KeyError(f"Content type '{schema.id}' not found")
        self._ct_repo.save(schema)
        return schema

    def delete_content_type(self, id: str) -> None:
        if not self._ct_repo.delete(id):
            raise KeyError(f"Content type '{id}' not found")

    # ── Content Entries ──────────────────────────────────────────────────

    def create_content(self, content_type_id: str, data: dict[str, Any]) -> ContentEntry:
        schema = self.get_content_type(content_type_id)
        model_cls = build_model(schema)
        validated = model_cls(**data)
        entry = ContentEntry(
            id=str(uuid.uuid4()),
            content_type_id=content_type_id,
            data=validated.model_dump(mode="json"),
        )
        self._c_repo.save(entry)
        return entry

    def get_content(self, id: str) -> ContentEntry:
        entry = self._c_repo.get(id)
        if entry is None:
            raise KeyError(f"Content entry '{id}' not found")
        return entry

    def list_content(self, content_type_id: str) -> list[ContentEntry]:
        return self._c_repo.list_all(content_type_id)

    def update_content(self, id: str, data: dict[str, Any]) -> ContentEntry:
        existing = self.get_content(id)
        schema = self.get_content_type(existing.content_type_id)
        model_cls = build_model(schema)
        validated = model_cls(**data)
        updated = ContentEntry(
            id=id,
            content_type_id=existing.content_type_id,
            data=validated.model_dump(mode="json"),
        )
        self._c_repo.save(updated)
        return updated

    def delete_content(self, id: str) -> None:
        if not self._c_repo.delete(id):
            raise KeyError(f"Content entry '{id}' not found")
