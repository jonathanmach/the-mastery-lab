"""File-system backed ContentTypeRepository using YAML Schema files."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import ContentTypeSchema
from .repository import ContentTypeRepository
from .schema_loader import SchemaLoader


class FileSystemSchemaRepository(ContentTypeRepository):
    """
    Implements ContentTypeRepository backed by .schema.yml files.

    Each content type is stored as `{schemas_dir}/{id}.schema.yml` in valid
    JSON Schema format.  The raw YAML Schema is preserved on disk; the
    SchemaLoader converts it to ContentTypeSchema on read.
    """

    def __init__(self, schemas_dir: Path) -> None:
        schemas_dir.mkdir(parents=True, exist_ok=True)
        self._dir = schemas_dir
        self._loader = SchemaLoader(schemas_dir)

    # ------------------------------------------------------------------
    # ContentTypeRepository interface
    # ------------------------------------------------------------------

    def save(self, schema: ContentTypeSchema) -> None:
        """
        Persist a ContentTypeSchema by converting it back to JSON Schema format.
        Used when the admin creates/updates a schema via the field-builder API.
        """
        raw = _content_type_to_json_schema(schema)
        path = self._dir / f"{schema.id}.schema.yml"
        path.write_text(yaml.dump(raw, sort_keys=False, allow_unicode=True))

    def save_raw(self, schema_id: str, raw: dict) -> None:
        """Write a raw schema dict to disk verbatim (preserves authoring intent)."""
        path = self._dir / f"{schema_id}.schema.yml"
        path.write_text(yaml.dump(raw, sort_keys=False, allow_unicode=True))

    def get(self, id: str) -> ContentTypeSchema | None:
        try:
            return self._loader.to_content_type_schema(id)
        except KeyError:
            return None

    def list_all(self) -> list[ContentTypeSchema]:
        schemas = []
        for schema_id in self._loader.list_ids():
            try:
                schemas.append(self._loader.to_content_type_schema(schema_id))
            except Exception:
                pass  # Skip malformed schemas silently
        return schemas

    def delete(self, id: str) -> bool:
        path = self._dir / f"{id}.schema.yml"
        if not path.exists():
            return False
        path.unlink()
        return True

    def exists(self, id: str) -> bool:
        return (self._dir / f"{id}.schema.yml").exists()


# ---------------------------------------------------------------------------
# ContentTypeSchema → JSON Schema conversion (used by save())
# ---------------------------------------------------------------------------

from .field_types import FieldType  # noqa: E402 (avoid circular at top)

_FIELD_TYPE_TO_JSON: dict[FieldType, dict] = {
    FieldType.text: {"type": "string"},
    FieldType.rich_text: {"type": "string", "x-cms-type": "rich_text"},
    FieldType.image: {"type": "string", "x-cms-type": "image"},
    FieldType.number: {"type": "number"},
    FieldType.integer: {"type": "integer"},
    FieldType.boolean: {"type": "boolean"},
    FieldType.date: {"type": "string", "format": "date"},
    FieldType.datetime_: {"type": "string", "format": "date-time"},
}


def _content_type_to_json_schema(schema: ContentTypeSchema) -> dict:
    """Convert a ContentTypeSchema to a JSON Schema dict."""
    properties: dict = {}
    required: list[str] = []

    for field in schema.fields:
        if field.type == FieldType.list_:
            item_base = _FIELD_TYPE_TO_JSON.get(field.item_type, {"type": "string"})
            prop: dict = {"type": "array", "items": dict(item_base)}
        else:
            prop = dict(_FIELD_TYPE_TO_JSON.get(field.type, {"type": "string"}))

        if field.label:
            prop["title"] = field.label
        if field.description:
            prop["description"] = field.description

        properties[field.name] = prop
        if field.required:
            required.append(field.name)

    result: dict = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema.id,
        "title": schema.name,
        "x-cms": {"base": None},
        "type": "object",
        "properties": properties,
    }
    if required:
        result["required"] = required
    return result
