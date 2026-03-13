from __future__ import annotations

from typing import Any

import pydantic

from .models import ContentTypeSchema


def build_model(schema: ContentTypeSchema) -> type[pydantic.BaseModel]:
    field_definitions: dict[str, Any] = {}

    for field in schema.fields:
        annotation = field.to_annotation()
        if field.required:
            field_definitions[field.name] = (annotation, ...)
        else:
            field_definitions[field.name] = (annotation | None, None)

    model_name = _slug_to_class_name(schema.id)
    return pydantic.create_model(model_name, **field_definitions)


def _slug_to_class_name(slug: str) -> str:
    return "".join(word.capitalize() for word in slug.split("-"))
