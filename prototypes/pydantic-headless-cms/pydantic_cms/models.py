from __future__ import annotations

import re
from typing import Any

import pydantic

from .field_types import FieldDefinition

_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class ContentTypeSchema(pydantic.BaseModel):
    id: str
    name: str
    fields: list[FieldDefinition]

    @pydantic.field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        if not _SLUG_RE.fullmatch(v):
            raise ValueError(
                "Content type id must be a lowercase slug (e.g. 'blog-post', 'recipe')"
            )
        return v


class ContentEntry(pydantic.BaseModel):
    id: str
    content_type_id: str
    data: dict[str, Any]
