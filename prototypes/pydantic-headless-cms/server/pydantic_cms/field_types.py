from __future__ import annotations

import datetime
from enum import Enum
from typing import Any

import pydantic


class FieldType(str, Enum):
    text = "text"
    rich_text = "rich_text"
    number = "number"
    integer = "integer"
    boolean = "boolean"
    date = "date"
    datetime_ = "datetime"
    list_ = "list"
    image = "image"
    ref = "ref"


SCALAR_TYPE_MAP: dict[FieldType, type] = {
    FieldType.text: str,
    FieldType.rich_text: str,
    FieldType.number: float,
    FieldType.integer: int,
    FieldType.boolean: bool,
    FieldType.date: datetime.date,
    FieldType.datetime_: datetime.datetime,
    FieldType.image: str,
}


class FieldDefinition(pydantic.BaseModel):
    name: str
    type: FieldType
    required: bool = True
    item_type: FieldType | None = None
    label: str | None = None
    description: str | None = None
    ref_schema: str | None = None
    item_ref_schema: str | None = None       # for list of single ref
    item_ref_schemas: list[str] | None = None  # for list of anyOf refs

    @pydantic.model_validator(mode="after")
    def _validate_list_item_type(self) -> FieldDefinition:
        if self.type == FieldType.list_:
            if self.item_type is None:
                raise ValueError("Fields of type 'list' must specify item_type")
            if self.item_type == FieldType.list_:
                raise ValueError("Nested lists are not supported")
            if self.item_type == FieldType.ref and self.item_ref_schema is None and not self.item_ref_schemas:
                raise ValueError("List of ref fields must specify item_ref_schema or item_ref_schemas")
        elif self.type == FieldType.ref:
            if self.ref_schema is None:
                raise ValueError("Fields of type 'ref' must specify ref_schema")
        else:
            if self.item_type is not None:
                raise ValueError("item_type is only valid for list fields")
        return self

    def to_annotation(self) -> Any:
        if self.type == FieldType.list_:
            if self.item_type == FieldType.ref:
                return list[dict]
            return list[SCALAR_TYPE_MAP[self.item_type]]
        if self.type == FieldType.ref:
            return dict
        return SCALAR_TYPE_MAP[self.type]
