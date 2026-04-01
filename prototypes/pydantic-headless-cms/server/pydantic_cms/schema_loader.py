"""Load, resolve, and convert JSON Schema files to internal CMS types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .field_types import FieldDefinition, FieldType
from .models import ContentTypeSchema


@dataclass
class ResolvedSchema:
    id: str
    name: str
    base: str | None
    own_fields: list[FieldDefinition]
    inherited_fields: list[FieldDefinition]

    @property
    def all_fields(self) -> list[FieldDefinition]:
        return self.inherited_fields + self.own_fields


# ---------------------------------------------------------------------------
# JSON Schema property → FieldType mapping
# ---------------------------------------------------------------------------

_FORMAT_MAP: dict[str, FieldType] = {
    "date": FieldType.date,
    "date-time": FieldType.datetime_,
}

_JSON_TYPE_MAP: dict[str, FieldType] = {
    "number": FieldType.number,
    "integer": FieldType.integer,
    "boolean": FieldType.boolean,
}


def _prop_to_field(
    name: str,
    prop: dict,
    required_names: list[str],
) -> FieldDefinition:
    """Convert a single JSON Schema property definition to a FieldDefinition."""
    json_type = prop.get("type")
    cms_type = prop.get("x-cms-type")
    fmt = prop.get("format")

    if json_type == "array":
        items = prop.get("items", {})
        item_field = _prop_to_field("_item", items, [])
        field_type = FieldType.list_
        item_type: FieldType | None = item_field.type
    elif json_type == "string":
        item_type = None
        if cms_type == "rich_text":
            field_type = FieldType.rich_text
        elif cms_type == "image":
            field_type = FieldType.image
        elif fmt in _FORMAT_MAP:
            field_type = _FORMAT_MAP[fmt]
        else:
            field_type = FieldType.text
    elif json_type in _JSON_TYPE_MAP:
        field_type = _JSON_TYPE_MAP[json_type]
        item_type = None
    else:
        # Fallback: treat as text
        field_type = FieldType.text
        item_type = None

    return FieldDefinition(
        name=name,
        type=field_type,
        required=name in required_names,
        item_type=item_type,
        label=prop.get("title"),
        description=prop.get("description"),
    )


# ---------------------------------------------------------------------------
# SchemaLoader
# ---------------------------------------------------------------------------


class SchemaLoader:
    def __init__(self, schemas_dir: Path) -> None:
        self._dir = schemas_dir

    def _schema_path(self, schema_id: str) -> Path:
        return self._dir / f"{schema_id}.schema.yml"

    def load_raw(self, schema_id: str) -> dict:
        """Return the raw schema dict from disk."""
        path = self._schema_path(schema_id)
        if not path.exists():
            raise KeyError(f"Schema '{schema_id}' not found")
        return yaml.safe_load(path.read_text())

    def list_ids(self) -> list[str]:
        """Return all schema IDs found in the schemas directory."""
        return [p.stem.removesuffix(".schema") for p in sorted(self._dir.glob("*.schema.yml"))]

    def resolve(self, schema_id: str) -> ResolvedSchema:
        """
        Load a schema file, resolve inheritance via x-cms.base, and return
        a ResolvedSchema with own_fields and inherited_fields separated.
        """
        raw = self.load_raw(schema_id)
        base_id: str | None = (raw.get("x-cms") or {}).get("base")
        required: list[str] = raw.get("required", [])
        own_props: dict = raw.get("properties", {})

        own_fields = [
            _prop_to_field(name, prop, required)
            for name, prop in own_props.items()
        ]

        inherited_fields: list[FieldDefinition] = []
        if base_id:
            parent = self.resolve(base_id)
            inherited_fields = parent.all_fields

        return ResolvedSchema(
            id=schema_id,
            name=raw.get("title", schema_id),
            base=base_id,
            own_fields=own_fields,
            inherited_fields=inherited_fields,
        )

    def to_content_type_schema(self, schema_id: str) -> ContentTypeSchema:
        """Return a flat ContentTypeSchema (inherited + own) for use with build_model()."""
        resolved = self.resolve(schema_id)
        return ContentTypeSchema(
            id=resolved.id,
            name=resolved.name,
            fields=resolved.all_fields,
        )
